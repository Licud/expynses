"""The 'Forecasts' page: where Left to spend is heading, from the debits due and the income you expect."""

import datetime
import decimal

import flet as ft

from expynses.ui import theme
from expynses.ui.forecasts_data import (
    MAX_MONTHS,
    ForecastInputs,
    ForecastMonth,
    OutlookMonth,
    after_months,
    build_outlook,
    first_below_zero,
    forecast_for,
    load_inputs,
    monthly_change,
    months_to_target,
    parse_money,
)
from expynses.ui.charts import Bar, Group, bar_chart, legend
from expynses.ui.report_widgets import page_header, signed_money
from expynses.ui.reports_data import ZERO

ACCOUNT_COLOR = theme.SLATE
DEBT_COLOR = theme.AMBER
OUTGOING_COLOR = theme.ACCENT
DEFAULT_MONTHS = 6


def _shade(color: str, projected: bool) -> str:
    """Projected bars are the same colour, but lighter."""
    return theme.tinted(color, 0.45) if projected else color


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


# --- The chart ---


def _assumptions(income: decimal.Decimal) -> str:
    text = "Lighter bars are projected from this month, using the debits still to come"
    if income:
        text += f" and {theme.money(income)} income a month"
    return text + ". Card owed is held where it is."


def _summary(start: decimal.Decimal, forecast: list[ForecastMonth], year: int) -> ft.Control:
    out = first_below_zero(forecast)
    if out:
        verdict = ft.Text(f"Runs out in {out.month:%B %Y}", size=14, weight=ft.FontWeight.W_600, color=theme.RED)
    else:
        verdict = ft.Text(f"Doesn't run out in {MAX_MONTHS} months", size=14, weight=ft.FontWeight.W_600,
                          color=theme.GREEN)
    december = next((f for f in forecast if f.month == datetime.date(year, 12, 1)), None)
    detail = f"Left to spend now {theme.money(start)}"
    if december:
        detail += f" · at the end of December {theme.money(december.balance)}"
    return ft.Row([verdict, ft.Text(detail, size=12, color=theme.MUTED)], spacing=14, wrap=True)


def _outlook_chart(
    months: list[OutlookMonth],
    forecast: list[ForecastMonth],
    inputs: ForecastInputs,
    income: decimal.Decimal,
) -> ft.Control:
    this_month = inputs.today.replace(day=1)
    out = first_below_zero(forecast)
    groups = []
    for m in months:
        note = " (projected)" if m.projected else ""
        groups.append(
            Group(
                label=m.month.strftime("%b"),
                bars=[
                    Bar.single(m.balance, _shade(ACCOUNT_COLOR, m.projected), f"Account{note}"),
                    # Debt hangs below the line, like on the Year page.
                    Bar.single(-m.card_owed, _shade(DEBT_COLOR, m.projected), f"Card owed{note}"),
                    Bar.single(m.outgoing, _shade(OUTGOING_COLOR, m.projected), f"Outgoing{note}"),
                ],
                highlighted=m.month == this_month,
                footer=ft.Text("runs out", size=10, color=theme.RED) if out and m.month == out.month else None,
            )
        )
    return theme.card(
        ft.Column(
            [
                theme.card_title(
                    f"Outlook for {inputs.today.year}",
                    legend([(ACCOUNT_COLOR, "Account"), (DEBT_COLOR, "Card owed"), (OUTGOING_COLOR, "Outgoing")]),
                ),
                ft.Text(_assumptions(income), size=12, color=theme.MUTED),
                ft.Container(height=8),
                _summary(inputs.start, forecast, inputs.today.year),
                ft.Container(height=8),
                bar_chart(groups, height=320, bar_width=16),
            ],
            spacing=4,
        ),
        padding=ft.Padding.only(left=20, right=24, top=20, bottom=18),
    )


# --- The two forecasting cards ---


def _result_lines(headline: str, lines: list[str], color: str = theme.TEXT) -> ft.Control:
    return ft.Column(
        [
            theme.heading(headline, size=26, color=color),
            *[ft.Text(line, size=12, color=theme.MUTED) for line in lines],
        ],
        spacing=4,
    )


def _hint(text: str) -> ft.Control:
    return ft.Text(text, size=13, color=theme.MUTED)


