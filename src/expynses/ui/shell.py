from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from expynses.ui import theme
from expynses.ui.monthly import monthly_view


@dataclass(frozen=True)
class NavItem:
    label: str
    icon: ft.IconData
    # Builds the page's content each time it is opened, like a partial view.
    build: Callable[[ft.Page], ft.Control]


# Add a line here to add a page to the left-hand navigation.
NAV_ITEMS = [
    NavItem("Monthly", ft.Icons.CALENDAR_MONTH, monthly_view),
]


def _nav_button(item: NavItem, selected: bool, on_click: Callable[[], None]) -> ft.Control:
    """One navigation entry: a raised, outlined pill when selected."""
    colour = theme.ACCENT_TEXT if selected else theme.MUTED
    return ft.Container(
        on_click=on_click,
        ink=True,
        border_radius=14,
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        bgcolor=theme.tinted(theme.ACCENT, 0.16) if selected else None,
        border=ft.Border.all(1, theme.tinted(theme.ACCENT, 0.55) if selected else theme.SURFACE),
        shadow=(
            ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color=theme.tinted(theme.ACCENT, 0.28),
                offset=ft.Offset(0, 5),
            )
            if selected
            else None
        ),
        content=ft.Row(
            [
                ft.Icon(item.icon, color=colour, size=26),
                ft.Text(
                    item.label,
                    size=18,
                    weight=ft.FontWeight.W_700 if selected else ft.FontWeight.W_500,
                    color=colour,
                    style=ft.TextStyle(letter_spacing=0.4),
                ),
            ],
            spacing=14,
        ),
    )


def app_shell(page: ft.Page) -> ft.Control:
    """Left-hand navigation plus a content area that swaps with the selection."""

    content = ft.Container(expand=True, padding=20)

    nav_items = ft.Column(spacing=8)

    def show(index: int):
        content.content = NAV_ITEMS[index].build(page)
        nav_items.controls = [
            _nav_button(item, selected=i == index, on_click=lambda i=i: select(i))
            for i, item in enumerate(NAV_ITEMS)
        ]

    def select(index: int):
        show(index)
        page.update()

    logo = ft.Container(
        padding=ft.Padding.only(left=8, top=24, bottom=28),
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.ACCOUNT_BALANCE_WALLET,
                        color=theme.ON_ACCENT,
                        size=22,
                    ),
                    padding=10,
                    border_radius=12,
                    bgcolor=theme.ACCENT,
                ),
                theme.heading("expynses", size=24),
            ],
            spacing=12,
        ),
    )

    # A solid panel with a hairline edge so the navigation reads as its own surface.
    nav_panel = ft.Container(
        width=240,
        padding=ft.Padding.symmetric(horizontal=16),
        content=ft.Column([logo, nav_items]),
        bgcolor=theme.SURFACE,
        border=ft.Border(right=ft.BorderSide(1, theme.BORDER)),
    )

    show(0)

    return ft.Row(
        [nav_panel, content],
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
