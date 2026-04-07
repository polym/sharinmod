.PHONY: up down restart logs push build-push up-claw down-claw logs-claw

# 从 .env 文件加载配置
include .env

VERSION ?= latest
export VERSION
IMAGE_BACKEND = sharinmod-backend:$(VERSION)
IMAGE_FRONTEND = sharinmod-frontend:$(VERSION)

COMPOSE_FILES = -f docker-compose.yml
COMPOSE_CMD = docker compose

all: build

# 默认目标
build:
	$(COMPOSE_CMD) $(COMPOSE_FILES) up -d --build

up:
	$(COMPOSE_CMD) $(COMPOSE_FILES) up -d
	@echo "Waiting for services to be ready..."
	@sleep 3

# 启动包含 claw-status-consumer 的服务
up-claw:
	$(COMPOSE_CMD) $(COMPOSE_FILES) -f docker-compose.claw.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 3

down:
	$(COMPOSE_CMD) $(COMPOSE_FILES) down

# 停止包含 claw-status-consumer 的服务
down-claw:
	$(COMPOSE_CMD) $(COMPOSE_FILES) -f docker-compose.claw.yml down

restart:
	$(COMPOSE_CMD) $(COMPOSE_FILES) restart

logs:
	$(COMPOSE_CMD) $(COMPOSE_FILES) logs -f

# 查看 claw-status-consumer 日志
logs-claw:
	$(COMPOSE_CMD) $(COMPOSE_FILES) -f docker-compose.claw.yml logs -f claw-status-consumer

# 标记并推送镜像到自定义仓库（需在 .env 中配置 IMAGE_REGISTRY）
push:
ifndef IMAGE_REGISTRY
	$(error IMAGE_REGISTRY 未设置，请在 .env 中添加，例如: IMAGE_REGISTRY=hub.upyun.com/huxingyun)
endif
	docker tag $(IMAGE_BACKEND) $(IMAGE_REGISTRY)/$(IMAGE_BACKEND)
	docker push $(IMAGE_REGISTRY)/$(IMAGE_BACKEND)
	docker tag $(IMAGE_FRONTEND) $(IMAGE_REGISTRY)/$(IMAGE_FRONTEND)
	docker push $(IMAGE_REGISTRY)/$(IMAGE_FRONTEND)

# 构建镜像并推送到自定义仓库
build-push: build push

