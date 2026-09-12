"""add news_articles table

Revision ID: f10a5b881a49
Revises: 61e8accee3d1
Create Date: 2026-09-12 16:20:47.071835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f10a5b881a49'
down_revision: Union[str, None] = '61e8accee3d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'news_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('summary', sa.String(length=1000), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_news_articles_external_id'), 'news_articles', ['external_id'], unique=True)
    op.create_index(op.f('ix_news_articles_id'), 'news_articles', ['id'], unique=False)
    op.create_index(op.f('ix_news_articles_published_at'), 'news_articles', ['published_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_news_articles_published_at'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_id'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_external_id'), table_name='news_articles')
    op.drop_table('news_articles')
