"""add user fields

Revision ID: 7a3e390234a9
Revises: e642b85a3042
Create Date: 2026-07-11 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3e390234a9'
down_revision: Union[str, None] = 'e642b85a3042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('account_status', sa.String(length=20), nullable=False, server_default='active'))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    
    # Run data migration to upgrade legacy roles to uppercase and USER
    op.execute("UPDATE users SET role = 'USER' WHERE role IN ('viewer', 'manager', 'user', 'viewers') OR role IS NULL")
    op.execute("UPDATE users SET role = 'ADMIN' WHERE role IN ('admin', 'admins')")


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('account_status')
