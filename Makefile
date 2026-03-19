.PHONY: up down restart logs push build-push

# 从 .env 文件加载配置
include .env

VERSION ?= latest
export VERSION
IMAGE_BACKEND = sharinmod-backend:$(VERSION)
IMAGE_FRONTEND = sharinmod-frontend:$(VERSION)

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

