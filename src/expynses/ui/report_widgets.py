"""Pieces shared by the report pages: the header, period switcher and stat tiles."""

import decimal

from collections.abc import Callable

import flet as ft

from expynses.ui import theme


def period_switcher(
    on_previous: Callable[[], None],
    on_today: Callable[[], None],
    on_next: Callable[[], None],
    today_text: str = "Today",
    unit: str = "month",
) -> ft.Control:
    """previous | Today | next, styled like the Monthly page's switcher."""
    divider = ft.Container(width=1, height=18, bgcolor=theme.BORDER)
    return ft.Container(
        height=theme.CONTROL_HEIGHT,
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1, theme.BORDER),
        border_radius=theme.RADIUS_SM,
        padding=2,
        content=ft.Row(
            [
                theme.icon_button(ft.Icons.CHEVRON_LEFT, f"Previous {unit}", on_previous, size=30),
                divider,
                theme.hoverable(
                    ft.Container(
                        ft.Text(today_text, size=13, weight=ft.FontWeight.W_600, color=theme.TEXT_SOFT),
                        padding=ft.Padding.symmetric(horizontal=12),
                        height=30,
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda _: on_today(),
                    ),
                    theme.SURFACE_HOVER,
                ),
                divider,
                theme.icon_button(ft.Icons.CHEVRON_RIGHT, f"Next {unit}", on_next, size=30),
            ],
            spacing=2,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def segmented(options: list[str], selected: str, on_select: Callable[[str], None]) -> ft.Control:
    """A small pill group for picking one option (e.g. 3 / 6 / 12 months)."""
    buttons = []
    for option in options:
        active = option == selected
        button = ft.Container(
            ft.Text(
                option,
                size=13,
                weight=ft.FontWeight.W_600,
                color=theme.ON_ACCENT if active else theme.TEXT_SOFT,
            ),
            padding=ft.Padding.symmetric(horizontal=12),
            height=30,
            border_radius=8,
            alignment=ft.Alignment.CENTER,
            bgcolor=theme.ACCENT if active else None,
            on_click=None if active else (lambda _, o=option: on_select(o)),
        )
        buttons.append(button if active else theme.hoverable(button, theme.SURFACE_HOVER))
    return ft.Container(
        height=theme.CONTROL_HEIGHT,
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1, theme.BORDER),
        border_radius=theme.RADIUS_SM,
        padding=2,
        content=ft.Row(buttons, spacing=2, tight=True),
    )


def page_header(caption: str, title: ft.Control, controls: list[ft.Control]) -> ft.Control:
    return ft.Row(
        [
            ft.Column([theme.label(caption), title], spacing=2),
            ft.Container(expand=True),
            *controls,
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )


def stat_tile(
    icon: ft.IconData,
    color: str,
    caption: str,
    value: str,
    note: str | None = None,
    value_color: str = theme.TEXT,
) -> ft.Control:
    """A headline number on its own small card."""
    return theme.card(
        ft.Column(
            [
                ft.Row(
                    [theme.icon_tile(icon, color, size=28), theme.label(caption)],
                    spacing=10,
                ),
                theme.heading(value, size=24, color=value_color),
                ft.Text(note or "", size=12, color=theme.MUTED, max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS, tooltip=note),
            ],
            spacing=8,
        ),
        padding=18,
        expand=1,
    )


def signed_money(amount: decimal.Decimal) -> str:
    """Money with an explicit + for gains, so net figures read at a glance."""
    return ("+" if amount > 0 else "") + theme.money(amount)


def net_color(amount: decimal.Decimal) -> str:
    if amount > 0:
        return theme.GREEN
    if amount < 0:
        return theme.RED
    return theme.MUTED


def empty_state(icon: ft.IconData, text: str) -> ft.Control:
    return ft.Container(
        padding=40,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [ft.Icon(icon, color=theme.MUTED, size=30), ft.Text(text, size=13, color=theme.MUTED)],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
