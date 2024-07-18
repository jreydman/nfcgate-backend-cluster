FROM python:latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-u", "server.py", "log", "--tls_cert", "certs/server.pem", "--tls_key", "certs/server.key", "--ca_cert", "certs/cacert.pem"]
