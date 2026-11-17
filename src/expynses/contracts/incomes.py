from dataclasses import dataclass

import datetime
import decimal
import uuid

@dataclass(frozen=True, kw_only=True)
class NewIncomeDto:
    date: datetime.date
    amount: decimal.Decimal
    source: str


@dataclass(frozen=True, kw_only=True)
class IncomeDto:
    id: uuid.UUID
    date: datetime.date
    amount: decimal.Decimal
    source: str


@dataclass(frozen=True, kw_only=True)
class IncomeFilterDto:
    from_date: datetime.date | None = None
    to_date: datetime.date | None = None
    take: int | None = None