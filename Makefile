.PHONY: up down restart logs

# 从 .env 文件加载配置
include .env

# 默认目标
up:
	docker-compose up -d --build
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Setting up port forward: $(HOST_PORT):80 -> $(COMPOSE_PROJECT_NAME)-nginx-1"
	port_forward -c $(COMPOSE_PROJECT_NAME)-nginx-1 -p $(HOST_PORT):80

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f
