"""Builders for showing expenses: the day-grouped transaction list and the
spend-by-category breakdown. They take already-loaded expenses; the page
decides when to load."""

import decimal

from collections.abc import Sequence
from itertools import groupby

import flet as ft

from expynses.contracts.expenses import ExpenseDto
from expynses.ui import theme
from expynses.ui.expense_type_icons import icon_for_type

ZERO = decimal.Decimal(0)


def _payment_tag(is_credit: bool) -> ft.Control:
    color = theme.AMBER if is_credit else theme.MUTED
    return ft.Row(
        [
            theme.dot(color, 6),
            ft.Text("Credit card" if is_credit else "Paid", size=12, color=theme.TEXT_SOFT if is_credit else theme.MUTED),
        ],
        spacing=6,
        tight=True,
    )


def _transaction_row(expense: ExpenseDto) -> ft.Control:
    name = expense.expense_type.name
    text_lines: list[ft.Control] = [
        ft.Text(name, size=14, weight=ft.FontWeight.W_500, color=theme.TEXT)
    ]
    if expense.notes:
        text_lines.append(
            ft.Text(
                expense.notes,
                size=12,
                color=theme.MUTED,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        )
    return theme.hoverable(
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=theme.RADIUS_SM,
            content=ft.Row(
                [
                    theme.icon_tile(icon_for_type(name), theme.ACCENT_TEXT),
                    ft.Column(text_lines, spacing=0, expand=True),
                    ft.Container(_payment_tag(expense.is_credit), width=110),
                    ft.Container(
                        ft.Text(
                            theme.money(expense.price),
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=theme.TEXT,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        width=100,
                        alignment=ft.Alignment.CENTER_RIGHT,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )


def _day_header(expenses: list[ExpenseDto]) -> ft.Control:
    day = expenses[0].date
    total = sum((e.price for e in expenses), ZERO)
    return ft.Container(
        padding=ft.Padding.only(left=12, right=12, top=14, bottom=4),
        content=ft.Row(
            [
                theme.label(day.strftime("%a %d %b")),
                ft.Container(expand=True),
                ft.Text(theme.money(total), size=12, color=theme.MUTED),
            ]
        ),
    )


def transactions_card(expenses: Sequence[ExpenseDto]) -> ft.Control:
    """Every expense, grouped under a header for each day, newest day first."""
    total = sum((e.price for e in expenses), ZERO)
    title = theme.card_title(
        "Transactions",
        ft.Row(
            [
                theme.badge(str(len(expenses))),
                ft.Text(theme.money(total), size=13, color=theme.MUTED),
            ],
            spacing=10,
        ),
    )

    if not expenses:
        body: ft.Control = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=theme.MUTED, size=28),
                    ft.Text("No expenses this month", color=theme.MUTED, size=13),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=40,
            alignment=ft.Alignment.CENTER,
        )
    else:
        rows: list[ft.Control] = []
        ordered = sorted(expenses, key=lambda e: e.date, reverse=True)
        for _, group in groupby(ordered, key=lambda e: e.date):
            day = list(group)
            rows.append(_day_header(day))
            rows += [_transaction_row(e) for e in day]
        body = ft.Column(rows, spacing=0)

    return theme.card(
        ft.Column(
            [ft.Container(title, padding=ft.Padding.symmetric(horizontal=12)), body],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding.only(left=8, right=8, top=18, bottom=10),
        expand=True,
    )


def category_card(expenses: Sequence[ExpenseDto]) -> ft.Control:
    """Spend per expense type, biggest first, each with a share-of-total bar."""
    totals: dict[str, decimal.Decimal] = {}
    for e in expenses:
        totals[e.expense_type.name] = totals.get(e.expense_type.name, ZERO) + e.price
    grand_total = sum(totals.values(), ZERO)

    rows: list[ft.Control] = []
    for name, amount in sorted(totals.items(), key=lambda kv: kv[1], reverse=True):
        share = float(amount / grand_total) if grand_total else 0.0
        rows.append(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon_for_type(name), size=16, color=theme.ACCENT_TEXT),
                            ft.Text(name, size=13, color=theme.TEXT, expand=True),
                            ft.Text(f"{share:.0%}", size=12, color=theme.MUTED),
                            ft.Text(
                                theme.money(amount),
                                size=13,
                                weight=ft.FontWeight.W_600,
                                width=76,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                        ],
                        spacing=10,
                    ),
                    theme.bar([(share, theme.ACCENT)], height=4),
                ],
                spacing=8,
            )
        )

    if not rows:
        rows = [ft.Text("Nothing spent yet", size=13, color=theme.MUTED)]

    return theme.card(
        ft.Column([theme.card_title("Where it went"), *rows], spacing=16)
    )
