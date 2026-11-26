
from dataclasses import dataclass
from decimal import Decimal
from datetime import date

import uuid

@dataclass(frozen=True, kw_only=True)
class NewCreditPaymentDto:
    date: date
    amount: Decimal
    is_external: bool


@dataclass(frozen=True, kw_only=True)
class CreditPaymentDto:
    id: uuid.UUID
    date: date
    amount: Decimal
    is_external: bool


@dataclass(frozen=True, kw_only=True)
class CreditPaymentFilterDto:
    id: uuid.UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    is_external: bool | None = None