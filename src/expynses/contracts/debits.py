
from dataclasses import dataclass
from enum import Enum

import datetime
import uuid
import decimal


class Frequency(Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True, kw_only=True)
class NewDebitTemplateDto:
    date: datetime.date
    amount: decimal.Decimal
    name: str
    frequency: Frequency
    is_savings: bool
    is_active: bool


@dataclass(frozen=True, kw_only=True)
class UpdateDebitTemplateDto:
    name: str
    date: datetime.date
    amount: decimal.Decimal
    frequency: Frequency
    is_active: bool
    

@dataclass(frozen=True, kw_only=True)
class DebitTemplateDto:
    id: uuid.UUID
    date: datetime.date
    amount: decimal.Decimal
    name: str
    frequency: Frequency
    is_savings: bool
    is_active: bool


@dataclass(frozen=True, kw_only=True)
class DebitTemplateFilterDto:
    id: uuid.UUID | None = None
    is_active: bool | None = None


@dataclass(frozen=True, kw_only=True)
class DebitPaymentDto:
    id: uuid.UUID
    date: datetime.date
    amount: decimal.Decimal
    template_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class DebitPaymentFilterDto:
    id: uuid.UUID | None = None
    given_date: datetime.date | None = None
    from_date: datetime.date | None = None
    to_date: datetime.date | None = None

