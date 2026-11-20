"""seed expense types

Revision ID: 9b9fc64b88dc
Revises: d9ab17791553
Create Date: 2026-11-16 21:22:44.761862

"""
import sqlalchemy as sa
import uuid

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9b9fc64b88dc'
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
        {"id": uuid.uuid4(), "name": "Eating Out"},
        {"id": uuid.uuid4(), "name": "Grocery"},
        {"id": uuid.uuid4(), "name": "Travel"},
        {"id": uuid.uuid4(), "name": "Games"},
        {"id": uuid.uuid4(), "name": "Bills"},
        {"id": uuid.uuid4(), "name": "Shopping"},
        {"id": uuid.uuid4(), "name": "Car"},
        {"id": uuid.uuid4(), "name": "Withdrawal"},
        {"id": uuid.uuid4(), "name": "Other"},
    ])


def downgrade() -> None:
    op.execute(
        "DELETE FROM expense_types"
    )
