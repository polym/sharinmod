# Sharinmod - API Token 共享平台

一个现代化的 API Token 共享和消费平台，支持共享经济模型和智能代理（Claw）管理。

## 目录

- [快速开始](#-快速开始)
- [项目架构](#-项目架构)
- [配置管理](#-配置管理)
- [开发指南](#-开发指南)
- [项目结构](#-项目结构)
- [数据库管理](#-数据库管理)
- [测试](#-测试)
- [部署](#-部署)

## 🚀 快速开始

### 前置要求

- Docker
- Docker Compose
- Git

### 安装和运行

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd sharinmod
   ```

2. **配置环境变量**

   创建 `.env` 文件：
   ```bash
   cp .env.example .env
   ```

   编辑 `.env` 文件配置：
   ```bash
   # Docker Compose 项目名称（用于区分多个运行环境）
   COMPOSE_PROJECT_NAME=sharinmod

   # 服务对外暴露的主端口
   HOST_PORT=18888

   # 配置文件路径（可选，默认使用 etc/config.yaml）
   # CONFIG_PATH=/path/to/config.yaml
   ```

3. **配置应用**

   编辑 `etc/config.yaml` 文件，配置数据库、OAuth、LiteLLM 等设置：
   ```yaml
   app:
     env: "development"
     database_uri: "postgresql://postgres:postgres@db:5432/sharinmod"
     github_client_id: "your-github-client-id"
     github_client_secret: "your-github-client-secret"
     litellm_base_url: "http://your-litellm-server:4000"
     litellm_master_key: "your-master-key"
   ```

4. **启动所有服务**
   ```bash
   docker-compose up -d
   ```

5. **访问应用**
   - 应用主页: http://localhost:18888
   - API 文档: http://localhost:18888/docs
   - Nginx 反向代理自动路由到前端/后端

### 停止服务

```bash
docker-compose down
```

## 🏗️ 项目架构

- **后端**: FastAPI (Python 3.11) + PostgreSQL 15
- **前端**: Next.js (TypeScript) + Tailwind CSS + shadcn/ui
- **基础设施**: Docker Compose
  - `db`: PostgreSQL 数据库
  - `redis`: Redis 缓存
  - `backend`: FastAPI 后端服务
  - `frontend`: Next.js 前端服务
  - `litellm-callback-consumer`: LiteLLM 回调消费者
  - `nginx`: 反向代理
- **认证**: GitHub/GitLab OAuth + JWT
- **数据库迁移**: Alembic

## ⚙️ 配置管理

**重要**: 所有应用配置统一通过 `etc/config.yaml` 文件管理。

### 配置文件路径

- **默认路径**: `etc/config.yaml`
- **容器内路径**: `/app/config.yaml`
- **自定义路径**: 通过 `CONFIG_PATH` 环境变量指定

### 配置结构

```yaml
# 应用配置
app:
  env: "development"           # 环境: development | staging | production
  database_uri: "..."          # PostgreSQL 连接串
  github_client_id: "..."      # GitHub OAuth
  github_client_secret: "..."
  litellm_base_url: "..."      # LiteLLM 服务地址
  litellm_master_key: "..."    # LiteLLM 主密钥

# Claw 类型配置
claw_types:
  NANOBOT:
    image: "..."
    model_id: "..."
    config_template: {...}
```

### 环境变量 Fallback

敏感配置支持环境变量 fallback（当 YAML 值为空时使用环境变量）：
- `DATABASE_URI`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITLAB_CLIENT_ID`
- `GITLAB_CLIENT_SECRET`
- `LITELLM_BASE_URL`
- `LITELLM_MASTER_KEY`
- `SHARINMOD_ADMIN_EMAIL`
- `SHARINMOD_ADMIN_PASSWORD`

## 💻 开发指南

### 本地开发

1. **安装后端依赖**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **安装前端依赖**
   ```bash
   cd frontend
   npm install
   ```

3. **配置环境**
   ```bash
   # 设置配置文件路径
   export CONFIG_PATH=$(pwd)/etc/config.yaml

   # 或从 backend 目录运行
   export CONFIG_PATH=../etc/config.yaml
   ```

4. **运行后端**
   ```bash
   cd backend
   python -m uvicorn api.main:app --reload --port 8000
   ```

5. **运行前端**
   ```bash
   cd frontend
   npm run dev
   ```

### 代码规范

- **后端**:
  - 使用 `datetime.now(timezone.utc)` 处理时间
  - 查询过滤使用辅助函数避免重复代码
  - 使用 Alembic 进行数据库迁移

- **前端**:
  - API 调用通过 `lib/services.ts` 封装
  - 日期格式化使用 `zh-CN` locale
  - 使用 shadcn/ui 组件库

## 📁 项目结构

```
sharinmod/
├── backend/                    # FastAPI 后端
│   ├── api/                   # API 应用
│   │   ├── alembic/           # 数据库迁移
│   │   │   └── versions/      # 迁移脚本
│   │   ├── models/            # SQLModel 数据模型
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── routers/           # FastAPI 路由
│   │   ├── services/          # 业务逻辑
│   │   ├── consumers/         # 后台消费者
│   │   ├── dependencies/      # 依赖注入
│   │   ├── config.py          # 配置加载
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试文件
│   ├── .env                   # 环境变量
│   └── Dockerfile
├── frontend/                   # Next.js 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── lib/               # 工具库
│   │   └── app/               # Next.js App Router
│   ├── public/                # 静态资源
│   └── Dockerfile
├── etc/                        # 配置文件目录
│   ├── config.yaml            # 应用配置（敏感，不提交）
│   ├── config.yaml.example    # 配置示例
│   ├── nginx.conf             # Nginx 配置
│   └── kubeconfig             # Kubernetes 配置（敏感）
├── docker-compose.yml          # Docker Compose 配置
├── .env                        # 环境变量
├── .gitignore
├── CLAUDE.md                   # AI 开发指南
└── README.md
```

## 🗄️ 数据库管理

### 运行迁移

**重要**: 数据库迁移必须在容器内执行：

```bash
# 方式 1: 通过 docker exec
docker exec -it sharinmod-backend-1 alembic upgrade head

# 方式 2: 进入容器后执行
docker exec -it sharinmod-backend-1 bash
alembic upgrade head

# 回滚迁移
docker exec -it sharinmod-backend-1 alembic downgrade -1
```

### 创建新迁移

```bash
# 进入 backend 容器
docker exec -it sharinmod-backend-1 bash

# 创建迁移文件
alembic revision --autogenerate -m "description"

# 编辑迁移文件后运行
alembic upgrade head
```

### 连接数据库

```bash
# 进入 PostgreSQL 容器
docker exec -it sharinmod-db-1 psql -U postgres -d sharinmod
```

## 🧪 测试

### 运行测试

```bash
# 从 backend 目录运行
cd backend
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_config_yaml.py -v

# 查看覆盖率
python -m pytest tests/ --cov=api --cov-report=html
```

### 测试覆盖

- 配置加载测试
- API 端点测试
- 数据库模型测试
- 业务逻辑测试

## 🚀 部署

### Docker Compose 部署

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `COMPOSE_PROJECT_NAME` | Docker Compose 项目名称 | `sharinmod` |
| `HOST_PORT` | 服务对外端口 | `18888` |
| `CONFIG_PATH` | 配置文件路径 | `etc/config.yaml` |

## 🔒 安全

- 敏感配置文件通过 `.gitignore` 保护（`etc/config.yaml`, `etc/kubeconfig`）
- JWT Token 认证
- OAuth 登录（GitHub/GitLab）
- 数据库密码环境变量隔离
- Nginx 反向代理

## 📚 相关文档

- [CLAUDE.md](./CLAUDE.md) - AI 助手开发指南
- [技术规范](./_bmad-output/implementation-artifacts/) - 技术实现文档

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### 2026-03-18
- 配置文件统一迁移至 `etc/` 目录
- 添加 `CONFIG_PATH` 环境变量支持
- 更新 Docker Compose 配置

### 2026-02-05
- 移除浏览器深色主题支持

## 📄 许可证

本项目采用 MIT 许可证。
