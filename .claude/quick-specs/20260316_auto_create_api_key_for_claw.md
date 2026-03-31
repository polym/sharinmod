# Quick Tech Spec: 龙虾自动创建 API Key

## 需求概述

将"领养龙虾"功能从"手动绑定已有 API Key"改为"自动创建与龙虾名字同名的 API Key"，并在释放龙虾时同步删除该 API Key。

## 当前实现

### 前端 (`claws.tsx`)
- 用户需要手动从下拉框选择已有的 API Key
- 如果没有可用 Key，需要点击"一键创建"按钮手动创建

### 后端 (`services/claw_service.py`)
- `create_claw_async`: 验证用户提供的 `unified_api_key_id` 是否有效
- `delete_claw_async`: 仅删除 K8s Deployment 和数据库记录，不处理 API Key

### Schema (`schemas/claw.py`)
- `ClawCreate.unified_api_key_id`: 必填字段

## 需要修改的文件

### 0. 数据库迁移：新建 `backend/api/alembic/versions/20260316_add_is_auto_created_to_unified_api_keys.py`

```python
"""Add is_auto_created field to unified_api_keys

Revision ID: 20260316_add_is_auto_created
Revises: 20260316_add_unified_api_key_to_claw
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa

revision = '20260316_add_is_auto_created'
down_revision = '20260316_add_unified_api_key_to_claw'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('unified_api_keys', sa.Column('is_auto_created', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('unified_api_keys', 'is_auto_created')
```

### 1. 后端模型：`backend/api/models/unified_api_key.py`

**添加 `is_auto_created` 字段：**

```python
class UnifiedAPIKey(SQLModel, table=True):
    # ... existing fields ...
    is_auto_created: bool = Field(default=False, description="Auto-created for claw, not counted in user quota")
    # ... rest of fields ...
```

### 2. 后端 Service：`backend/api/services/unified_api_key_service.py`

**修改 `count_active_user_api_keys` 函数：**

```python
def count_active_user_api_keys(session: Session, user_id: int) -> int:
    """
    Count active unified API keys for a user (excluding auto-created keys)

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Count of ACTIVE API keys (excluding auto-created ones)
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.user_id == user_id,
        UnifiedAPIKey.status == UnifiedAPIKeyStatus.ACTIVE,
        UnifiedAPIKey.is_auto_created == False  # 只统计手动创建的
    )
    api_keys = session.exec(statement).all()
    return len(api_keys)
```

**修改 `create_unified_api_key_async` 函数签名和实现：**

```python
async def create_unified_api_key_async(
    session: Session,
    user: User,
    api_key_name: Optional[str] = None,
    description: Optional[str] = None,
    is_auto_created: bool = False  # 新增参数
) -> UnifiedAPIKey:
    """
    Generate a new unified API key for user with LiteLLM integration

    Args:
        session: Database session
        user: Current authenticated user
        api_key_name: Optional user-friendly name
        description: Optional description
        is_auto_created: If True, this key was auto-created for claw and doesn't count toward quota

    Returns:
        Created UnifiedAPIKey object with litellm_key

    Raises:
        HTTPException: If user has reached 5-key limit (only for manual keys), or LiteLLM sync fails
    """
    # 只有手动创建的 Key 才检查配额
    if not is_auto_created:
        active_count = count_active_user_api_keys(session, user.id)
        if active_count >= MAX_API_KEYS_PER_USER:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_API_KEYS_PER_USER} API keys per user. Please revoke an existing API key first."
            )

    # ... rest of the function ...

    # Create unified API key record with is_auto_created flag
    unified_api_key = UnifiedAPIKey(
        user_id=user.id,
        api_key=api_key,
        status=UnifiedAPIKeyStatus.ACTIVE,
        api_key_name=api_key_name,
        description=description,
        litellm_key=litellm_key,
        api_key_hash=api_key_hash,
        is_auto_created=is_auto_created  # 新字段
    )
    # ... rest of the function ...
```

### 3. 前端：`frontend/src/components/claws.tsx`

**移除以下内容：**
- API Key 选择器 UI（第 379-412 行）
- `loadApiKeys` 函数（第 101-114 行）
- `handleCreateApiKey` 函数（第 121-140 行）
- 相关状态：`apiKeys`, `selectedApiKeyId`, `creatingKey`（第 73-75 行）
- `useEffect` 中的 `loadApiKeys()` 调用（第 118 行）

**修改 `handleCreate` 函数：**
```typescript
// 移除 selectedApiKeyId 参数
await clawAPI.createClaw({
  name: newName.trim(),
  type: newType,
  qq_bot_id: newQqBotId.trim(),
  qq_bot_secret: newQqBotSecret.trim(),
  // unified_api_key_id 不再需要传递
});
```

**修改验证逻辑：**
```typescript
// 移除 !selectedApiKeyId 条件
if (!newName.trim() || !newQqBotId.trim() || !newQqBotSecret.trim()) {
  // ...
}
```

### 2. 后端 Schema：`backend/api/schemas/claw.py`

**修改 `ClawCreate` 类：**
```python
class ClawCreate(BaseModel):
    """Request schema for creating a claw"""
    name: str = Field(max_length=100, description="Friendly name for the claw")
    type: ClawType = Field(description="Type of QQ bot (NanoBot, OpenClaw, ZeroBot)")
    qq_bot_id: str = Field(max_length=255, description="QQ Bot ID")
    qq_bot_secret: str = Field(max_length=255, description="QQ Bot Secret")
    # unified_api_key_id 字段移除（不再需要前端传递）
```

