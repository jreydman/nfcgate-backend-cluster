include .env

__source_dir=src
PROTO_IN=$(__source_dir)/protocol/protobuf
PROTO_OUT=$(__source_dir)/plugins

protogen:
	protoc -I=$(PROTO_IN) --python_out=$(PROTO_OUT) $(PROTO_IN)/*.proto

run:
	python $(__source_dir)/server.py log

run-cluster:
	docker-compose --env-file=.env --file docker/docker-compose.yaml -p $(PROJECT_NAME) up -d