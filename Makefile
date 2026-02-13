.PHONY: up down restart logs

# 从 .env 文件加载配置
include .env

all: build forward

# 默认目标
build:
	docker-compose up -d --build

_up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 3

up: _up forward

forward:
	@echo "Cleaning up existing port forwarding on port $(HOST_PORT)..."
	-@pkill -f "socat TCP-LISTEN:$(HOST_PORT)"
	@sleep 20
	@echo "Setting up port forward: $(HOST_PORT):80 -> $(COMPOSE_PROJECT_NAME)-nginx-1"
	@nohup port_forward -c $(COMPOSE_PROJECT_NAME)-nginx-1 -p $(HOST_PORT):80
	@echo "Port forwarding started. Check logs with: tail -f /tmp/port_forward.log"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

