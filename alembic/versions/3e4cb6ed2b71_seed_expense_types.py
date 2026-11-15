"""seed expense types

Revision ID: 3e4cb6ed2b71
Revises: d9ab17791553
Create Date: 2026-11-15 20:45:06.590498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '3e4cb6ed2b71'
down_revision: Union[str, Sequence[str], None] = 'd9ab17791553'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    expense_types = sa.table(
        "expense_types",
        sa.column("id", sa.Uuid),
        sa.column("name", sa.String),
    )
    op.bulk_insert(expense_types, [
        {"id": uuid.uuid4(), "name": "Food"},
        {"id": uuid.uuid4(), "name": "Rent"},
        {"id": uuid.uuid4(), "name": "Transport"},
    ])


def downgrade() -> None:
    op.execute(
        "DELETE FROM expense_types WHERE name IN ('Food', 'Rent', 'Transport')"
    )
