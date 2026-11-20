
from dataclasses import dataclass

import datetime
import decimal
import uuid

@dataclass(frozen=True, kw_only=True)
class NewCreditPaymentDto:
    date: datetime.date
    amount: decimal.Decimal


@dataclass(frozen=True, kw_only=True)
class CreditPaymentDto:
    id: uuid.UUID
    date: datetime.date
    amount: decimal.Decimal


@dataclass(frozen=True, kw_only=True)
class CreditPaymentFilterDto:
    id: uuid.UUID | None = None
    from_date: datetime.date | None = None
    to_date: datetime.date | None = None