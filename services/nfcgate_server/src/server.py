#!/usr/bin/env python3
import argparse
import socket
import socketserver
import ssl
import struct
import datetime
import sys
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
HOST = os.getenv("NFCGATESERVER_SERVICE_HOST", "127.0.0.1")
PORT = int(os.getenv("NFCGATESERVER_PORT", 5566))
# HOST = "localhost"

class PluginHandler:
    def __init__(self, plugins):
        self.plugin_list = []

        for modname in plugins:
            self.plugin_list.append((modname, __import__("plugins.mod_%s" % modname, fromlist=["plugins"])))
            print("Loaded", "mod_%s" % modname)

    def filter(self, client, data):
        for modname, plugin in self.plugin_list:
            if type(data) == list:
                first = data[0]
            else:
                first = data
            first = plugin.handle_data(lambda *x: client.log(*x, tag=modname), first, client.state)
            if type(data) == list:
                data = [first] + data[1:]
            else:
                data = first

        return data


class NFCGateClientHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, srv):
        super().__init__(request, client_address, srv)
        
    def log(self, *args, tag="server"):
        self.server.log(*args, origin=self.client_address, tag=tag)

    def setup(self):
        super().setup()
        
        self.session = None
        self.state = {}
        self.request.settimeout(300)

    def handle(self):
        super().handle()

        while True:
            try:
                msg_len_data = self.rfile.read(5)
            except socket.timeout:
                self.log("server", "Timeout")
                break
            if len(msg_len_data) < 5:
                break

            msg_len, session = struct.unpack("!IB", msg_len_data)
            data = self.rfile.read(msg_len)
            self.log("server", "data:", bytes(data))

            # no data was sent or no session number supplied and none set yet
            if msg_len == 0 or session == 0 and self.session is None:
                break

            # change in session number detected
            if self.session != session:
                # remove from old association
                self.server.remove_client(self, self.session)
                # update and add association
                self.session = session
                self.server.add_client(self, session)

            # allow plugins to filter data before sending it to all clients in the session
            self.server.send_to_clients(self.session, self.server.plugins.filter(self, data), self)

    def finish(self):
        super().finish()

        self.server.remove_client(self, self.session)
        self.log("server", "disconnected")


class NFCGateServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, request_handler, plugins, tls_options=None, bind_and_activate=True):
        self.allow_reuse_address = True
        super().__init__(server_address, request_handler, bind_and_activate)

        self.clients = {}
        self.plugins = PluginHandler(plugins)

        # TLS
        self.tls_options = tls_options

        self.log("NFCGate server listening on", server_address)
        if self.tls_options:
            if "verify" in self.tls_options and self.tls_options["verify"] is not None:
                self.log("Verify mode enabled\n=============\ncacert\t{}\ncert\t{}\nkey\t{}\n=============".format(self.tls_options["cacert_file"], self.tls_options["cert_file"],
                                                                  self.tls_options["key_file"]))
            else:
                self.log("TLS enabled\n=============\ncert\t{}\nkey\t{}\n=============".format(self.tls_options["cert_file"],
                                                                  self.tls_options["key_file"]))
    
    def get_request(self):
        client_socket, from_addr = super().get_request()
        if not self.tls_options:
            return client_socket, from_addr
        # if TLS enabled, wrap the socket
        return self.tls_options["context"].wrap_socket(client_socket, server_side=True), from_addr

    def log(self, *args, origin="0", tag="server"):
        print(datetime.datetime.now(), "["+tag+"]", origin, *args)

    def add_client(self, client, session):
        if session is None:
            return

        if session not in self.clients:
            self.clients[session] = []

        self.clients[session].append(client)
        client.log("joined session", session)

    def remove_client(self, client, session):
        if session is None or session not in self.clients:
            return

        self.clients[session].remove(client)
        client.log("left session", session)

    def send_to_clients(self, session, msgs, origin):
        if session is None or session not in self.clients:
            return

        for client in self.clients[session]:
            # do not send message back to originator
            if client is origin:
                continue

            if type(msgs) != list:
                msgs = [msgs]

            for msg in msgs:
                client.wfile.write(int.to_bytes(len(msg), 4, byteorder='big'))
                client.wfile.write(msg)

        self.log("Publish reached", len(self.clients[session]) - 1, "clients")


def parse_args():
    parser = argparse.ArgumentParser(prog="NFCGate server")
    parser.add_argument("plugins", type=str, nargs="*", help="List of plugin modules to load.")
    parser.add_argument("-s", "--tls", help="Enable TLS. You must specify certificate and key.",
                        default=False, action="store_true")
    parser.add_argument("--tls_cert", help="TLS certificate file in PEM format.", action="store")
    parser.add_argument("--tls_key", help="TLS key file in PEM format.", action="store")
    parser.add_argument("--verify", help="Enable verify client's certificate. Needs --tls", 
                        default=False, action="store_true")
    parser.add_argument("--ca_cert", help="CA certificate file in PEM format. It needs for check client certificates", action="store")

    args = parser.parse_args()
    tls_options = None

    if args.verify:
        # check cacert, cert and key file
        if args.ca_cert is None or args.tls_cert is None or args.tls_key is None:
            print("You must specify ca_cert, tls_cert and tls_key!")
            sys.exit(1)

        tls_options = {
            "verify": args.verify,
            "cert_file": args.tls_cert,
            "key_file": args.tls_key,
            "cacert_file": args.ca_cert
        }
        try:
            tls_options["context"] = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            tls_options["context"].verify_mode=ssl.CERT_REQUIRED
            tls_options["context"].load_cert_chain(tls_options["cert_file"], tls_options["key_file"])
            tls_options["context"].load_verify_locations(tls_options["cacert_file"])

        except ssl.SSLError:
            print("CA certificate or certificate or key could not be loaded. Please check format and file permissions!")
            sys.exit(1)

    elif args.tls:
        # check cert and key file
        if args.tls_cert is None or args.tls_key is None:
            print("You must specify tls_cert and tls_key!")
            sys.exit(1)

        tls_options = {
            "cert_file": args.tls_cert,
            "key_file": args.tls_key
        }
        try:
            tls_options["context"] = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            tls_options["context"].load_cert_chain(tls_options["cert_file"], tls_options["key_file"])
        except ssl.SSLError:
            print("Certificate or key could not be loaded. Please check format and file permissions!")
            sys.exit(1)

    return args.plugins, tls_options


async def main():
    plugins, tls_options = parse_args()
    server = NFCGateServer((HOST, PORT), NFCGateClientHandler, plugins, tls_options)
    await server.serve_forever()

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.set_debug(True)
    loop.set_exception_handler(lambda loop, ctx: print('Caught ' + str(ctx.get('exception', ctx['message']))))
        
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
