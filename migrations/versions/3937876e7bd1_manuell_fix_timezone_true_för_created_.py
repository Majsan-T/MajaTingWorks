"""Manuell fix: timezone=True för created_at och updated_at"""

from alembic import op
import sqlalchemy as sa


# Unik ID (ändra till din fil)
revision = 'abc123'
down_revision = 'a08498d4b6f2'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('blog_posts', 'created_at',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        nullable=False
    )
    op.alter_column('blog_posts', 'updated_at',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        nullable=True
    )


def downgrade():
    op.alter_column('blog_posts', 'updated_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        nullable=True
    )
    op.alter_column('blog_posts', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        nullable=False
    )
