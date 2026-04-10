# Sharinmod - AI 开发指南

本文档记录了 Sharinmod 项目中 AI 助手需要了解的项目特定信息和开发指南。

## 项目架构

- **后端**: FastAPI (Python) + PostgreSQL
- **前端**: Next.js (TypeScript) + Tailwind CSS
- **基础设施**: Docker Compose (db, redis, backend, frontend, nginx)
- **数据库迁移**: Alembic

## 配置管理

**重要**: 后端配置统一通过 `etc/config.yaml` 文件管理。

### 配置文件路径

- **默认路径**: `etc/config.yaml`
- **自定义路径**: 通过 `CONFIG_PATH` 环境变量指定（相对于项目根目录）
  ```bash
  export CONFIG_PATH=/path/to/custom/config.yaml
  ```

### 配置结构

`config.yaml` 包含两个主要部分：

1. **`app`**: 应用配置（数据库、OAuth、LiteLLM 等）
2. **`claw_types`**: Claw 类型配置（NANOBOT、OPENCLAW 等）
3. **`workspace_*`**: 工作区存储配置（`workspace_storage_class`、`workspace_storage_size`、`workspace_mount_path`）
4. **`prunc_*`**: Prunc RuntimeClass 配置（`prunc_enabled`、`rootfs_storage_class`、`rootfs_storage_size`）

### 敏感配置 Fallback

敏感配置（如密钥、密码）支持环境变量 fallback：
- 优先级: YAML 值 > 环境变量
- 当 YAML 中值为 `null` 或空字符串时，使用对应环境变量

支持 fallback 的配置项：
- `DATABASE_URI` → `DATABASE_URI` 环境变量
- `GITHUB_CLIENT_ID` → `GITHUB_CLIENT_ID` 环境变量
- `GITHUB_CLIENT_SECRET` → `GITHUB_CLIENT_SECRET` 环境变量
- `GITLAB_CLIENT_ID` → `GITLAB_CLIENT_ID` 环境变量
- `GITLAB_CLIENT_SECRET` → `GITLAB_CLIENT_SECRET` 环境变量
- `LITELLM_BASE_URL` → `LITELLM_BASE_URL` 环境变量
- `LITELLM_MASTER_KEY` → `LITELLM_MASTER_KEY` 环境变量
- `SHARINMOD_ADMIN_EMAIL` → `SHARINMOD_ADMIN_EMAIL` 环境变量
- `SHARINMOD_ADMIN_PASSWORD` → `SHARINMOD_ADMIN_PASSWORD` 环境变量

### 配置示例

```yaml
# Application Configuration
app:
  # Environment
  env: "development"

  # Database (敏感配置，支持环境变量 fallback)
  database_uri: "postgresql://postgres:postgres@db:5432/sharinmod"

  # GitHub OAuth
  github_client_id: ""
  github_client_secret: ""
  github_redirect_uri: "http://localhost:28888/api/oauth/github/callback"

  # ... 其他配置
```

## Docker 容器化环境

**重要**: 项目使用 Docker Compose 管理所有服务，数据库运行在容器内。

### 服务说明

- `db`: PostgreSQL 15 数据库容器 (容器名: `db`)
- `redis`: Redis 缓存容器
- `backend`: FastAPI 后端服务
- `frontend`: Next.js 前端服务
- `litellm-callback-consumer`: LiteLLM 回调消费者
- `nginx`: 反向代理

### 数据库连接

- 容器内: `postgresql://postgres:postgres@db:5432/sharinmod`
- 外部访问: `postgresql://postgres:postgres@localhost:5454/sharinmod` (端口 5454)

### 环境变量

项目根目录的 `.env` 文件包含以下关键配置：

- `COMPOSE_PROJECT_NAME`: Docker Compose 项目名称（如 `sharinmod-ws2`），用于区分多个独立的 worktree 运行环境
  - 容器命名格式：`{COMPOSE_PROJECT_NAME}-{服务名}-1`
  - 示例：`sharinmod-ws2-backend-1`, `sharinmod-ws2-db-1`
  - 查找容器时使用：`docker ps | grep sharinmod-ws2`

- `HOST_PORT`: 服务对外暴露的主端口（如 `28888`）
  - Nginx 反向代理将此端口映射到容器的内部端口
  - 访问地址：`http://localhost:{HOST_PORT}`

