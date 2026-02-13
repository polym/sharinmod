"""Add provider_configs and provider_models tables

Revision ID: 20260213_add_provider_configs
Revises: 20260212_add_is_admin_field
Create Date: 2026-02-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '20260213_add_provider_configs'
down_revision: Union[str, None] = '20260212_add_is_admin_field'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Provider configuration data from PROVIDER_INFO in shared_api_key_service.py
PROVIDER_DATA = [
    {
        'provider_key': 'bigmodel',
        'name': '智谱 AI Coding Plan',
        'website': 'https://bigmodel.cn',
        'logo_path': '/providers/bigmodel-logo.png',
        'is_enabled': True,
        'models': [
            {'model_key': 'glm-5', 'display_name': 'GLM-5', 'description': '智谱 AI 最新一代旗舰模型，超长上下文支持',
             'context_length': '200k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': None},
            {'model_key': 'glm-4.7', 'display_name': 'GLM-4.7', 'description': '智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1441},
            {'model_key': 'glm-4.6', 'display_name': 'GLM-4.6', 'description': '智谱 AI 高性能模型，平衡速度与质量',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1356},
            {'model_key': 'glm-4.5-air', 'display_name': 'GLM-4.5 Air', 'description': '智谱 AI 轻量级模型，快速响应适合简单任务',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': None},
        ]
    },
    {
        'provider_key': 'z.ai',
        'name': 'Z.AI Coding Plan',
        'website': 'https://z.ai',
        'logo_path': '/providers/zai-logo.png',
        'is_enabled': True,
        'models': [
            {'model_key': 'glm-5', 'display_name': 'GLM-5', 'description': '智谱 AI 最新一代旗舰模型，超长上下文支持',
             'context_length': '200k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': None},
            {'model_key': 'glm-4.7', 'display_name': 'GLM-4.7', 'description': '智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1441},
            {'model_key': 'glm-4.6', 'display_name': 'GLM-4.6', 'description': '智谱 AI 高性能模型，平衡速度与质量',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1356},
            {'model_key': 'glm-4.5-air', 'display_name': 'GLM-4.5 Air', 'description': '智谱 AI 轻量级模型，快速响应适合简单任务',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': None},
        ]
    },
    {
        'provider_key': 'volcengine',
        'name': '火山引擎 Coding Plan',
        'website': 'https://volcengine.com',
        'logo_path': '/providers/volcengine-logo.png',
        'is_enabled': True,
        'models': [
            {'model_key': 'doubao-seed-code', 'display_name': 'Doubao Seed Code', 'description': '豆包种子代码模型，专注于代码生成和理解',
             'context_length': '256k', 'max_output_length': '32k', 'input_types': ['Text', 'Image'], 'output_types': ['Text'], 'coding_score': 1014},
            {'model_key': 'kimi-k2.5', 'display_name': 'Kimi K2.5', 'description': 'Kimi K2.5 高性能模型',
             'context_length': '128k', 'max_output_length': '128k', 'input_types': ['Text', 'Image', 'Video'], 'output_types': ['Text'], 'coding_score': 1447},
            {'model_key': 'kimi-k2', 'display_name': 'Kimi K2', 'description': 'Kimi K2 模型',
             'context_length': '128k', 'max_output_length': '128k', 'input_types': ['Text', 'Image', 'Video'], 'output_types': ['Text'], 'coding_score': 1330},
            {'model_key': 'glm-4.7', 'display_name': 'GLM-4.7', 'description': '智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力',
             'context_length': '128k', 'max_output_length': '4k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1441},
            {'model_key': 'deepseek-v3.2', 'display_name': 'DeepSeek V3.2', 'description': 'DeepSeek V3.2 高性能模型',
             'context_length': '128k', 'max_output_length': '8k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1377},
        ]
    },
    {
        'provider_key': 'moonshot',
        'name': '月之暗面 Coding Plan',
        'website': 'https://kimi.com',
        'logo_path': '/providers/moonshot-logo.png',
        'is_enabled': True,
        'models': [
            {'model_key': 'kimi-k2.5', 'display_name': 'Kimi K2.5', 'description': 'Kimi K2.5 高性能模型',
             'context_length': '128k', 'max_output_length': '128k', 'input_types': ['Text', 'Image', 'Video'], 'output_types': ['Text'], 'coding_score': 1447},
        ]
    },
    {
        'provider_key': 'minimax',
        'name': 'MiniMax Coding Plan',
        'website': 'https://www.minimaxi.com',
        'logo_path': '/providers/minimax-logo.png',
        'is_enabled': True,
        'models': [
            {'model_key': 'minimax-m2.1', 'display_name': 'MiniMax M2.1', 'description': 'MiniMax M2.1 高性能代码模型，230B 总参数，10B 激活参数',
             'context_length': '196k', 'max_output_length': '65k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': 1409},
        ]
    },
    {
        'provider_key': 'openrouter',
        'name': 'OpenRouter Coding Plan',
        'website': 'https://openrouter.ai',
        'logo_path': '/providers/openrouter-logo.png',
        'is_enabled': True,
        'models': [
            {'model_key': 'pony-alpha', 'display_name': 'Pony Alpha', 'description': 'OpenRouter 高性能大语言模型',
             'context_length': '200k', 'max_output_length': '131k', 'input_types': ['Text'], 'output_types': ['Text'], 'coding_score': None},
        ]
    },
]


def upgrade() -> None:
    # Create provider_configs table
    op.create_table(
        'provider_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=False),
        sa.Column('logo_path', sa.String(length=500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_key')
    )
    op.create_index(op.f('ix_provider_configs_provider_key'), 'provider_configs', ['provider_key'], unique=True)
    op.create_index(op.f('ix_provider_configs_is_enabled'), 'provider_configs', ['is_enabled'], unique=False)

    # Create provider_models table with CASCADE delete
    op.create_table(
        'provider_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_config_id', sa.Integer(), nullable=False),
        sa.Column('model_key', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('context_length', sa.String(length=50), nullable=False),
        sa.Column('max_output_length', sa.String(length=50), nullable=False),
        sa.Column('input_types', sa.JSON(), nullable=True),
        sa.Column('output_types', sa.JSON(), nullable=True),
        sa.Column('coding_score', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['provider_config_id'], ['provider_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_config_id', 'model_key', name='idx_provider_model_unique')
    )
    op.create_index(op.f('ix_provider_models_provider_config_id'), 'provider_models', ['provider_config_id'], unique=False)
    op.create_index(op.f('ix_provider_models_is_enabled'), 'provider_models', ['is_enabled'], unique=False)

    # Insert initial data
    connection = op.get_bind()

    for provider in PROVIDER_DATA:
        # Insert provider
        provider_result = connection.execute(
            sa.text("""
                INSERT INTO provider_configs (provider_key, name, website, logo_path, is_enabled, created_at, updated_at)
                VALUES (:provider_key, :name, :website, :logo_path, :is_enabled, NOW(), NOW())
                RETURNING id
            """),
            {
                'provider_key': provider['provider_key'],
                'name': provider['name'],
                'website': provider['website'],
                'logo_path': provider['logo_path'],
                'is_enabled': provider['is_enabled']
            }
        )
        provider_id = provider_result.fetchone()[0]

        # Insert models for this provider
        for model in provider['models']:
            connection.execute(
                sa.text("""
                    INSERT INTO provider_models
                    (provider_config_id, model_key, display_name, description, context_length,
                     max_output_length, input_types, output_types, coding_score, is_enabled, created_at, updated_at)
                    VALUES (:provider_config_id, :model_key, :display_name, :description, :context_length,
                            :max_output_length, :input_types, :output_types, :coding_score, :is_enabled, NOW(), NOW())
                """),
                {
                    'provider_config_id': provider_id,
                    'model_key': model['model_key'],
                    'display_name': model['display_name'],
                    'description': model['description'],
                    'context_length': model['context_length'],
                    'max_output_length': model['max_output_length'],
                    'input_types': json.dumps(model['input_types']) if model['input_types'] else None,
                    'output_types': json.dumps(model['output_types']) if model['output_types'] else None,
                    'coding_score': model['coding_score'],
                    'is_enabled': True
                }
            )

    print(f"Inserted {len(PROVIDER_DATA)} providers with initial model configurations")


def downgrade() -> None:
    # Drop tables in correct order (child first, then parent)
    op.drop_index(op.f('ix_provider_models_is_enabled'), table_name='provider_models')
    op.drop_index(op.f('ix_provider_models_provider_config_id'), table_name='provider_models')
    op.drop_table('provider_models')

    op.drop_index(op.f('ix_provider_configs_is_enabled'), table_name='provider_configs')
    op.drop_index(op.f('ix_provider_configs_provider_key'), table_name='provider_configs')
    op.drop_table('provider_configs')
