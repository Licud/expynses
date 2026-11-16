import flet as ft

from expynses.db import init_db
from expynses.ui.expense_list import expense_list
from expynses.ui.forms import expense_form


def main(page: ft.Page):
    page.title = "expynses"

    expenses, refresh = expense_list(page)
    form = expense_form(page, on_saved=refresh)

    page.add(
        ft.Row(
            [form, expenses],
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=40,
        )
    )


if __name__ == "__main__":
    init_db()
    ft.run(main)