- `CONFIG_PATH`: 可选，指定自定义配置文件路径

## 数据库迁移

**必须在容器内执行数据库迁移命令**:

```bash
# 方式 1: 通过 docker exec 在 backend 容器中执行
docker exec -it sharinmod-backend-1 alembic upgrade head

# 方式 2: 进入 backend 容器后执行
docker exec -it sharinmod-backend-1 bash
alembic upgrade head

# 方式 3: 如果容器名不同，先查找容器名
docker ps | grep backend
docker exec -it <容器名> alembic upgrade head
```

**不要**在宿主机直接运行 `alembic upgrade head`，因为宿主机无法连接到容器内的数据库。

## Alembic 迁移规范

### 创建新迁移

迁移文件命名格式: `YYYYMMDD_description.py`

```python
"""Add column to table

Revision ID: YYYYMMDD_description
Revises: <上一迁移的 revision>
Create Date: YYYY-MM-DD

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'YYYYMMDD_description'
down_revision: Union[str, None] = '<上一迁移的 revision>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 添加列、表等的操作
    op.add_column('table_name', sa.Column('column_name', sa.Type(), nullable=True))

def downgrade() -> None:
    # 回滚操作
    op.drop_column('table_name', 'column_name')
```

### 查找最新迁移 revision

```bash
# 在宿主机查看最新迁移文件的 down_revision
ls -lt backend/api/alembic/versions/ | head -5

# 在容器内查看（工作目录为 /app）
ls -lt /app/api/alembic/versions/ | head -5
```

## 代码结构

### 后端目录结构

```
backend/api/
├── alembic/              # 数据库迁移
│   └── versions/         # 迁移脚本
├── models/               # SQLModel 数据模型
├── schemas/              # Pydantic 请求/响应模式
├── routers/              # FastAPI 路由
├── services/             # 业务逻辑层
├── consumers/            # 后台消费者 (Redis 队列)
├── dependencies/         # 依赖注入 (auth 等)
└── database.py           # 数据库连接
```

### 前端目录结构

```
frontend/src/
├── components/           # React 组件
│   ├── ui/              # shadcn/ui 基础组件
│   ├── usage/           # 使用情况页面组件
│   └── *.tsx            # 其他页面组件
├── lib/                  # 工具库
│   ├── services.ts      # API 调用封装
│   └── api.ts           # Axios 配置
└── app/                  # Next.js App Router
```

## 开发规范

### 后端规范

1. **查询过滤**: 使用辅助函数避免重复代码
   ```python
   def _apply_filters(query, param1, param2):
       if param1:
           query = query.where(Model.field == param1)
       if param2:
           query = query.where(Model.field2 == param2)
       return query
   ```

2. **时间处理**: 使用 `datetime.now(timezone.utc)` 存储时间
   ```python
   from datetime import datetime, timezone
   now = datetime.now(timezone.utc)
   ```

3. **可选字段**: 使用 `Optional[datetime] = Field(default=None)`

### 前端规范

1. **API 调用**: 通过 `services.ts` 封装
   ```typescript
   export const usageAPI = {
     getLogs: (params?: { page?: number; unified_api_key_id?: number }) =>
       api.get('/api/usage/logs', { params })
   };
   ```

2. **条件参数展开**:
   ```typescript
   const response = await usageAPI.getLogs({
     page,
     ...(selectedApiKey !== 'all' && { unified_api_key_id: parseInt(selectedApiKey) })
   });
   ```

3. **日期格式化**:
   ```typescript
   new Date(dateString).toLocaleString('zh-CN', {
     year: 'numeric',
     month: '2-digit',
     day: '2-digit',
     hour: '2-digit',
     minute: '2-digit',
     second: '2-digit',
     hour12: false
   })
   ```

## 常用命令

### 容器管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看 backend 日志
docker-compose logs -f backend

# 进入 backend 容器
docker exec -it sharinmod-backend-1 bash
```

### 数据库操作

```bash
# 在容器中运行迁移
docker exec -it sharinmod-backend-1 alembic upgrade head

# 在容器中回滚迁移
docker exec -it sharinmod-backend-1 alembic downgrade -1

# 在容器中查看迁移历史
docker exec -it sharinmod-backend-1 alembic history

