import flet as ft

from expynses.ui.forms import expense_form


def main(page: ft.Page):
    page.title = "expynses"
    page.add(expense_form(page))


if __name__ == "__main__":
    ft.run(main)
