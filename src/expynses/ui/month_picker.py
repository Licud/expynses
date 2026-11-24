import calendar
import datetime

from collections.abc import Callable

import flet as ft

from expynses.ui import theme


def open_month_picker(
    page: ft.Page,
    current: datetime.date,
    on_picked: Callable[[datetime.date], None],
) -> None:
    """A small dialog to jump to any month: step the year, then click a month.
    Clicking a month picks it straight away, with no OK button to confirm."""
    year = {"value": current.year}
    year_text = theme.heading(str(year["value"]), size=22)
    grid = ft.Column(spacing=6, tight=True)

    def close():
        dialog.open = False
        page.update()

    def pick(month: int):
        close()
        on_picked(datetime.date(year["value"], month, 1))

    def build_grid():
        year_text.value = str(year["value"])
        grid.controls = []
        for row_start in range(1, 13, 3):
            buttons = []
            for month in range(row_start, row_start + 3):
                selected = year["value"] == current.year and month == current.month
                buttons.append(
                    theme.hoverable(
                        ft.Container(
                            ft.Text(
                                calendar.month_abbr[month],
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=theme.ON_ACCENT if selected else theme.TEXT_SOFT,
                            ),
                            width=80,
                            height=40,
                            border_radius=theme.RADIUS_SM,
                            alignment=ft.Alignment.CENTER,
                            bgcolor=theme.ACCENT if selected else None,
                            on_click=lambda _, m=month: pick(m),
                        ),
                        theme.ACCENT if selected else theme.SURFACE_HOVER,
                    )
                )
            grid.controls.append(ft.Row(buttons, spacing=6, alignment=ft.MainAxisAlignment.CENTER))

    def shift_year(delta: int):
        year["value"] += delta
        build_grid()
        page.update()

    build_grid()
    dialog = ft.AlertDialog(
        bgcolor=theme.SURFACE,
        shape=ft.RoundedRectangleBorder(radius=16),
        content=ft.Column(
            [
                ft.Row(
                    [
                        theme.icon_button(ft.Icons.CHEVRON_LEFT, "Previous year", lambda: shift_year(-1)),
                        year_text,
                        theme.icon_button(ft.Icons.CHEVRON_RIGHT, "Next year", lambda: shift_year(1)),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                grid,
            ],
            spacing=14,
            tight=True,
            width=270,
        ),
    )
    page.show_dialog(dialog)
