"""add user phone and pet birth_date/weight

Revision ID: a9d199ba71f5
Revises: 149ad5685e19
Create Date: 2026-09-12 15:45:10.974266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9d199ba71f5'
down_revision: Union[str, None] = '149ad5685e19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pets', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('pets', sa.Column('weight', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone')
    op.drop_column('pets', 'weight')
    op.drop_column('pets', 'birth_date')
