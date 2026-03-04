.PHONY: up down restart logs

# 从 .env 文件加载配置
include .env

all: build

# 默认目标
build:
	docker-compose up -d --build

up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 3

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

