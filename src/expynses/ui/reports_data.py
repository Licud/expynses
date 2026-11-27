"""Number crunching for the report pages (Year, Cash flow, Categories).

Everything in here works out totals from the plain search_* services, in Python.
It lives in the UI for now so the backend stays untouched, but it is business
logic: each piece marked "SERVICE CANDIDATE" is listed in SERVICE_CANDIDATES.md
at the repo root, with a note on where it would go.
"""

import calendar
import datetime
import decimal

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from expynses.contracts.credit_payments import CreditPaymentDto
from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto
from expynses.contracts.incomes import IncomeDto
from expynses.services.expenses import search_expenses, spending_by_type
from expynses.services.expenses_types import get_expense_types
from expynses.services.totals import monthly_figures

ZERO = decimal.Decimal(0)


# --- Month helpers (UI-only, fine to stay here) ---


def month_end(start: datetime.date) -> datetime.date:
    return start.replace(day=calendar.monthrange(start.year, start.month)[1])


def add_months(start: datetime.date, delta: int) -> datetime.date:
    index = start.year * 12 + (start.month - 1) + delta
    return datetime.date(index // 12, index % 12 + 1, 1)


def months_of_year(year: int) -> list[datetime.date]:
    return [datetime.date(year, m, 1) for m in range(1, 13)]


def months_ending(last: datetime.date, count: int) -> list[datetime.date]:
    """The `count` months up to and including `last`, oldest first."""
    return [add_months(last, -i) for i in reversed(range(count))]


# --- Year figures ---


@dataclass(frozen=True)
class MonthFigures:
    start: datetime.date
    income: decimal.Decimal
    paid: decimal.Decimal  # expenses paid in full
    on_credit: decimal.Decimal  # expenses put on the card
    card_repaid: decimal.Decimal  # credit card repayments made this month
    debits: decimal.Decimal  # debit payments ticked off this month
    # Account balance and card owed at the end of the month. None for months
    # that haven't started yet, since there's nothing meaningful to show.
    balance: decimal.Decimal | None
    card_owed: decimal.Decimal | None
    is_future: bool

    @property
    def has_activity(self) -> bool:
        """Anything at all recorded this month (empty months skew averages)."""
        return any((self.income, self.paid, self.on_credit, self.card_repaid, self.debits))

    @property
    def spent(self) -> decimal.Decimal:
        """Everything bought this month, however it was paid."""
        return self.paid + self.on_credit

    @property
    def outgoing(self) -> decimal.Decimal:
        """Money that actually left the account this month.

        Same rule as `totals.balance`: card spending only counts once it's
        repaid, so this is paid-in-full + card repayments + debits.
        """
        return self.paid + self.card_repaid + self.debits

    @property
    def net(self) -> decimal.Decimal:
        return self.income - self.outgoing


def year_figures(year: int) -> list[MonthFigures]:
    """Income, spending and end-of-month balances for each month of a year."""
    return [
        MonthFigures(
            start=datetime.date(year, dto.month, 1),
            income=dto.income,
            paid=dto.paid,
            on_credit=dto.on_credit,
            card_repaid=dto.card_repaid,
            debits=dto.debits,
            balance=dto.balance,
            card_owed=dto.card_owed,
            # The service leaves both as None for months that haven't started.
            is_future=dto.balance is None,
        )
        for dto in monthly_figures(year)
    ]


# --- Category spending ---


@dataclass(frozen=True)
class CategorySpending:
    months: list[datetime.date]
    categories: list[str]  # every category with spending, biggest total first
    amounts: dict[tuple[str, datetime.date], decimal.Decimal]

    def amount(self, category: str, month: datetime.date) -> decimal.Decimal:
        return self.amounts.get((category, month), ZERO)

    def category_total(self, category: str) -> decimal.Decimal:
        return sum((self.amount(category, m) for m in self.months), ZERO)

    def month_total(self, month: datetime.date) -> decimal.Decimal:
        return sum((self.amount(c, month) for c in self.categories), ZERO)

    @property
    def total(self) -> decimal.Decimal:
        return sum((self.month_total(m) for m in self.months), ZERO)


def category_spending(months: list[datetime.date]) -> CategorySpending:
    """How much went on each expense type in each of the given months."""
    rows = spending_by_type(months[0], month_end(months[-1]))
    amounts: dict[tuple[str, datetime.date], decimal.Decimal] = defaultdict(lambda: ZERO)
    for row in rows:
        amounts[(row.expense_type.name, row.month)] += row.total

    totals: dict[str, decimal.Decimal] = defaultdict(lambda: ZERO)
    for (name, _), amount in amounts.items():
        totals[name] += amount
    # Keep the type list's order for ties, so colours and rows stay put.
    order = {t.name: i for i, t in enumerate(get_expense_types())}
    categories = sorted(totals, key=lambda n: (-totals[n], order.get(n, len(order))))
    return CategorySpending(months=months, categories=categories, amounts=dict(amounts))


# --- Left to spend ---


def left_to_spend(
    expenses: Iterable[ExpenseDto],
    incomes: Iterable[IncomeDto],
    payments: Iterable[CreditPaymentDto],
    carried_over: decimal.Decimal,
    debits: decimal.Decimal,
) -> decimal.Decimal:
    """The Monthly page's "Left to spend" for one month, from that month's own records.

    Income plus what was carried over, less spending paid in full, less the debits ticked off
    and less card repayments made from the account. Card spending isn't taken off until it's
    repaid, and repayments made by someone else (external) never come off.
    """
    income = sum((i.amount for i in incomes), ZERO)
    paid = sum((e.price for e in expenses if not e.is_credit), ZERO)
    from_account = sum((p.amount for p in payments if not p.is_external), ZERO)
    return income + carried_over - paid - debits - from_account


# --- Repeat purchases ---


@dataclass(frozen=True)
class RepeatPurchase:
    note: str
    count: int
    total: decimal.Decimal

    @property
    def average(self) -> decimal.Decimal:
        return self.total / self.count


def repeat_purchases(expenses: Iterable[ExpenseDto], minimum: int = 3, take: int = 20) -> list[RepeatPurchase]:
    """Notes that keep coming back, biggest total first.

    "Coffee" and "coffee " count as the same thing. Empty notes are ignored.
    """
    counts: dict[str, int] = defaultdict(int)
    totals: dict[str, decimal.Decimal] = defaultdict(lambda: ZERO)
    shown: dict[str, str] = {}
    for e in expenses:
        key = e.notes.strip().lower()
        if not key:
            continue
        counts[key] += 1
        totals[key] += e.price
        shown.setdefault(key, e.notes.strip())
    repeats = [RepeatPurchase(shown[k], counts[k], totals[k]) for k in counts if counts[k] >= minimum]
    return sorted(repeats, key=lambda r: r.total, reverse=True)[:take]


# SERVICE CANDIDATE: expenses.repeat_purchases(from_date, to_date, minimum, take) -> list[RepeatPurchaseDto]
def repeat_purchases_in(months: list[datetime.date], minimum: int = 3, take: int = 20) -> list[RepeatPurchase]:
    """The repeat purchases across the given months."""
    expenses = search_expenses(ExpenseFilterDto(from_date=months[0], to_date=month_end(months[-1])))
    return repeat_purchases(expenses, minimum, take)


# --- Biggest purchases ---


def top_by_price(expenses: Iterable[ExpenseDto], take: int = 10) -> list[ExpenseDto]:
    """The most expensive expenses, biggest first. Ties keep their original order."""
    return sorted(expenses, key=lambda e: e.price, reverse=True)[:take]


# SERVICE CANDIDATE: expenses.top_expenses(from_date, to_date, take) -> list[ExpenseDto]
def biggest_purchases(year: int, take: int = 10) -> list[ExpenseDto]:
    """The biggest single purchases of a year, card or not."""
    first, last = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
    return top_by_price(search_expenses(ExpenseFilterDto(from_date=first, to_date=last)), take)


# --- No-spend days ---


@dataclass(frozen=True)
class NoSpendDays:
    days: int  # days looked at
    no_spend: int  # of those, days with nothing bought
    longest_run: int  # most no-spend days in a row
    current_run: int  # no-spend days in a row up to the last day looked at


def no_spend_days(expenses: Iterable[ExpenseDto], start: datetime.date, end: datetime.date) -> NoSpendDays:
    """Days from start to end (both included) on which nothing was bought, card or not."""
    if end < start:
        return NoSpendDays(0, 0, 0, 0)
    spent_on = {e.date for e in expenses}
    flags = [
        (start + datetime.timedelta(days=i)) not in spent_on
        for i in range((end - start).days + 1)
    ]
    longest = run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        longest = max(longest, run)
    return NoSpendDays(days=len(flags), no_spend=sum(flags), longest_run=longest, current_run=run)


def all_category_names() -> list[str]:
    """Every expense type, in the backend's order (used to keep colours stable)."""
    return [t.name for t in get_expense_types()]
