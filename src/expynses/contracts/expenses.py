import datetime
import decimal
import uuid

from dataclasses import dataclass

from expynses.contracts.expenses_types import ExpenseTypeDto


@dataclass(frozen=True, kw_only=True)
class NewExpenseDto:
    date: datetime.date
    price: decimal.Decimal
    notes: str
    is_credit: bool
    expense_type_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class ExpenseDto:
    id: uuid.UUID
    date: datetime.date
    price: decimal.Decimal
    notes: str
    is_credit: bool
    expense_type: ExpenseTypeDto


@dataclass(frozen=True, kw_only=True)
class ExpenseFilterDto:
    id: uuid.UUID | None = None
    from_date: datetime.date | None = None
    to_date: datetime.date | None = None
    is_credit: bool | None = None