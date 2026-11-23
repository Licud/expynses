from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from expynses import __version__
from expynses.ui import theme
from expynses.ui.cash_flow_page import cash_flow_view
from expynses.ui.categories_page import categories_view
from expynses.ui.debit_page import debits_view
from expynses.ui.income_page import income_view
from expynses.ui.monthly import monthly_view
from expynses.ui.year_page import year_view


@dataclass(frozen=True)
class NavItem:
    label: str
    icon: ft.IconData
    # Builds the page's content each time it is opened, like a partial view.
    build: Callable[[ft.Page], ft.Control]


# Add a line here to add a page to the left-hand navigation.
NAV_ITEMS = [
    NavItem("Monthly", ft.Icons.CALENDAR_MONTH_OUTLINED, monthly_view),
    NavItem("Income", ft.Icons.SAVINGS_OUTLINED, income_view),
    NavItem("Debits", ft.Icons.EVENT_REPEAT_OUTLINED, debits_view),
    NavItem("Year", ft.Icons.CALENDAR_VIEW_MONTH_OUTLINED, year_view),
    NavItem("Cash flow", ft.Icons.COMPARE_ARROWS, cash_flow_view),
    NavItem("Categories", ft.Icons.DONUT_SMALL_OUTLINED, categories_view),
]


def _nav_button(item: NavItem, selected: bool, on_click: Callable[[], None]) -> ft.Control:
    """One navigation entry: a quiet row, softly filled when selected."""
    colour = theme.TEXT if selected else theme.MUTED
    row = ft.Container(
        on_click=lambda _: on_click(),
        height=38,
        border_radius=theme.RADIUS_SM,
        padding=ft.Padding.only(left=10, right=12),
        bgcolor=theme.SURFACE_HIGH if selected else None,
        content=ft.Row(
            [
                # A small accent bar marks the current page.
                ft.Container(
                    width=3,
                    height=16,
                    border_radius=2,
                    bgcolor=theme.ACCENT if selected else None,
                ),
                ft.Icon(item.icon, color=theme.ACCENT_TEXT if selected else colour, size=19),
                ft.Text(
                    item.label,
                    size=14,
                    weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                    color=colour,
                ),
            ],
            spacing=10,
        ),
    )
    return row if selected else theme.hoverable(row)


def app_shell(page: ft.Page) -> ft.Control:
    """Left-hand navigation plus a content area that swaps with the selection."""

    content = ft.Container(
        expand=True,
        padding=ft.Padding.only(left=32, right=32, top=28, bottom=24),
    )

    nav_items = ft.Column(spacing=2)

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
        padding=ft.Padding.only(left=6, top=26, bottom=30),
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED,
                        color=theme.ON_ACCENT,
                        size=16,
                    ),
                    width=28,
                    height=28,
                    alignment=ft.Alignment.CENTER,
                    border_radius=8,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=["#e39a7d", theme.ACCENT],
                    ),
                ),
                theme.heading("expynses", size=19),
            ],
            spacing=10,
        ),
    )

    menu_label = ft.Container(
        content=theme.label("Menu"),
        padding=ft.Padding.only(left=12, bottom=8),
    )

    version_label = ft.Container(
        padding=ft.Padding.only(top=12, bottom=16),
        content=ft.Row(
            [
                ft.Text(
                    f"expynses v{__version__}",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=theme.MUTED,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    nav_panel = ft.Container(
        width=216,
        padding=ft.Padding.symmetric(horizontal=12),
        # The expanding spacer pushes the version to the bottom of the panel.
        content=ft.Column(
            [logo, menu_label, nav_items, ft.Container(expand=True), version_label],
            spacing=0,
            expand=True,
        ),
        bgcolor=theme.BG,
        border=ft.Border(right=ft.BorderSide(1, theme.BORDER)),
    )

    show(0)

    return ft.Row(
        [nav_panel, content],
        expand=True,
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
    )
