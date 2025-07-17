"""Fix user columns: non-nullable with defaults

Revision ID: 21d05aacae79
Revises: bdde41db3c40
Create Date: 2025-07-16 22:44:22.945981

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '21d05aacae79'
down_revision = 'bdde41db3c40'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_active',
                              existing_type=sa.Boolean(),
                              nullable=False,
                              server_default=sa.sql.expression.true())

        batch_op.alter_column('is_deleted',
                              existing_type=sa.Boolean(),
                              nullable=False,
                              server_default=sa.sql.expression.false())

        batch_op.alter_column('is_password_set',
                              existing_type=sa.Boolean(),
                              nullable=False,
                              server_default=sa.sql.expression.false())

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_active',
                              existing_type=sa.Boolean(),
                              nullable=True,
                              server_default=None)

        batch_op.alter_column('is_deleted',
                              existing_type=sa.Boolean(),
                              nullable=True,
                              server_default=None)

        batch_op.alter_column('is_password_set',
                              existing_type=sa.Boolean(),
                              nullable=True,
                              server_default=None)

    # ### end Alembic commands ###
