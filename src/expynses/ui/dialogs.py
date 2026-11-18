import datetime

from collections.abc import Callable

import flet as ft

from expynses.ui import theme


def open_add_dialog(
    page: ft.Page,
    title: str,
    build_form: Callable[..., ft.Control],
    on_saved: Callable[[], None],
    default_date: datetime.date | None = None,
) -> None:
    """Show a form in a dialog. The dialog closes after a save unless the form's
    "add another" switch is on; on_saved runs after every save."""

    def close():
        dialog.open = False
        page.update()

    def saved(add_another: bool):
        if not add_another:
            close()
        on_saved()

    dialog = ft.AlertDialog(
        bgcolor=theme.SURFACE,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(
            [
                theme.heading(title, size=24),
                ft.IconButton(
                    ft.Icons.CLOSE,
                    icon_color=theme.MUTED,
                    tooltip="Close",
                    on_click=close,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        content=build_form(page, on_saved=saved, default_date=default_date),
    )
    page.show_dialog(dialog)
