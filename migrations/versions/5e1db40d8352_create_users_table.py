"""create_users_table

Revision ID: 5e1db40d8352
Revises: 
Create Date: 2025-10-29 18:44:36.006826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e1db40d8352'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create users table."""
    op.create_table(
        'users',
        sa.Column('username', sa.String(255), primary_key=True),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('disabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create index on role for faster queries
    op.create_index('idx_users_role', 'users', ['role'])


def downgrade() -> None:
    """Downgrade schema - drop users table."""
    op.drop_index('idx_users_role', table_name='users')
    op.drop_table('users')
