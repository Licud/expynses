import decimal

from collections.abc import Callable, Sequence

import flet as ft

from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto
from expynses.services.expenses import search_expenses
from expynses.ui import theme
from expynses.ui.expense_type_icons import icon_for_type


def _pill(text: str, color: str) -> ft.Control:
    """A small rounded label with a tinted background."""
    return ft.Container(
        content=ft.Text(text, size=12, color=color, weight=ft.FontWeight.W_600),
        bgcolor=theme.tinted(color),
        border_radius=12,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )


def _type_cell(name: str) -> ft.Control:
    # One colour for every type, so the eye isn't pulled around the column.
    color = theme.ACCENT_TEXT
    return ft.Row(
        [
            ft.Container(
                content=ft.Icon(icon_for_type(name), size=18, color=color),
                bgcolor=theme.tinted(color),
                border_radius=8,
                padding=6,
            ),
            ft.Text(name),
        ],
        spacing=10,
    )


def _row(expense: ExpenseDto) -> ft.DataRow:
    payment = (
        _pill("Credit card", theme.GREEN)
        if expense.is_credit
        else _pill("Paid in full", theme.MUTED)
    )
    return ft.DataRow(
        cells=[
            ft.DataCell(ft.Text(expense.date.strftime("%d-%m-%Y"))),
            ft.DataCell(_type_cell(expense.expense_type.name)),
            ft.DataCell(
                ft.Text(
                    f"£{expense.price:.2f}",
                    color=theme.ACCENT_TEXT,
                    weight=ft.FontWeight.W_600,
                )
            ),
            ft.DataCell(payment),
            ft.DataCell(ft.Text(expense.notes)),
        ]
    )


def _stat_tile(icon: ft.IconData, caption: str, value: str, color: str) -> ft.Control:
    return ft.Container(
        expand=True,
        padding=16,
        border_radius=14,
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1, theme.BORDER),
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, color=color, size=22),
                    bgcolor=theme.tinted(color),
                    border_radius=10,
                    padding=10,
                ),
                ft.Column(
                    [
                        theme.label(caption),
                        ft.Text(value, size=22, weight=ft.FontWeight.W_600),
                    ],
                    spacing=2,
                ),
            ],
            spacing=14,
        ),
    )


def _stats(expenses: Sequence[ExpenseDto]) -> list[ft.Control]:
    zero = decimal.Decimal(0)
    total = sum((e.price for e in expenses), zero)
    on_credit = sum((e.price for e in expenses if e.is_credit), zero)
    paid_in_full = total - on_credit
    return [
        _stat_tile(ft.Icons.PAYMENTS, "Total spent", f"£{total:.2f}", theme.ACCENT_TEXT),
        _stat_tile(ft.Icons.CHECK_CIRCLE, "Paid in full", f"£{paid_in_full:.2f}", theme.GREEN),
        _stat_tile(ft.Icons.CREDIT_CARD, "On credit card", f"£{on_credit:.2f}", theme.AMBER),
        _stat_tile(ft.Icons.RECEIPT, "Entries", str(len(expenses)), theme.SLATE),
    ]


def expense_list(
    page: ft.Page, get_filter: Callable[[], ExpenseFilterDto]
) -> tuple[ft.Control, Callable[[], None]]:
    """The summary tiles and table of saved expenses, plus a refresh function.

    get_filter is asked for the filter every time the list loads, so the caller
    can change what is shown (e.g. the month) and then call refresh.
    """

    stats = ft.Row(spacing=16)
    table = ft.DataTable(
        columns=[
            ft.DataColumn(theme.label("Date")),
            ft.DataColumn(theme.label("Type")),
            ft.DataColumn(theme.label("Price")),
            ft.DataColumn(theme.label("Payment")),
            ft.DataColumn(theme.label("Notes")),
        ],
        heading_row_color=theme.SURFACE_HIGH,
        data_row_min_height=56,
        column_spacing=28,
        divider_thickness=0.5,
        expand=True,
    )

    empty_box = ft.Container(
        content=ft.Text("No expenses this month", color=theme.MUTED),
        padding=32,
        alignment=ft.Alignment.CENTER,
    )

    def load():
        expenses = list(search_expenses(get_filter()))
        stats.controls = _stats(expenses)
        table.rows = [_row(e) for e in expenses]
        table.visible = bool(expenses)
        empty_box.visible = not expenses

    def refresh():
        load()
        page.update()

    load()

    # Fills the page width.
    control = ft.Column(
        [
            stats,
            ft.Container(
                bgcolor=theme.SURFACE,
                border=ft.Border.all(1, theme.BORDER),
                border_radius=14,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Column([ft.Row([table]), empty_box]),
            ),
        ],
        expand=True,
        spacing=16,
    )
    return control, refresh
