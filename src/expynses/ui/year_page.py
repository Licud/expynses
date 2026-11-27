"""The 'Year' page: all twelve months side by side, plus the balance chart."""

import datetime

import flet as ft

from expynses.contracts.expenses import ExpenseDto
from expynses.ui import theme
from expynses.ui.charts import Bar, Group, bar_chart, legend
from expynses.ui.expense_type_icons import icon_for_type
from expynses.ui.report_widgets import (
    empty_state,
    net_color,
    page_header,
    period_switcher,
    signed_money,
    stat_tile,
)
from expynses.ui.reports_data import ZERO, MonthFigures, biggest_purchases, year_figures

ACCOUNT_COLOR = theme.SLATE
DEBT_COLOR = theme.AMBER
OUTGOING_COLOR = theme.ACCENT


def _stats(figures: list[MonthFigures]) -> ft.Control:
    started = [f for f in figures if not f.is_future]
    active = [f for f in started if f.has_activity]
    income = sum((f.income for f in figures), ZERO)
    outgoing = sum((f.outgoing for f in figures), ZERO)
    net = income - outgoing
    latest = started[-1] if started else None

    best = max(active, key=lambda f: f.net, default=None)
    worst = min(active, key=lambda f: f.net, default=None)
    net_note = None
    if best and worst and best is not worst:
        net_note = f"Best {best.start:%b} {signed_money(best.net)} · worst {worst.start:%b} {signed_money(worst.net)}"

    as_of = f"End of {latest.start:%B}" if latest else "No months yet"
    return ft.Row(
        [
            stat_tile(ft.Icons.ARROW_DOWNWARD, theme.GREEN, "Income", theme.money(income),
                      f"{theme.money(income / len(active)) if active else '£0.00'} a month on average"),
            stat_tile(ft.Icons.ARROW_UPWARD, OUTGOING_COLOR, "Outgoing", theme.money(outgoing),
                      f"{theme.money(outgoing / len(active)) if active else '£0.00'} a month on average"),
            stat_tile(ft.Icons.SAVINGS_OUTLINED, net_color(net), "Net", signed_money(net), net_note,
                      value_color=net_color(net)),
            stat_tile(ft.Icons.ACCOUNT_BALANCE_OUTLINED, ACCOUNT_COLOR, "Account",
                      theme.money(latest.balance) if latest and latest.balance is not None else "—", as_of),
            stat_tile(ft.Icons.CREDIT_CARD, DEBT_COLOR, "Card owed",
                      theme.money(latest.card_owed) if latest and latest.card_owed is not None else "—", as_of),
        ],
        spacing=14,
    )


def _chart(figures: list[MonthFigures], this_month: datetime.date) -> ft.Control:
    groups = []
    for f in figures:
        bars = []
        if not f.is_future:
            bars = [
                Bar.single(f.balance or ZERO, ACCOUNT_COLOR, "Account"),
                # Debt hangs below the line, like the old spreadsheet.
                Bar.single(-(f.card_owed or ZERO), DEBT_COLOR, "Card owed"),
                Bar.single(f.outgoing, OUTGOING_COLOR, "Outgoing"),
            ]
        groups.append(
            Group(
                label=f.start.strftime("%b"),
                bars=bars,
                faded=f.is_future,
                highlighted=f.start == this_month,
            )
        )
    return theme.card(
        ft.Column(
            [
                theme.card_title(
                    "Account, card debt & outgoing",
                    legend([(ACCOUNT_COLOR, "Account"), (DEBT_COLOR, "Card owed"), (OUTGOING_COLOR, "Outgoing")]),
                ),
                ft.Text("End-of-month balances. Hover a bar for the exact amount.", size=12, color=theme.MUTED),
                ft.Container(height=8),
                bar_chart(groups, height=300, bar_width=16),
            ],
            spacing=4,
        ),
        padding=ft.Padding.only(left=20, right=24, top=20, bottom=18),
    )


def _row(caption: str, value: str, color: str = theme.TEXT_SOFT) -> ft.Control:
    return ft.Row(
        [
            ft.Text(caption, size=12, color=theme.MUTED, expand=True),
            ft.Text(value, size=12, weight=ft.FontWeight.W_600, color=color),
        ],
    )


