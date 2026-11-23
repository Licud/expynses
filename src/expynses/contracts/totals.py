
from dataclasses import dataclass

from decimal import Decimal 

@dataclass(frozen=True, kw_only=True)
class MonthFiguresDto:
    month: int
    income: Decimal
    paid: Decimal
    on_credit: Decimal
    card_repaid: Decimal
    debits: Decimal
    balance: Decimal | None
    card_owed: Decimal | None


@dataclass(frozen=True, kw_only=True)
class MonthTotalDto:
    month: int
    total: Decimal