def _target_result(start: decimal.Decimal, forecast: list[ForecastMonth], target: decimal.Decimal | None) -> ft.Control:
    if target is None:
        return _hint("Enter a target to see how long it takes.")
    result = months_to_target(start, forecast, target)
    if result.status == "already":
        return _result_lines("You're already there", [f"Left to spend is {theme.money(start)}"])
    change = monthly_change(forecast)
    going = "saving up to" if target > start else "running down to"
    if result.status == "never":
        return _result_lines(
            f"Not within {MAX_MONTHS} months",
            [f"At about {signed_money(change)} a month it never gets to {theme.money(target)}."],
            theme.RED,
        )
    when = "This month" if result.months == 0 else _plural(result.months, "month")
    return _result_lines(
        when,
        [f"Around {result.month:%B %Y}, {going} {theme.money(target)}",
         f"From {theme.money(start)}, about {signed_money(change)} a month"],
        theme.GREEN if target > start else theme.AMBER,
    )


def _after_result(start: decimal.Decimal, forecast: list[ForecastMonth], months: int) -> ft.Control:
    f = after_months(forecast, months)
    return _result_lines(
        theme.money(f.balance),
        [f"End of {f.month:%B %Y}", f"{signed_money(f.balance - start)} from {theme.money(start)} now"],
        theme.TEXT if f.balance >= 0 else theme.RED,
    )


CARD_HEIGHT = 262  # both cards share it, so they line up whatever their results say


def _forecast_card(title: str, subtitle: str, field: ft.Control, result_box: ft.Control) -> ft.Control:
    return theme.card(
        ft.Column(
            [
                theme.card_title(title),
                ft.Text(subtitle, size=12, color=theme.MUTED),
                ft.Container(height=4),
                field,
                ft.Container(height=6),
                result_box,
            ],
            spacing=6,
        ),
        padding=20,
        expand=1,
        height=CARD_HEIGHT,
    )


def _income_card(field: ft.TextField) -> ft.Control:
    return theme.card(
        ft.Column(
            [
                theme.card_title("Expected monthly income"),
                ft.Text("What you expect to come in each month. Everything below uses it; blank means none.",
                        size=12, color=theme.MUTED),
                ft.Container(height=4),
                ft.Row([field]),
            ],
            spacing=6,
        ),
        padding=20,
    )


def _read_income(field: ft.TextField) -> decimal.Decimal | None:
    """Blank counts as 0. None means what's typed isn't an amount, and the field says so."""
    field.error = None
    text = field.value or ""
    if not text.strip():
        return ZERO
    value = parse_money(text)
    if value is None or value < 0:
        field.error = "Enter an amount"
        return None
    return value


# --- The page ---


def forecasts_view(page: ft.Page) -> ft.Control:
    inputs = load_inputs()
    income = {"value": ZERO}  # one income for the whole page

    chart_box = ft.Container()
    target_box = ft.Container()
    after_box = ft.Container()

    income_field = ft.TextField(
        label="Income a month", prefix="£", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, expand=1
    )
    target_field = ft.TextField(
        label="Target", prefix="£", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, expand=1
    )
    months_field = ft.TextField(
        label="Months from now",
        value=str(DEFAULT_MONTHS),
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        expand=1,
    )

    def months_wanted() -> int:
        try:
            return int((months_field.value or "").strip())
        except ValueError:
            return DEFAULT_MONTHS

    def draw_chart():
        f = forecast_for(inputs, income["value"])
        chart_box.content = _outlook_chart(
            build_outlook(inputs.today.year, inputs.figures, f, inputs.today), f, inputs, income["value"]
        )

    def draw_target():
        f = forecast_for(inputs, income["value"])
        target_box.content = _target_result(inputs.start, f, parse_money(target_field.value or ""))

    def draw_after():
        f = forecast_for(inputs, income["value"])
        after_box.content = _after_result(inputs.start, f, months_wanted())

    def on_income():
        value = _read_income(income_field)
        if value is not None:
            income["value"] = value
            draw_chart()
            draw_target()
            draw_after()
        page.update()

    def on_target():
        draw_target()
        page.update()

    def on_after():
        draw_after()
        page.update()

    income_field.on_change = on_income
    target_field.on_change = on_target
    months_field.on_change = on_after

    draw_chart()
    draw_target()
    draw_after()

    header = page_header("Looking ahead", theme.heading("Forecasts", size=30), [])
    cards = ft.Row(
        [
            _forecast_card("Reach a target", "How long until Left to spend gets to an amount.", target_field, target_box),
            _forecast_card("Where will I be", "Left to spend after a number of months.", months_field, after_box),
        ],
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
    return ft.Column(
        [
            header,
            ft.Column(
                [_income_card(income_field), chart_box, cards, ft.Container(height=8)],
                spacing=20,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        ],
        spacing=24,
        expand=True,
    )
