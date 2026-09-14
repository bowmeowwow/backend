"""add pet photo and expenses table

Revision ID: 62e7330c2d52
Revises: f10a5b881a49
Create Date: 2026-09-14 00:00:43.486357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '62e7330c2d52'
down_revision: Union[str, None] = 'f10a5b881a49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pet_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['pet_id'], ['pets.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_expenses_date'), 'expenses', ['date'], unique=False)
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)
    op.create_index(op.f('ix_expenses_pet_id'), 'expenses', ['pet_id'], unique=False)
    op.create_index(op.f('ix_expenses_user_id'), 'expenses', ['user_id'], unique=False)
    op.add_column('pets', sa.Column('photo', sa.LargeBinary(length=8000000), nullable=True))
    op.add_column('pets', sa.Column('photo_content_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('pets', 'photo_content_type')
    op.drop_column('pets', 'photo')
    op.drop_index(op.f('ix_expenses_user_id'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_pet_id'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_id'), table_name='expenses')
    op.drop_index(op.f('ix_expenses_date'), table_name='expenses')
    op.drop_table('expenses')
