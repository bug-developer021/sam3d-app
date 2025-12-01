"""initial schema

Revision ID: v1_initial_schema
Revises:
Create Date: 2024-06-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v1_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


processing_status = sa.Enum(
    'queued', 'processing', 'completed', 'failed', name='processing_status'
)
asset_type = sa.Enum('input_image', 'output_mesh', 'texture', name='asset_type')


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('api_key_hash', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_api_key_hash'), 'users', ['api_key_hash'], unique=False)

    op.create_table(
        'projects',
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_user_id', 'projects', ['user_id'], unique=False)
    op.create_index('ix_projects_created_at', 'projects', ['created_at'], unique=False)

    op.create_table(
        'processing_jobs',
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('status', processing_status, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_processing_jobs_status', 'processing_jobs', ['status'], unique=False)
    op.create_index('ix_processing_jobs_created_at', 'processing_jobs', ['created_at'], unique=False)

    op.create_table(
        'assets',
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', asset_type, nullable=False),
        sa.Column('uri', sa.String(length=1024), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assets_project_id', 'assets', ['project_id'], unique=False)
    op.create_index('ix_assets_created_at', 'assets', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_assets_created_at', table_name='assets')
    op.drop_index('ix_assets_project_id', table_name='assets')
    op.drop_table('assets')

    op.drop_index('ix_processing_jobs_created_at', table_name='processing_jobs')
    op.drop_index('ix_processing_jobs_status', table_name='processing_jobs')
    op.drop_table('processing_jobs')

    op.drop_index('ix_projects_created_at', table_name='projects')
    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_table('projects')

    op.drop_index(op.f('ix_users_api_key_hash'), table_name='users')
    op.drop_table('users')

    processing_status.drop(op.get_bind(), checkfirst=False)
    asset_type.drop(op.get_bind(), checkfirst=False)