# 连接到数据库容器
docker exec -it db psql -U postgres -d sharinmod
```

## 当前已知问题

1. **数据库迁移**: 必须在 backend 容器内执行，不能在宿主机直接运行
2. **时间格式**: 前端使用中文格式化 `zh-CN`，保持 UI 一致性

---

## 经验教训与解决方案

### 问题 1: TypeScript 重复声明变量

**现象**: 添加新提供商时，前端编译报错 `Identifier 'PROVIDER_NAMES' has already been declared`

**原因**: 在 `ModelCard.tsx` 中存在两个同名的 `const PROVIDER_NAMES` 声明（第13行和第107行），一个用于 ProviderLogoTooltip 组件，另一个用于主组件，导致重复声明。

**解决方案**:
- 合并重复的声明为一个完整的版本
- 包含所有支持的提供商

**预防措施**:
- 添加新常量前，先搜索项目中是否已存在同名定义
- 使用全局常量而非局部重复定义

```typescript
// 正确做法：单一完整声明
const PROVIDER_NAMES: Record<string, string> = {
  'bigmodel': '智谱',
  'z.ai': 'Z.AI',
  'volcengine': '火山引擎',
  'moonshot': '月之暗面',
  'minimax': 'MiniMax',
  'openrouter': 'OpenRouter',
};
```

### 问题 2: PostgreSQL 枚举类型添加新值

**现象**: 添加 `APIKeyProvider.OPENROUTER` 枚举后，运行时错误 `invalid input value for enum apikeyprovider: "OPENROUTER"`

**原因**: PostgreSQL 的枚举类型 `apikeyprovider` 是数据库层面的约束，添加 Python 枚举值后需要同步更新数据库。

**解决方案**:

1. **创建迁移文件**：
```python
# backend/api/alembic/versions/YYYYMMDD_add_provider.py
def upgrade() -> None:
    # 使用 IF NOT EXISTS 避免重复添加错误
    op.execute("ALTER TYPE apikeyprovider ADD VALUE IF NOT EXISTS 'OPENROUTER'")
```

2. **手动修复（当迁移链断裂时）**：
```bash
# 直接在数据库执行
docker exec sharinmod-ws2-db-1 psql -U postgres -d sharinmod -c "ALTER TYPE apikeyprovider ADD VALUE IF NOT EXISTS 'OPENROUTER';"

# 检查当前枚举值
docker exec sharinmod-ws2-db-1 psql -U postgres -d sharinmod -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'apikeyprovider');"

# 更新 alembic_version 表
docker exec sharinmod-ws2-db-1 psql -U postgres -d sharinmod -c "UPDATE alembic_version SET version_num = 'YYYYMMDD_new';"
```

3. **修复迁移链**：
```bash
# 修复已存在的迁移文件，添加 IF NOT EXISTS
# 宿主机: 编辑 backend/api/alembic/versions/20260208_moonshot_fix.py
# 容器内: 编辑 /app/api/alembic/versions/20260208_moonshot_fix.py
# 将 "ALTER TYPE ... ADD VALUE 'MOONSHOT'" 改为 "ALTER TYPE ... ADD VALUE IF NOT EXISTS 'MOONSHOT'"
```

**预防措施**:
- 每次添加枚举值时，迁移文件必须使用 `IF NOT EXISTS`
- 添加新枚举值后，先检查数据库枚举状态再运行迁移
- 如果迁移失败，检查 `alembic_version` 表状态并手动修复

---

## Design Context

### Users
**目标用户**: 个人开发者、开发团队、企业管理员
**使用场景**: API 密钥创建、配置、管理；多个 AI 提供商统一管理；使用量监控和费用统计

### Brand Personality
**三个词**: 友好 · 有趣 · 易用
**情感目标**: 让技术管理不那么枯燥，通过交互细节和视觉反馈带来愉悦感

### Aesthetic Direction
**视觉基调**: Claymorphism（拟物化）- 友好、圆润、3D 质感

**核心设计元素**:
- 字体: 标题 Fredoka + 正文 Nunito
- 主色: 靛蓝 Indigo-600 (#4F46E5) + 橙色 Orange-500 (#F97316)
- 圆角: 1rem - 1.5rem
- 按钮: 3D 按钮带底部边框，点击下压效果
- 卡片: 柔和阴影 + 内发光
- 主题: 仅浅色模式

**参考**: 友好有趣的拟物化界面，类似 Notion/Figma 的圆润设计风格
**反向参考**: ❌ 过于企业化的扁平设计 ❌ 冰冷的技术仪表盘 ❌ 紫色渐变 AI 模板

### Design Principles
1. **友好优先**: 用圆润代替锐角，用柔和代替硬朗，用反馈代替沉默
2. **有趣的交互**: 每个交互都有愉悦的反馈（按钮点击、卡片悬停、状态变化）
3. **一致的品牌感**: 所有元素都符合 claymorphism 语言
4. **清晰的信息层级**: 重要信息突出，次要信息弱化
5. **简化复杂操作**: 友好的界面包裹复杂功能

### Design Tokens
```css
/* Colors */
--primary: #4F46E5;       /* Indigo-600 */
--secondary: #818CF8;     /* Indigo-400 */
--accent: #F97316;        /* Orange-500 */
--background: #EEF2FF;    /* Indigo-50 */
--text: #1E1B4B;          /* Indigo-950 */

