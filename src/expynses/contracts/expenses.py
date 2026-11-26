import uuid

from dataclasses import dataclass

from datetime import date
from decimal import Decimal
from expynses.contracts.expenses_types import ExpenseTypeDto


@dataclass(frozen=True, kw_only=True)
class NewExpenseDto:
    date: date
    price: Decimal
    notes: str
    is_credit: bool
    expense_type_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class ExpenseDto:
    id: uuid.UUID
    date: date
    price: Decimal
    notes: str
    is_credit: bool
    expense_type: ExpenseTypeDto


@dataclass(frozen=True, kw_only=True)
class ExpenseFilterDto:
    id: uuid.UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    is_credit: bool | None = None


@dataclass(frozen=True, kw_only=True)
class TypeMonthTotalDto:
    expense_type: ExpenseTypeDto
    month: date
    total: Decimal