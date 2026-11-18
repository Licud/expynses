import flet as ft

from expynses.contracts.incomes import IncomeFilterDto
from expynses.ui import theme
from expynses.ui.dialogs import open_add_dialog
from expynses.ui.forms import income_form
from expynses.ui.income_list import income_list


def income_view(page: ft.Page) -> ft.Control:
    """The 'Income' page: every recorded income, newest first."""
    incomes, refresh = income_list(
        page, lambda: IncomeFilterDto(), total_caption="Total income, all time"
    )

    header = ft.Row(
        [
            theme.heading("Income", size=34),
            ft.Container(expand=True),
            theme.action_button(
                "Add income",
                ft.Icons.ADD,
                lambda: open_add_dialog(page, "Add income", income_form, on_saved=refresh),
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    return ft.Column([header, incomes], spacing=20, expand=True)
