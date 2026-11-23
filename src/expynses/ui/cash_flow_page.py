"""The 'Cash flow' page: income against outgoing, month by month."""

import datetime
import decimal

import flet as ft

from expynses.ui import theme
from expynses.ui.charts import Bar, Group, Segment, bar_chart, legend
from expynses.ui.report_widgets import (
    net_color,
    page_header,
    period_switcher,
    signed_money,
    stat_tile,
)
from expynses.ui.reports_data import ZERO, MonthFigures, year_figures

INCOME_COLOR = theme.GREEN
PAID_COLOR = theme.ACCENT
DEBITS_COLOR = theme.MAUVE
CARD_COLOR = theme.SLATE


def _kept(f_income: decimal.Decimal, f_net: decimal.Decimal) -> str:
    """The share of income kept, e.g. '23%'; a dash when there was no income."""
    return f"{f_net / f_income:.0%}" if f_income else "—"


# SERVICE CANDIDATE: running net is a cumulative sum over monthly_figures; trivial,
# but if a service returns monthly figures it could return this too.
def _running(figures: list[MonthFigures]) -> list[decimal.Decimal]:
    total = ZERO
    out = []
    for f in figures:
        total += f.net
        out.append(total)
    return out


def _stats(figures: list[MonthFigures]) -> ft.Control:
    started = [f for f in figures if not f.is_future]
    income = sum((f.income for f in figures), ZERO)
    paid = sum((f.paid for f in figures), ZERO)
    debits = sum((f.debits for f in figures), ZERO)
    card = sum((f.card_repaid for f in figures), ZERO)
    outgoing = paid + debits + card
    net = income - outgoing
    active = [f for f in started if f.has_activity]
    in_the_green = sum(1 for f in active if f.net > 0)

    def share(part: decimal.Decimal) -> str:
        return f"{part / outgoing:.0%}" if outgoing else "0%"

    return ft.Row(
        [
            stat_tile(ft.Icons.ARROW_DOWNWARD, INCOME_COLOR, "Money in", theme.money(income)),
            stat_tile(ft.Icons.ARROW_UPWARD, PAID_COLOR, "Money out", theme.money(outgoing),
                      f"{share(paid)} spending · {share(debits)} debits · {share(card)} card"),
            stat_tile(ft.Icons.SAVINGS_OUTLINED, net_color(net), "Kept", signed_money(net),
                      f"{_kept(income, net)} of what came in", value_color=net_color(net)),
            stat_tile(ft.Icons.TRENDING_UP, theme.AMBER, "Months in the green",
                      f"{in_the_green} of {len(active)}",
                      "Months where more came in than went out"),
        ],
        spacing=14,
    )


def _flow_chart(figures: list[MonthFigures], this_month: datetime.date) -> ft.Control:
    groups = []
    for f in figures:
        bars = []
        if not f.is_future:
            bars = [
                Bar.single(f.income, INCOME_COLOR, "Income"),
                Bar(
                    [
                        Segment(f.paid, PAID_COLOR, "Spending"),
                        Segment(f.debits, DEBITS_COLOR, "Debits"),
                        Segment(f.card_repaid, CARD_COLOR, "Card repayments"),
                    ]
                ),
            ]
        footer = (
            ft.Text(signed_money(f.net), size=11, weight=ft.FontWeight.W_600, color=net_color(f.net))
            if not f.is_future
            else None
        )
        groups.append(
            Group(
                label=f.start.strftime("%b"),
                bars=bars,
                faded=f.is_future,
                highlighted=f.start == this_month,
                footer=footer,
            )
        )
    return theme.card(
        ft.Column(
            [
                theme.card_title(
                    "Income vs outgoing",
                    legend(
                        [
                            (INCOME_COLOR, "Income"),
                            (PAID_COLOR, "Spending"),
                            (DEBITS_COLOR, "Debits"),
                            (CARD_COLOR, "Card repayments"),
                        ]
                    ),
                ),
                ft.Text(
                    "Outgoing is what left the account: card spending counts when it's repaid. "
                    "The figure under each month is what was kept.",
                    size=12,
                    color=theme.MUTED,
                ),
                ft.Container(height=8),
                bar_chart(groups, height=300, bar_width=22, bar_gap=4),
            ],
            spacing=4,
        ),
        padding=ft.Padding.only(left=20, right=24, top=20, bottom=18),
    )


