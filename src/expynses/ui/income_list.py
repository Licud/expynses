"""Builder for the income list card. It takes already-loaded incomes; the page
decides when to load."""

import decimal

from collections.abc import Sequence
from itertools import groupby

import flet as ft

from expynses.contracts.incomes import IncomeDto
from expynses.ui import theme


def _delete_button() -> ft.Control:
    # Not wired up yet: there is no delete in the backend.
    return theme.icon_button(ft.Icons.DELETE_OUTLINE, "Delete", lambda: None, size=28)


def _row(income: IncomeDto, show_date: bool) -> ft.Control:
    lines: list[ft.Control] = [
        ft.Text(
            income.source,
            size=14,
            weight=ft.FontWeight.W_500,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
    ]
    if show_date:
        lines.append(ft.Text(income.date.strftime("%a %d %b"), size=12, color=theme.MUTED))
    return theme.hoverable(
        ft.Container(
            padding=ft.Padding.only(left=12, right=6, top=8, bottom=8),
            border_radius=theme.RADIUS_SM,
            content=ft.Row(
                [
                    theme.icon_tile(ft.Icons.ARROW_DOWNWARD, theme.GREEN, size=30),
                    ft.Column(lines, spacing=0, expand=True),
                    ft.Text(
                        "+" + theme.money(income.amount),
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=theme.GREEN,
                    ),
                    _delete_button(),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )


def income_card(
    incomes: Sequence[IncomeDto],
    title: str = "Income",
    empty_text: str = "No income recorded",
    show_date: bool = True,
) -> ft.Control:
    """A card listing incomes, with their total next to the title."""
    total = sum((i.amount for i in incomes), decimal.Decimal(0))
    header = ft.Container(
        theme.card_title(
            title, ft.Text(theme.money(total), size=13, weight=ft.FontWeight.W_600, color=theme.GREEN)
        ),
        padding=ft.Padding.only(left=12, right=12, bottom=6),
    )
    if incomes:
        rows: list[ft.Control] = [_row(i, show_date) for i in incomes]
    else:
        rows = [
            ft.Container(
                ft.Text(empty_text, size=13, color=theme.MUTED),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        ]
    return theme.card(
        ft.Column([header, *rows], spacing=0),
        padding=ft.Padding.only(left=8, right=8, top=18, bottom=10),
    )


def _month_header(incomes: list[IncomeDto]) -> ft.Control:
    total = sum((i.amount for i in incomes), decimal.Decimal(0))
    return ft.Container(
        padding=ft.Padding.only(left=12, right=12, top=14, bottom=4),
        content=ft.Row(
            [
                theme.label(incomes[0].date.strftime("%B %Y")),
                ft.Container(expand=True),
                ft.Text(theme.money(total), size=12, color=theme.MUTED),
            ]
        ),
    )


def income_by_month_card(incomes: Sequence[IncomeDto], title: str = "All income") -> ft.Control:
    """Every income, newest first, under a header and total for each month."""
    total = sum((i.amount for i in incomes), decimal.Decimal(0))
    header = ft.Container(
        theme.card_title(
            title,
            ft.Row(
                [
                    theme.badge(str(len(incomes))),
                    ft.Text(theme.money(total), size=13, weight=ft.FontWeight.W_600, color=theme.GREEN),
                ],
                spacing=10,
            ),
        ),
        padding=ft.Padding.symmetric(horizontal=12),
    )

    rows: list[ft.Control] = []
    ordered = sorted(incomes, key=lambda i: i.date, reverse=True)
    for _, group in groupby(ordered, key=lambda i: (i.date.year, i.date.month)):
        month = list(group)
        rows.append(_month_header(month))
        rows += [_row(i, show_date=True) for i in month]
    if not rows:
        rows = [
            ft.Container(
                ft.Text("No income recorded", size=13, color=theme.MUTED),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        ]

    return theme.card(
        ft.Column([header, *rows], spacing=0),
        padding=ft.Padding.only(left=8, right=8, top=18, bottom=10),
    )