def _month_tile(f: MonthFigures, this_month: datetime.date) -> ft.Control:
    is_current = f.start == this_month
    title_row: list[ft.Control] = [
        ft.Text(f.start.strftime("%B"), size=14, weight=ft.FontWeight.W_600, color=theme.TEXT, expand=True)
    ]
    if is_current:
        title_row.append(theme.badge("Now", theme.ACCENT_TEXT))

    if f.is_future or not f.has_activity:
        body: list[ft.Control] = [
            ft.Container(height=6),
            ft.Text("Not started yet" if f.is_future else "Nothing recorded", size=13, color=theme.MUTED),
        ]
    else:
        scale = max(f.income, f.outgoing)
        used = float(f.outgoing / scale) if scale else 0.0
        body = [
            theme.heading(signed_money(f.net), size=22, color=net_color(f.net)),
            theme.bar([(used, OUTGOING_COLOR)], height=5),
            ft.Container(height=2),
            _row("In", theme.money(f.income), theme.GREEN if f.income else theme.MUTED),
            _row("Out", theme.money(f.outgoing)),
            _row("On the card", theme.money(f.on_credit), theme.AMBER if f.on_credit else theme.MUTED),
            ft.Divider(height=10, color=theme.BORDER),
            _row("Account", theme.money(f.balance or ZERO), theme.TEXT),
            _row("Card owed", theme.money(f.card_owed or ZERO), theme.AMBER if f.card_owed else theme.MUTED),
        ]

    return ft.Container(
        col={"xs": 12, "sm": 6, "md": 4, "xl": 3},
        padding=16,
        bgcolor=theme.SURFACE,
        border_radius=theme.RADIUS,
        border=ft.Border.all(1, theme.tinted(theme.ACCENT, 0.55) if is_current else theme.BORDER),
        opacity=0.5 if f.is_future or not f.has_activity else 1.0,
        content=ft.Column([ft.Row(title_row), *body], spacing=6),
    )


def _biggest_card(purchases: list[ExpenseDto]) -> ft.Control:
    """The year's most expensive single purchases, biggest first."""
    if not purchases:
        body: list[ft.Control] = [empty_state(ft.Icons.RECEIPT_LONG, "No purchases this year")]
    else:
        body = []
        for rank, e in enumerate(purchases, start=1):
            title = e.notes.strip() or e.expense_type.name
            right: list[ft.Control] = []
            if e.is_credit:
                right.append(theme.badge("Card", theme.AMBER))
            right.append(ft.Text(theme.money(e.price), size=14, weight=ft.FontWeight.W_600, color=theme.TEXT))
            body.append(
                ft.Row(
                    [
                        ft.Text(str(rank), size=12, color=theme.MUTED, width=20),
                        theme.icon_tile(icon_for_type(e.expense_type.name), theme.ACCENT_TEXT, size=30),
                        ft.Column(
                            [
                                ft.Text(title, size=13, color=theme.TEXT, no_wrap=True,
                                        overflow=ft.TextOverflow.ELLIPSIS, tooltip=title),
                                ft.Text(f"{e.date:%a %d %b} · {e.expense_type.name}", size=12, color=theme.MUTED),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        *right,
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
    return theme.card(
        ft.Column(
            [
                theme.card_title("Biggest purchases"),
                ft.Text("The single most expensive things bought this year, card or not.", size=12, color=theme.MUTED),
                ft.Container(height=6),
                *body,
            ],
            spacing=12,
        ),
        padding=ft.Padding.only(left=20, right=24, top=20, bottom=18),
    )


def year_view(page: ft.Page) -> ft.Control:
    today = datetime.date.today()
    this_month = today.replace(day=1)
    state = {"year": today.year}

    title = theme.heading("", size=30)
    stats_box = ft.Container()
    chart_box = ft.Container()
    biggest_box = ft.Container()
    tiles = ft.ResponsiveRow(spacing=14, run_spacing=14)

    def load():
        figures = year_figures(state["year"])
        title.value = str(state["year"])
        stats_box.content = _stats(figures)
        chart_box.content = _chart(figures, this_month)
        tiles.controls = [_month_tile(f, this_month) for f in figures]
        biggest_box.content = _biggest_card(biggest_purchases(state["year"]))

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
        "Year overview",
        title,
        [period_switcher(lambda: shift(-1), this_year, lambda: shift(1), "This year", unit="year")],
    )
    return ft.Column(
        [
            header,
            ft.Column(
                [stats_box, chart_box, theme.label("Month by month"), tiles, biggest_box, ft.Container(height=8)],
                spacing=20,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        ],
        spacing=24,
        expand=True,
    )
