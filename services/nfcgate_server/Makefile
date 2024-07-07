__source_dir=src

PROTO_IN=$(__source_dir)/protocol/protobuf
PROTO_OUT=$(__source_dir)/plugins

TLS_CERT=
TLS_KEY=

protogen:
	protoc -I=$(PROTO_IN) --python_out=$(PROTO_OUT) $(PROTO_IN)/*.proto

run:
	python $(__source_dir)/server.py log

run-tls:
	python $(__source_dir)/server.py log --tls-cert $(TLS_CERT) --tls-key $(TLS_KEY) --tls