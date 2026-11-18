import datetime
import decimal

from collections.abc import Sequence

import flet as ft

from expynses.contracts.incomes import IncomeDto, IncomeFilterDto
from expynses.services.incomes import search_incomes
from expynses.ui import theme
from expynses.ui.dialogs import open_add_dialog
from expynses.ui.forms import income_form
from expynses.ui.income_list import income_by_month_card

ZERO = decimal.Decimal(0)
AVERAGE_MONTHS = 12


def _first_of_month_ago(today: datetime.date, months: int) -> datetime.date:
    """The first day of the month `months - 1` months before this one."""
    index = today.year * 12 + today.month - 1 - (months - 1)
    return datetime.date(index // 12, index % 12 + 1, 1)


def _stat(caption: str, value: str, detail: str | None = None) -> ft.Control:
    lines: list[ft.Control] = [
        theme.label(caption),
        ft.Text(value, size=18, weight=ft.FontWeight.W_600, color=theme.TEXT),
    ]
    if detail:
        lines.append(ft.Text(detail, size=12, color=theme.MUTED))
    return ft.Column(lines, spacing=3, expand=True)


def _divider() -> ft.Control:
    return ft.Container(width=1, height=56, bgcolor=theme.BORDER)


def _summary(incomes: Sequence[IncomeDto], today: datetime.date) -> ft.Control:
    """The headline total and a few supporting figures, side by side."""
    all_time = sum((i.amount for i in incomes), ZERO)
    this_year = sum((i.amount for i in incomes if i.date.year == today.year), ZERO)
    window_start = _first_of_month_ago(today, AVERAGE_MONTHS)
    recent = sum((i.amount for i in incomes if i.date >= window_start), ZERO)
    latest = max(incomes, key=lambda i: i.date, default=None)

    headline = ft.Column(
        [theme.label("All-time income"), theme.heading(theme.money(all_time), size=40)],
        spacing=4,
        expand=2,
    )

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=28, vertical=22),
        border_radius=theme.RADIUS,
        border=ft.Border.all(1, theme.BORDER),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[theme.tinted(theme.GREEN, 0.06), theme.SURFACE, theme.SURFACE],
            stops=[0.0, 0.4, 1.0],
        ),
        content=ft.Row(
            [
                headline,
                _divider(),
                _stat(f"{today.year} so far", theme.money(this_year)),
                _divider(),
                _stat("Monthly avg", theme.money(recent / AVERAGE_MONTHS), "last 12 months"),
                _divider(),
                _stat(
                    "Last payment",
                    theme.money(latest.amount) if latest else "—",
                    f"{latest.source} · {latest.date.strftime('%d %b %Y')}" if latest else None,
                ),
            ],
            spacing=28,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def income_view(page: ft.Page) -> ft.Control:
    """The 'Income' page: headline totals and every recorded income grouped by month."""
    summary_box = ft.Container()
    list_box = ft.Container()

    def load():
        incomes = list(search_incomes(IncomeFilterDto()))
        summary_box.content = _summary(incomes, datetime.date.today())
        list_box.content = income_by_month_card(incomes)

    def refresh():
        load()
        page.update()

    load()

    header = ft.Row(
        [
            ft.Column([theme.label("History"), theme.heading("Income", size=30)], spacing=2),
            ft.Container(expand=True),
            theme.action_button(
                "Income",
                ft.Icons.ADD,
                lambda: open_add_dialog(page, "Add income", income_form, on_saved=refresh),
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.END,
    )
    return ft.Column(
        [
            header,
            ft.Column([summary_box, list_box], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True),
        ],
        spacing=24,
        expand=True,
    )
