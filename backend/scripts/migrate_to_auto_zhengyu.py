#!/usr/bin/env python3
"""
Migration script to create 'auto-zhengyu' models in LiteLLM.

This script queries the database for subscriptions with glm-4.7, minimax-m2.1,
or kimi-k2.5 models and creates corresponding 'auto-zhengyu' models in LiteLLM.

Usage:
    python backend/scripts/migrate_to_auto_zhengyu.py [--dry-run] [--verbose]

Target models to migrate:
    - glm-4.7
    - minimax-m2.1
    - kimi-k2.5
"""
import sys
import os
import argparse
import logging
import json
import asyncio
from datetime import datetime
from typing import List, Tuple, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlmodel import Session, create_engine, select

from api.config import settings
from api.models.subscription import Subscription
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus
from api.models.user import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Target models to migrate
TARGET_MODELS = ["glm-4.7", "minimax-m2.1", "kimi-k2.5"]

# New model name in LiteLLM
AUTO_ZHENGYU_MODEL_NAME = "auto-zhengyu"


def _find_model_name_by_litellm_id(litellm_model_ids_json: str, target_model_id: str) -> str:
    """
    从 litellm_model_ids JSON 中通过 litellm_model_id 反向查找原始 model_name

    Args:
        litellm_model_ids_json: JSON 字符串，格式为 {"glm-4.7": "uuid-...", ...}
        target_model_id: 要查找的 LiteLLM model_id (UUID)

    Returns:
        原始 model_name (如 "glm-4.7")，如果未找到返回 target_model_id
    """
    try:
        litellm_model_ids = json.loads(litellm_model_ids_json)
        for model_name, model_id in litellm_model_ids.items():
            if model_id == target_model_id:
                return model_name
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse litellm_model_ids: {e}")
    return target_model_id


def get_subscriptions_to_migrate(db: Session) -> List[Tuple[Subscription, SharedAPIKey, User, str]]:
    """
    查询需要迁移的订阅记录

    查询逻辑：
    1. 从 Subscription 表获取所有记录
    2. JOIN SharedAPIKey 获取 provider 信息（只包含 ACTIVE 状态）
    3. JOIN User 获取用户信息
    4. 使用 _find_model_name_by_litellm_id 反向查找实际模型名称
    5. 过滤出目标模型（glm-4.7、minimax-m2.1、kimi-k2.5）

    Args:
        db: Database session

    Returns:
        List of tuples: (subscription, shared_api_key, user, actual_model_name)
    """
    # 构建 JOIN 查询：Subscription -> SharedAPIKey -> User
    statement = (
        select(Subscription, SharedAPIKey, User)
        .join(SharedAPIKey, Subscription.shared_api_key_id == SharedAPIKey.id)
        .join(User, Subscription.user_id == User.id)
        .where(SharedAPIKey.status == APIKeyStatus.ACTIVE)
    )

    results = db.exec(statement).all()

    # 过滤目标模型
    filtered_results = []
    seen_credentials = set()  # 用于去重

    for subscription, shared_api_key, user in results:
        # 从 litellm_model_ids JSON 中反向查找原始 model_name
        actual_model_name = _find_model_name_by_litellm_id(
            shared_api_key.litellm_model_ids or "{}",
            subscription.model_id
        )

        # 只处理目标模型
        if actual_model_name not in TARGET_MODELS:
            continue

        # 生成 credential_name 用于去重
        credential_name = f"{shared_api_key.provider.value}/{user.email}"

        # 跳过已处理的 credential
        if credential_name in seen_credentials:
            logger.info(f"Skipping duplicate credential: {credential_name}")
            continue

        seen_credentials.add(credential_name)
        filtered_results.append((subscription, shared_api_key, user, actual_model_name))

    return filtered_results


def _handle_litellm_response(response, operation_name: str) -> bool:
    """
    Handle LiteLLM API response with unified error handling

    Args:
        response: httpx.Response object
        operation_name: Description of the operation for logging

    Returns:
        True if operation succeeded (2xx or 404)

    Raises:
        httpx.HTTPStatusError: If response status code is not 2xx or 404
    """
    print(f"[{operation_name}] Response status: {response.status_code}")
    print(f"[{operation_name}] Response body: {response.text}")

    if 200 <= response.status_code < 300:
        return True
    elif response.status_code == 404:
        print(f"[{operation_name}] Object not found (404), treating as success")
        return True
    else:
        print(f"[{operation_name}] Unexpected status code: {response.status_code}")
        response.raise_for_status()


