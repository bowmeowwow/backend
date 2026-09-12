"""add missing clinics category index

The category column was added to the live DB by hand (manual ALTER
TABLE, before Alembic existed) without its index, unlike every other
indexed column on this model. This brings it in line with what the
model has declared all along.

Revision ID: 149ad5685e19
Revises: 8c9725dd6b82
Create Date: 2026-09-12 13:23:09.195232

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '149ad5685e19'
down_revision: Union[str, None] = '8c9725dd6b82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_clinics_category'), 'clinics', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_clinics_category'), table_name='clinics')