def _running_chart(figures: list[MonthFigures], this_month: datetime.date) -> ft.Control:
    running = _running(figures)
    groups = [
        Group(
            label=f.start.strftime("%b"),
            bars=[] if f.is_future else [Bar.single(r, net_color(r), "Kept so far")],
            faded=f.is_future,
            highlighted=f.start == this_month,
        )
        for f, r in zip(figures, running)
    ]
    return theme.card(
        ft.Column(
            [
                theme.card_title("Kept so far this year"),
                ft.Text("Each month's net, added up from January.", size=12, color=theme.MUTED),
                ft.Container(height=8),
                bar_chart(groups, height=140, bar_width=26),
            ],
            spacing=4,
        ),
        padding=ft.Padding.only(left=20, right=24, top=20, bottom=18),
    )


def _table(figures: list[MonthFigures]) -> ft.Control:
    def cell(text: str, color: str = theme.TEXT_SOFT, bold: bool = False) -> ft.DataCell:
        return ft.DataCell(
            ft.Text(text, size=13, color=color, weight=ft.FontWeight.W_600 if bold else ft.FontWeight.W_400)
        )

    def header(text: str) -> ft.DataColumn:
        return ft.DataColumn(ft.Text(text.upper(), style=theme.label_style()), numeric=text != "Month")

    rows = []
    for f, running in zip(figures, _running(figures)):
        if f.is_future or not f.has_activity:
            continue
        rows.append(
            ft.DataRow(
                cells=[
                    cell(f.start.strftime("%B"), theme.TEXT),
                    cell(theme.money(f.income), theme.GREEN if f.income else theme.MUTED),
                    cell(theme.money(f.paid)),
                    cell(theme.money(f.debits)),
                    cell(theme.money(f.card_repaid)),
                    cell(signed_money(f.net), net_color(f.net), bold=True),
                    cell(_kept(f.income, f.net), theme.MUTED),
                    cell(signed_money(running), net_color(running)),
                ]
            )
        )
    table = ft.DataTable(
        columns=[
            header("Month"),
            header("In"),
            header("Spending"),
            header("Debits"),
            header("Card"),
            header("Net"),
            header("Kept"),
            header("So far"),
        ],
        rows=rows,
        heading_row_height=36,
        data_row_min_height=36,
        data_row_max_height=36,
        column_spacing=24,
        divider_thickness=0.5,
        horizontal_lines=ft.BorderSide(1, theme.BORDER),
    )
    return theme.card(
        ft.Column([theme.card_title("Month by month"), ft.Row([table], scroll=ft.ScrollMode.AUTO)], spacing=8),
    )


def cash_flow_view(page: ft.Page) -> ft.Control:
    today = datetime.date.today()
    this_month = today.replace(day=1)
    state = {"year": today.year}

    title = theme.heading("", size=30)
    body = ft.Column(spacing=20, expand=True, scroll=ft.ScrollMode.AUTO)

    def load():
        figures = year_figures(state["year"])
        title.value = str(state["year"])
        body.controls = [
            _stats(figures),
            _flow_chart(figures, this_month),
            _running_chart(figures, this_month),
            _table(figures),
            ft.Container(height=8),
        ]

    def shift(delta: int):
        state["year"] += delta
        load()
        page.update()

    def this_year():
        state["year"] = today.year
        load()
        page.update()

    load()

    header = page_header(
        "Income vs outgoing",
        title,
        [period_switcher(lambda: shift(-1), this_year, lambda: shift(1), "This year", unit="year")],
    )
    return ft.Column([header, body], spacing=24, expand=True)
