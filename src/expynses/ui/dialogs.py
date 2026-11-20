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
                theme.heading(title, size=21),
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


def confirm_delete(
    page: ft.Page,
    message: str,
    on_confirm: Callable[[], None],
    title: str = "Delete?",
    warning: str | None = None,
    confirm_text: str = "Delete",
) -> None:
    """Ask before deleting; on_confirm runs only if the user agrees.

    A warning, when given, shows in a red box under the message for deletes
    that reach further than the item itself.
    """

    def close():
        dialog.open = False
        page.update()

    def confirmed():
        close()
        on_confirm()

    body: list[ft.Control] = [ft.Text(message, color=theme.TEXT_SOFT)]
    if warning:
        body.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                border_radius=theme.RADIUS_SM,
                bgcolor=theme.tinted(theme.RED, 0.10),
                border=ft.Border.all(1, theme.tinted(theme.RED, 0.35)),
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=theme.RED, size=20),
                        ft.Text(warning, size=13, color=theme.TEXT, expand=True),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            )
        )

    dialog = ft.AlertDialog(
        bgcolor=theme.SURFACE,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=theme.heading(title, size=21),
        content=ft.Column(body, spacing=14, tight=True, width=380),
        actions=[
            ft.TextButton("Cancel", on_click=close),
            ft.TextButton(confirm_text, on_click=confirmed, style=ft.ButtonStyle(color=theme.RED)),
        ],
    )
    page.show_dialog(dialog)