/* Typography */
--font-heading: 'Fredoka', sans-serif;
--font-body: 'Nunito', sans-serif;

/* Radius */
--radius-sm: 0.75rem;   /* 12px */
--radius-md: 1rem;      /* 16px */
--radius-lg: 1.25rem;   /* 20px */
--radius-xl: 1.5rem;    /* 24px */
```

---

## BMad Quick Dev Workflow

本项目使用 `bmad-quick-dev` workflow 进行快速开发。该 workflow 专为小型变更和功能设计，确保代码质量和实现完整性。

### Workflow 步骤

| 步骤 | 名称 | 目的 |
|------|------|------|
| **Step 1** | Mode Detection | 确定执行模式（tech-spec 或 direct），捕获基线 commit |
| **Step 2** | Context Gathering | 收集上下文：文件、模式、依赖关系（仅 direct 模式） |
| **Step 3** | Execute Implementation | 执行所有任务，编写测试，处理错误 |
| **Step 4** | Self-Check | 自我审核：任务完成、测试通过、AC 满足、模式遵循 |
| **Step 5** | Adversarial Code Review | 构建差异，调用对抗性审查，发现潜在问题 |
| **Step 6** | Resolve Findings | 处理审查发现，应用修复，完成技术规范 |

### 执行模式

**Mode A: Tech-Spec**
- 用户提供技术规范文件路径（如 `quick-dev tech-spec-xxx.md`）
- 直接从规范中提取任务、上下文和 AC
- 跳过 Step 2（Context Gathering）

**Mode B: Direct Instructions**
- 用户提供直接任务描述（如 `refactor src/foo.ts...`）
- 在 Step 2 中收集文件、模式和依赖
- 创建心智计划并请求确认

### 状态变量

Workflow 执行期间维护以下状态：

- `{baseline_commit}` - Git HEAD 在 workflow 开始时的 commit hash
- `{execution_mode}` - "tech-spec" 或 "direct"
- `{tech_spec_path}` - 技术规范文件路径（仅 Mode A）
- `{project_context}` - 项目上下文（如果存在）

### 对抗性审查

**Step 5** 会执行对抗性代码审查，发现至少 10 个潜在问题。审查类型包括：

- 未使用的变量和导入
- React 最佳实践问题（如 useEffect 中的函数定义）
- 性能优化机会
- 错误处理缺失
- 边界情况处理
- UI 一致性问题

**处理选项：**
- `[W] Walk through` - 逐个讨论每个发现
- `[F] Fix automatically` - 自动修复标记为 "real" 的问题
- `[S] Skip` - 确认并跳过所有发现

### 提交规范

Workflow 完成后，遵循项目提交规范：

```bash
git add <files>
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

<description>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

**Type 可选值：** feat, fix, refactor, chore, docs, test, perf
**Scope 可选值：** org, api, frontend, backend, db, ui

### Workflow 完成

**检查清单：**
- ✅ 所有任务标记为完成
- ✅ 所有 AC（验收标准）满足
- ✅ 代码模式遵循项目约定
- ✅ 技术规范状态更新为 "Implementation Complete"
- ✅ 对抗性审查发现已处理
- ✅ 代码已提交
