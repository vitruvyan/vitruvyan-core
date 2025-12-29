"""merge_three_heads

Revision ID: b4dfbece7fcb
Revises: 001_create_external_datasets, 20251104_vsgs, a675c9c6611e
Create Date: 2025-11-09 17:32:44.988690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4dfbece7fcb'
down_revision: Union[str, Sequence[str], None] = ('001_create_external_datasets', '20251104_vsgs', 'a675c9c6611e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
