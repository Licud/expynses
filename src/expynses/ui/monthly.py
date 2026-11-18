import calendar
import datetime

import flet as ft

from expynses.contracts.expenses import ExpenseFilterDto
from expynses.contracts.incomes import IncomeFilterDto
from expynses.ui.dialogs import open_add_dialog
from expynses.ui.expense_list import expense_list
from expynses.ui.income_list import income_list
from expynses.ui import theme
from expynses.ui.forms import expense_form, income_form


def monthly_view(page: ft.Page) -> ft.Control:
    """The 'Monthly' page: pick a month, see its expenses, add a new one."""
    today = datetime.date.today()
    this_month = today.replace(day=1)

    # The first day of the month being shown.
    month = {"start": this_month}

    month_label = ft.Text(size=18, font_family=theme.HEADING_FONT)

    def month_filter() -> ExpenseFilterDto:
        start = month["start"]
        last_day = calendar.monthrange(start.year, start.month)[1]
        return ExpenseFilterDto(from_date=start, to_date=start.replace(day=last_day))

    def income_month_filter() -> IncomeFilterDto:
        f = month_filter()
        return IncomeFilterDto(from_date=f.from_date, to_date=f.to_date)

    expenses, refresh_expenses = expense_list(page, month_filter)
    incomes, refresh_incomes = income_list(
        page,
        income_month_filter,
        empty_text="No income this month",
        total_caption="Income this month",
        show_date=False,
    )

    def refresh():
        refresh_expenses()
        refresh_incomes()

    def show_month(start: datetime.date):
        month["start"] = start
        month_label.value = start.strftime("%B %Y")

    def shift_month(delta: int):
        start = month["start"]
        index = start.year * 12 + (start.month - 1) + delta
        show_month(datetime.date(index // 12, index % 12 + 1, 1))
        refresh()

    def go_to_this_month():
        show_month(this_month)
        refresh()

    def add_dialog(title: str, build_form):
        # Add to the month on screen: today if it's the current month.
        default = today if month["start"] == this_month else month["start"]
        open_add_dialog(page, title, build_form, on_saved=refresh, default_date=default)

    def open_add_expense():
        add_dialog("Add expense", expense_form)

    def open_add_income():
        add_dialog("Add income", income_form)

    show_month(this_month)

    month_picker = ft.Container(
        height=44,
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1.5, theme.BORDER),
        border_radius=24,
        padding=ft.Padding.symmetric(horizontal=4),
        content=ft.Row(
            [
                ft.IconButton(
                    ft.Icons.CHEVRON_LEFT,
                    icon_color=theme.MUTED,
                    tooltip="Previous month",
                    on_click=lambda: shift_month(-1),
                ),
                ft.Container(content=month_label, width=170, alignment=ft.Alignment.CENTER),
                ft.IconButton(
                    ft.Icons.CHEVRON_RIGHT,
                    icon_color=theme.MUTED,
                    tooltip="Next month",
                    on_click=lambda: shift_month(1),
                ),
            ],
            spacing=0,
        ),
    )

    header = ft.Row(
        [
            theme.heading("Monthly", size=34),
            ft.Container(expand=True),
            month_picker,
            theme.action_button("This month", ft.Icons.TODAY, go_to_this_month, filled=False, quiet=True),
            theme.action_button("Add income", ft.Icons.ADD, open_add_income),
            theme.action_button("Add expense", ft.Icons.ADD, open_add_expense),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    body = ft.Row(
        [
            ft.Container(incomes, width=380),
            ft.Container(expenses, expand=True),
        ],
        spacing=20,
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
    return ft.Column([header, body], spacing=20, expand=True)
