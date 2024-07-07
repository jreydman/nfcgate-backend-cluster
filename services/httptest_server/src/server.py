import http.server
import socketserver
import os
# from dotenv import load_dotenv

# load_dotenv()

# PORT = int(os.getenv("TESTHTTP_PORT", 3000))
PORT=3000
DIRECTORY = os.path.join(os.path.dirname(__file__), "web")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"serving at port {PORT}")
    httpd.serve_forever()