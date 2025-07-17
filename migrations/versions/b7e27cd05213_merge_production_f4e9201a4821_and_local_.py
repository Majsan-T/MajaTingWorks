"""Merge production (f4e9201a4821) and local (21d05aacae79)

Revision ID: b7e27cd05213
Revises: 21d05aacae79, f4e9201a4821
Create Date: 2025-07-17 22:12:26.331720

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e27cd05213'
down_revision = ('21d05aacae79', 'f4e9201a4821')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
