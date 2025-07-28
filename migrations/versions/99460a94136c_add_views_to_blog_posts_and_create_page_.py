"""Add views to blog_posts and create page_views table

Revision ID: 99460a94136c
Revises: 491705b9701d
Create Date: 2025-07-22 20:05:08.036613

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '99460a94136c'
down_revision = '491705b9701d'
branch_labels = None
depends_on = None



def upgrade():
    op.execute("UPDATE blog_posts SET views = 0 WHERE views IS NULL")

    with op.batch_alter_table('blog_posts', schema=None) as batch_op:
        batch_op.alter_column(
            'views',
            existing_type=mysql.INTEGER(),
            nullable=False,
            server_default='0'
        )

    # ✅ Skapa bara tabellen om den inte finns
    bind = op.get_bind()
    inspector = inspect(bind)
    if "page_views" not in inspector.get_table_names():
        op.create_table(
            'page_views',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('endpoint', sa.String(length=255), nullable=False, unique=True),
            sa.Column('views', sa.Integer(), nullable=False, server_default='0')
        )


def downgrade():
    # ✅ Ta bort page_views-tabellen
    op.drop_table('page_views')

    # ✅ Tillåt NULL igen på blog_posts.views (om du vill rulla tillbaka)
    with op.batch_alter_table('blog_posts', schema=None) as batch_op:
        batch_op.alter_column(
            'views',
            existing_type=mysql.INTEGER(),
            nullable=True,
            server_default=None
        )
