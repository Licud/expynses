import datetime
import decimal
import uuid

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class NewExpenseDto:
    date: datetime.date
    price: decimal.Decimal
    notes: str
    is_credit: bool
    expense_type_id: uuid.UUID