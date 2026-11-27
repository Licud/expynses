"""Number crunching for the Forecasts page: forecasts, still rough.

Everything starts from the Monthly page's "Left to spend" and then looks forward month by month:
the debits that fall due, and the income you tell it to expect. Nothing here is a prediction.
"""

import datetime
import decimal

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from expynses.contracts.debits import DebitTemplateDto, DebitTemplateFilterDto
from expynses.contracts.totals import MonthFiguresDto
from expynses.services.debits import search_debit_templates
from expynses.services.totals import left_to_spend_for_month, monthly_figures
from expynses.ui.debit_month_dialog import _due_in, month_debits, pending
from expynses.ui.reports_data import ZERO, add_months

MAX_MONTHS = 36  # how far ahead the forecast looks


# --- The forecast ---


@dataclass(frozen=True)
class ForecastMonth:
    month: datetime.date
    debits: decimal.Decimal  # debits leaving this month
    income: decimal.Decimal  # expected income this month
    balance: decimal.Decimal  # left to spend at the end of the month


def build_forecast(
    start: decimal.Decimal,
    this_month: datetime.date,
    pending_now: decimal.Decimal,
    debits_in: Callable[[datetime.date], decimal.Decimal],
    income: decimal.Decimal,
    months_ahead: int = MAX_MONTHS,
) -> list[ForecastMonth]:
    """Left to spend at the end of this month and each of the next `months_ahead` months.

    This month is already under way, so it only loses the debits not yet ticked off: its income
    and spending are in `start` already. Every later month adds the expected income and takes off
    its own debits.
    """
    running = start - pending_now
    months = [ForecastMonth(this_month, pending_now, ZERO, running)]
    for k in range(1, months_ahead + 1):
        month = add_months(this_month, k)
        due = debits_in(month)
        running += income - due
        months.append(ForecastMonth(month, due, income, running))
    return months


def debits_due(templates: Iterable[DebitTemplateDto], month: datetime.date) -> decimal.Decimal:
    """The active debits that fall due in a month (savings too: that money leaves the account)."""
    return sum((t.amount for t in templates if t.is_active and _due_in(t, month)), ZERO)


def first_below_zero(forecast: Sequence[ForecastMonth]) -> ForecastMonth | None:
    return next((f for f in forecast if f.balance < 0), None)


@dataclass(frozen=True)
class TargetResult:
    status: str  # "already", "reached" or "never"
    months: int = 0  # months after this one; 0 means by the end of this month
    month: datetime.date | None = None


def months_to_target(start: decimal.Decimal, forecast: Sequence[ForecastMonth], target: decimal.Decimal) -> TargetResult:
    """When the balance first gets to the target, going up if it is above where you are, down if below."""
    if target == start:
        return TargetResult("already")
    for index, f in enumerate(forecast):
        hit = f.balance >= target if target > start else f.balance <= target
        if hit:
            return TargetResult("reached", index, f.month)
    return TargetResult("never")


def after_months(forecast: Sequence[ForecastMonth], months: int) -> ForecastMonth:
    """The forecast `months` months after this one (0 is the end of this month)."""
    return forecast[max(0, min(months, len(forecast) - 1))]


def monthly_change(forecast: Sequence[ForecastMonth]) -> decimal.Decimal:
    """How much the balance moves in an ordinary future month (the one after this)."""
    if len(forecast) < 2:
        return ZERO
    f = forecast[1]
    return f.income - f.debits


# --- Gathering the inputs from the services ---


@dataclass(frozen=True)
class ForecastInputs:
    today: datetime.date
    start: decimal.Decimal  # this month's Left to spend, the same number as on the Monthly page
    pending_now: decimal.Decimal  # debits this month not ticked off yet
    templates: list[DebitTemplateDto]
    figures: list[MonthFiguresDto]  # this year, month by month


def load_inputs(today: datetime.date | None = None) -> ForecastInputs:
    today = today or datetime.date.today()
    start_of_month = today.replace(day=1)

    return ForecastInputs(
        today=today,
        start=left_to_spend_for_month(start_of_month),
        pending_now=sum((d.amount for d in pending(month_debits(start_of_month))), ZERO),
        templates=list(search_debit_templates(DebitTemplateFilterDto())),
        figures=list(monthly_figures(today.year)),
    )


def forecast_for(inputs: ForecastInputs, income: decimal.Decimal) -> list[ForecastMonth]:
    """The forecast with the debits that fall due and the given income each month."""
    return build_forecast(
        start=inputs.start,
        this_month=inputs.today.replace(day=1),
        pending_now=inputs.pending_now,
        debits_in=lambda month: debits_due(inputs.templates, month),
        income=income,
    )


# --- The chart: this year, recorded then projected ---


@dataclass(frozen=True)
class OutlookMonth:
    month: datetime.date
    balance: decimal.Decimal  # account at the end of the month
    card_owed: decimal.Decimal
    outgoing: decimal.Decimal
    projected: bool  # worked out by the forecast, not recorded


def build_outlook(
    year: int, figures: Sequence[MonthFiguresDto], forecast: Sequence[ForecastMonth], today: datetime.date
) -> list[OutlookMonth]:
    """All twelve months: those before this month as recorded, this month onwards from the forecast.

    Card owed stays where it is now: no new card spending and no repayments are assumed.
    """
    this_month = datetime.date(today.year, today.month, 1)
    projected = {f.month: f for f in forecast}
    owed_now = ZERO
    months = []
    for fig in figures:
        start = datetime.date(year, fig.month, 1)
        recorded_outgoing = fig.paid + fig.card_repaid + fig.debits
        if start < this_month:
            months.append(OutlookMonth(start, fig.balance or ZERO, fig.card_owed or ZERO, recorded_outgoing, False))
            continue
        if start == this_month:
            owed_now = fig.card_owed or ZERO
        f = projected[start]
        # This month keeps what has already gone out and adds what is still to come.
        outgoing = f.debits + (recorded_outgoing if start == this_month else ZERO)
        months.append(OutlookMonth(start, f.balance, owed_now, outgoing, True))
    return months


# --- Reading what people type ---


def parse_money(text: str) -> decimal.Decimal | None:
    """£1,234.50 or 1234.5 become a Decimal; anything else is None. Blank is None too."""
    cleaned = text.replace("£", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = decimal.Decimal(cleaned)
    except decimal.InvalidOperation:
        return None
    return value if value.is_finite() else None