async def create_auto_zhengyu_model(
    client: httpx.AsyncClient,
    shared_api_key: SharedAPIKey,
    user: User,
    actual_model_name: str,
    dry_run: bool = False
) -> Optional[str]:
    """
    在 LiteLLM 中创建 auto-zhengyu 模型

    Args:
        client: httpx AsyncClient
        shared_api_key: SharedAPIKey instance
        user: User instance
        actual_model_name: 实际模型名称（如 glm-4.7）
        dry_run: 如果为 True，仅打印不执行

    Returns:
        model_id if successful, None if dry-run
    """
    credential_name = f"{shared_api_key.provider.value}/{user.email}"

    model_payload = {
        "model_name": AUTO_ZHENGYU_MODEL_NAME,
        "litellm_params": {
            "custom_llm_provider": "anthropic",
            "litellm_credential_name": credential_name,
            "model": actual_model_name
        },
        "provider": "anthropic",
        "litellm_model_name": actual_model_name,
    }

    operation_name = f"create_{actual_model_name}_{user.email}"

    if dry_run:
        print(f"\n[DRY-RUN] Would create model for {actual_model_name}:")
        print(f"  model_name: {model_payload['model_name']}")
        print(f"  litellm_model_name: {model_payload['litellm_model_name']}")
        print(f"  credential_name: {credential_name}")
        print(f"  litellm_params.model: {model_payload['litellm_params']['model']}")
        return None

    try:
        response = await client.post(
            f"{settings.LITELLM_BASE_URL}/model/new",
            json=model_payload,
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
            timeout=30.0
        )

        _handle_litellm_response(response, operation_name)

        # 尝试从响应中提取 model_id
        try:
            response_data = response.json()
            model_id = response_data.get("id") or response_data.get("model", {}).get("id")
            if model_id:
                print(f"[{operation_name}] Created model with id: {model_id}")
            return model_id
        except json.JSONDecodeError:
            print(f"[{operation_name}] Model created successfully (no id in response)")
            return None

    except httpx.HTTPStatusError as e:
        print(f"[{operation_name}] HTTP error: {e}")
        raise


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Migration script to create 'auto-zhengyu' models in LiteLLM"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode: only print what would be done, no actual API calls"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 60)
    print("Auto-Zhengyu Model Migration Script")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Target models: {', '.join(TARGET_MODELS)}")
    print(f"New model name: {AUTO_ZHENGYU_MODEL_NAME}")
    print(f"Dry-run mode: {'ON' if args.dry_run else 'OFF'}")
    print("=" * 60)

    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URI, echo=False)

    try:
        with Session(engine) as db:
            # 查询需要迁移的订阅
            subscriptions = get_subscriptions_to_migrate(db)

            if not subscriptions:
                print("\nNo subscriptions found to migrate.")
                print("This means either:")
                print("  1. No subscriptions exist for the target models")
                print("  2. All matching subscriptions are already processed")
                return 0

            print(f"\nFound {len(subscriptions)} subscription(s) to migrate:")
            print("-" * 60)

            for i, (subscription, shared_api_key, user, actual_model_name) in enumerate(subscriptions, 1):
                credential_name = f"{shared_api_key.provider.value}/{user.email}"
                print(f"{i}. Model: {actual_model_name}")
                print(f"   Provider: {shared_api_key.provider.value}")
                print(f"   User: {user.email}")
                print(f"   Credential: {credential_name}")
                print()

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
        return 130
    except Exception as e:
        print(f"\nDatabase error: {e}")
        logger.exception("Database error during migration")
        return 1

    # 统计
    success_count = 0
    failure_count = 0
    skip_count = 0

    try:
        async with httpx.AsyncClient() as client:
            for subscription, shared_api_key, user, actual_model_name in subscriptions:
                try:
                    model_id = await create_auto_zhengyu_model(
                        client,
                        shared_api_key,
                        user,
                        actual_model_name,
                        dry_run=args.dry_run
                    )
                    if model_id or args.dry_run:
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:
                    logger.exception(f"Failed to create model for {actual_model_name}: {e}")
                    failure_count += 1

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        failure_count += 1

    # 打印统计
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total subscriptions processed: {len(subscriptions)}")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failure_count}")
    print(f"  Skipped: {skip_count}")

    if args.dry_run:
        print("\n[DRY-RUN MODE] No models were actually created.")
    else:
        print(f"\nNew model name created: {AUTO_ZHENGYU_MODEL_NAME}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    return 1 if failure_count > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
