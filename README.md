# NFCGate Server

This is the NFCGate server application using Python 3 and the Google [Protobuf](https://github.com/google/protobuf/) library, version 3.

![Route schema](docs/assets/route-schema.jpg)

To run, simply start the server using `python server.py`. You can then connect to the server using the IP address of your device and the default port of 5566.  
The server features a plugin system for data filtering. When starting the server, you can specify a list of plugins to be loaded as parameters, e.g. `python server.py log`. For an example, see the shipped `mod_log.py` plugin.

## Meta steps:

```sh
# generate project venv workspace
python3 -m venv .venv

# activate project venv workspace
source .venv/bin/activate && which python

# deactivate project venv workspace
deactivate && which python

# dependencies
python -m pip install protobuf

# generate proto files
make protogen

# NOTE! make shure NFCGATESERVER_SERVICE_HOST (.env) is correct

# start server locally
make run

# start network cluster
make run-cluster
```
