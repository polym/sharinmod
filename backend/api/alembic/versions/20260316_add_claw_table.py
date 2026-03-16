"""Add claws table

Revision ID: 20260316_add_claw_table
Revises: 20260307_add_real_model_to_provider_models
Create Date: 2026-03-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260316_add_claw_table'
down_revision: Union[str, None] = '20260307_add_real_model_to_provider_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE IF NOT EXISTS clawtype AS ENUM ('NanoBot', 'OpenClaw', 'ZeroBot')")
    op.execute("CREATE TYPE IF NOT EXISTS clawstatus AS ENUM ('pending', 'running', 'failed', 'stopped')")

    op.create_table(
        'claws',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.Enum('NanoBot', 'OpenClaw', 'ZeroBot', name='clawtype'), nullable=False),
        sa.Column('qq_bot_id', sa.String(255), nullable=False),
        sa.Column('qq_bot_secret', sa.String(255), nullable=False),
        sa.Column('k8s_deployment_name', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('pending', 'running', 'failed', 'stopped', name='clawstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_claw_user_status', 'claws', ['user_id', 'status'])
    op.create_index(op.f('ix_claws_user_id'), 'claws', ['user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_claws_user_id'), table_name='claws')
    op.drop_index('idx_claw_user_status', table_name='claws')
    op.drop_table('claws')
    op.execute("DROP TYPE IF EXISTS clawstatus")
    op.execute("DROP TYPE IF EXISTS clawtype")