### 3. 后端 Service：`backend/api/services/claw_service.py`

**修改 `create_claw_async` 函数：**

```python
async def create_claw_async(session: Session, current_user: User, data: ClawCreate) -> Claw:
    """
    Create a new Claw:
    1. Check quota (max 10 per user)
    2. Auto-create API Key with claw name
    3. Persist a PENDING record to obtain the ID
    4. Build IMAGE, COMMAND and CONFIG_FILES dict from /app/assets/config.yaml
    5. Create K8s ConfigMap (all files mounted at /config) + Deployment
    6. Update record with deployment name and RUNNING status
    If any step fails, rollback everything.
    """
    if count_user_claws(session, current_user.id) >= MAX_CLAWS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"每用户最多 {MAX_CLAWS_PER_USER} 只龙虾"
        )

    # Auto-create API Key with claw name
    from api.services.unified_api_key_service import (
        create_unified_api_key_async,
        block_unified_api_key_async,
        delete_unified_api_key_async
    )

    api_key_obj = None
    try:
        api_key_obj = await create_unified_api_key_async(
            session=session,
            user=current_user,
            api_key_name=data.name,  # 使用龙虾名字作为 API Key 名称
            description=f"Auto-created for claw: {data.name}",
            is_auto_created=True  # 标记为自动创建，不占用配额
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=400,
            detail=f"创建 API Key 失败: {e.detail}"
        )

    # Persist initial record to get an auto-increment ID
    claw = Claw(
        user_id=current_user.id,
        name=data.name,
        type=data.type,
        qq_bot_id=data.qq_bot_id,
        qq_bot_secret=data.qq_bot_secret,
        unified_api_key_id=api_key_obj.id,  # 关联自动创建的 API Key
        status=ClawStatus.PENDING,
    )
    session.add(claw)
    session.commit()
    session.refresh(claw)

    # ... (K8s 创建逻辑保持不变，使用 api_key_obj.litellm_key)

    # 创建 K8s Deployment 失败时，需要回滚 API Key
    try:
        deployment_name = k8s_service.create_deployment(...)
    except Exception as e:
        # 回滚：删除已创建的 API Key
        await block_unified_api_key_async(session, current_user, api_key_obj.id)
        await delete_unified_api_key_async(session, current_user, api_key_obj.id)
        session.delete(claw)
        session.commit()
        raise HTTPException(...)
```

**修改 `delete_claw_async` 函数：**

```python
async def delete_claw_async(session: Session, user_id: int, claw_id: int) -> None:
    """
    Delete a Claw:
    1. Delete the associated API Key
    2. Delete the K8s Deployment (404 is ignored)
    3. Delete the database record
    """
    claw = get_user_claw_by_id(session, user_id, claw_id)

    # Delete associated API Key first
    if claw.unified_api_key_id:
        from api.services.unified_api_key_service import (
            block_unified_api_key_async,
            delete_unified_api_key_async
        )
        from api.models.user import User
        user_stmt = select(User).where(User.id == user_id)
        current_user = session.exec(user_stmt).first()

        try:
            # 先 block（revoke）
            await block_unified_api_key_async(
                session=session,
                user=current_user,
                api_key_id=claw.unified_api_key_id
            )
            # 再删除
            await delete_unified_api_key_async(
                session=session,
                user=current_user,
                api_key_id=claw.unified_api_key_id
            )
        except Exception as e:
            logger.error(f"Error deleting API key for claw {claw.id}: {e}")
            # 继续执行，不阻止龙虾删除

    # Delete K8s Deployment
    if claw.k8s_deployment_name:
        try:
            k8s_service.delete_deployment(claw.k8s_deployment_name)
        except Exception as e:
            logger.error(f"Error deleting K8s deployment {claw.k8s_deployment_name}: {e}")

    session.delete(claw)
    session.commit()
```

## API Key 删除流程说明

根据 `unified_api_key_service.py` 的实现，删除 API Key 需要两步：
1. `block_unified_api_key_async`：将状态改为 REVOKED（会同时调用 LiteLLM block）
2. `delete_unified_api_key_async`：删除数据库记录（需要状态为 REVOKED，会调用 LiteLLM delete）

## 注意事项

1. **事务一致性**：创建龙虾时，如果 K8s Deployment 创建失败，需要回滚已创建的 API Key
2. **用户配额**：自动创建的 API Key（`is_auto_created=True`）**不占用**用户的 5-Key 配额，只有手动创建的 Key 才受限
3. **LiteLLM 同步**：删除 API Key 时会同步调用 LiteLLM 删除接口，失败时记录日志但不阻止龙虾删除

## 数据库字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_auto_created` | Boolean | `true` 表示自动创建（龙虾专用），不计入配额；`false` 表示用户手动创建 |

## 测试计划

1. 领养龙虾时，验证自动创建了同名 API Key
2. 领养龙虾时 K8s 部署失败，验证 API Key 被正确回滚
3. 释放龙虾时，验证关联的 API Key 被正确删除
4. 检查 API Key 列表页面，确认龙虾的 API Key 显示正确
5. **配额测试**：用户已有 5 个手动 Key 时，仍可领养龙虾（自动创建的 Key 不占用配额）
6. **配额测试**：用户有 5 个手动 Key + 3 个龙虾时，手动创建第 6 个 Key 应该被拒绝
