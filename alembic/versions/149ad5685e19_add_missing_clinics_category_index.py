"""add missing clinics category index

The category column was added to the live MySQL DB by hand (manual
ALTER TABLE, before Alembic existed) without its index, unlike every
other indexed column on this model. This brought it in line with what
the model had declared all along.

Guarded with an existence check: by the time the baseline migration
was generated, the model already had index=True on this column, so
on any DB that goes through the full chain from empty (as opposed to
the legacy MySQL DB, which was `alembic stamp head`-ed past the
baseline without actually running it) the baseline's own
create_table already creates this index, and an unconditional
create_index here would fail as a duplicate.

Revision ID: 149ad5685e19
Revises: 8c9725dd6b82
Create Date: 2026-09-12 13:23:09.195232

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '149ad5685e19'
down_revision: Union[str, None] = '8c9725dd6b82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    existing = {index["name"] for index in inspector.get_indexes("clinics")}
    if "ix_clinics_category" not in existing:
        op.create_index(op.f("ix_clinics_category"), "clinics", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinics_category"), table_name="clinics")
