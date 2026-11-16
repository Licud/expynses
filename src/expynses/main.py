import flet as ft

from expynses.db import init_db
from expynses.ui.forms import expense_form


def main(page: ft.Page):
    page.title = "expynses"
    page.add(expense_form(page))


if __name__ == "__main__":
    init_db()
    ft.run(main)
