"""add clinics external_id

Revision ID: 61e8accee3d1
Revises: a9d199ba71f5
Create Date: 2026-09-12 15:57:36.506443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '61e8accee3d1'
down_revision: Union[str, None] = 'a9d199ba71f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clinics', sa.Column('external_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_clinics_external_id'), 'clinics', ['external_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_clinics_external_id'), table_name='clinics')
    op.drop_column('clinics', 'external_id')
