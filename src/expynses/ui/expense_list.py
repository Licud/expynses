from collections.abc import Callable

import flet as ft

from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto
from expynses.services.expenses import search_expenses


def _row(expense: ExpenseDto) -> ft.DataRow:
    return ft.DataRow(
        cells=[
            ft.DataCell(ft.Text(expense.date.strftime("%d-%m-%Y"))),
            ft.DataCell(ft.Text(expense.expense_type.name)),
            ft.DataCell(ft.Text(f"£{expense.price:.2f}")),
            ft.DataCell(ft.Text("Credit card" if expense.is_credit else "Paid in full")),
            ft.DataCell(ft.Text(expense.notes)),
        ]
    )


def _rows() -> list[ft.DataRow]:
    # An empty filter matches everything, newest first.
    return [_row(e) for e in search_expenses(ExpenseFilterDto())]


def expense_list(page: ft.Page) -> tuple[ft.Control, Callable[[], None]]:
    """The table of saved expenses. Returns the control and a refresh function."""

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Type")),
            ft.DataColumn(ft.Text("Price")),
            ft.DataColumn(ft.Text("Payment")),
            ft.DataColumn(ft.Text("Notes")),
        ],
        rows=_rows(),
    )

    def refresh():
        table.rows = _rows()
        page.update()

    # The Column scrolls on its own once the table gets long.
    return ft.Column([ft.Text("Expenses", size=24), table], scroll=ft.ScrollMode.AUTO), refresh
