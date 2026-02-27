"""Add global_models table

Revision ID: 20260227_add_global_models_table
Revises: 20260226_add_base_url_provider_configs
Create Date: 2026-02-27

"""
from typing import Sequence, Union
from alembic import op

revision: str = '20260227_add_global_models_table'
down_revision: Union[str, None] = '20260226_add_base_url_provider_configs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use IF NOT EXISTS to handle case where table was already created
    op.execute("""
        CREATE TABLE IF NOT EXISTS global_models (
            id SERIAL NOT NULL,
            model_key VARCHAR(100) NOT NULL,
            display_name VARCHAR(200) NOT NULL,
            description VARCHAR(1000),
            context_length VARCHAR(50) NOT NULL,
            max_output_length VARCHAR(50) NOT NULL,
            input_types JSON,
            output_types JSON,
            coding_score INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_global_models_model_key UNIQUE (model_key)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_models_model_key ON global_models (model_key)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_global_models_model_key")
    op.execute("DROP TABLE IF EXISTS global_models")
