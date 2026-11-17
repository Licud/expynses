import calendar
import datetime

import flet as ft

from expynses.contracts.expenses import ExpenseFilterDto
from expynses.ui.expense_list import expense_list
from expynses.ui import theme
from expynses.ui.forms import expense_form


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

    expenses, refresh = expense_list(page, month_filter)

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

    def open_add_expense():
        def close():
            dialog.open = False
            page.update()

        def saved(add_another: bool):
            if not add_another:
                close()
            refresh()

        # Add to the month on screen: today if it's the current month.
        default = today if month["start"] == this_month else month["start"]
        dialog = ft.AlertDialog(
            bgcolor=theme.SURFACE,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                [
                    theme.heading("Add expense", size=24),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        icon_color=theme.MUTED,
                        tooltip="Close",
                        on_click=close,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=expense_form(page, on_saved=saved, default_date=default),
        )
        page.show_dialog(dialog)

    show_month(this_month)

    month_picker = ft.Container(
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1, theme.BORDER),
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
            ft.TextButton("This month", on_click=go_to_this_month, style=ft.ButtonStyle(color=theme.ACCENT_TEXT)),
            ft.FilledButton(
                "Add expense",
                icon=ft.Icons.ADD,
                on_click=open_add_expense,
                height=44,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Column([header, expenses], spacing=20, expand=True)
