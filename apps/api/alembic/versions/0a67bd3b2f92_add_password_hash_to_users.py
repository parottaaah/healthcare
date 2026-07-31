"""add password_hash to users

Revision ID: 0a67bd3b2f92
Revises: 273a007d3dbf
Create Date: 2026-07-31 12:11:26.145131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a67bd3b2f92'
down_revision: Union[str, None] = '273a007d3dbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
