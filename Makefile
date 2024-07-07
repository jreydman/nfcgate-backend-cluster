include .env

run-cluster:
	docker-compose --env-file=.env --file docker/docker-compose.yaml -p $(PROJECT_NAME) up -d