import decimal

from collections.abc import Callable, Sequence

import flet as ft

from expynses.contracts.incomes import IncomeDto, IncomeFilterDto
from expynses.services.incomes import search_incomes
from expynses.ui import theme


def _delete_button() -> ft.Control:
    # Not wired up yet: there is no delete in the backend.
    return ft.IconButton(
        ft.Icons.DELETE_OUTLINE,
        icon_color=theme.MUTED,
        icon_size=20,
        tooltip="Delete",
        on_click=lambda: None,
    )


def _row(income: IncomeDto, show_date: bool) -> ft.DataRow:
    cells = []
    if show_date:
        cells.append(ft.DataCell(ft.Text(income.date.strftime("%d-%m-%Y"))))
    cells += [
        ft.DataCell(ft.Text(income.source)),
        ft.DataCell(
            ft.Text(
                f"£{income.amount:,.2f}",
                color=theme.GREEN,
                weight=ft.FontWeight.W_600,
            )
        ),
        ft.DataCell(_delete_button()),
    ]
    return ft.DataRow(cells=cells)


def _total_tile(incomes: Sequence[IncomeDto], caption: str) -> ft.Control:
    total = sum((i.amount for i in incomes), decimal.Decimal(0))
    return ft.Container(
        padding=16,
        border_radius=14,
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1, theme.BORDER),
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.SAVINGS, color=theme.GREEN, size=22),
                    bgcolor=theme.tinted(theme.GREEN),
                    border_radius=10,
                    padding=10,
                ),
                ft.Column(
                    [
                        theme.label(caption),
                        ft.Text(f"£{total:,.2f}", size=22, weight=ft.FontWeight.W_600),
                    ],
                    spacing=2,
                ),
            ],
            spacing=14,
        ),
    )


def income_list(
    page: ft.Page,
    get_filter: Callable[[], IncomeFilterDto],
    empty_text: str = "No income recorded",
    total_caption: str = "Total income",
    show_date: bool = True,
) -> tuple[ft.Control, Callable[[], None]]:
    """A total tile and table of recorded income, plus a refresh function."""

    total_box = ft.Container()
    table = ft.DataTable(
        columns=(
            ([ft.DataColumn(theme.label("Date"))] if show_date else [])
            + [
                ft.DataColumn(theme.label("Source")),
                ft.DataColumn(theme.label("Amount")),
                ft.DataColumn(ft.Text("")),
            ]
        ),
        heading_row_color=theme.SURFACE_HIGH,
        data_row_min_height=56,
        column_spacing=24,
        divider_thickness=0.5,
        expand=True,
    )
    empty_box = ft.Container(
        content=ft.Text(empty_text, color=theme.MUTED),
        padding=32,
        alignment=ft.Alignment.CENTER,
    )

    def load():
        incomes = list(search_incomes(get_filter()))
        total_box.content = _total_tile(incomes, total_caption)
        table.rows = [_row(i, show_date) for i in incomes]
        table.visible = bool(incomes)
        empty_box.visible = not incomes

    def refresh():
        load()
        page.update()

    load()

    control = ft.Column(
        [
            total_box,
            ft.Container(
                bgcolor=theme.SURFACE,
                border=ft.Border.all(1, theme.BORDER),
                border_radius=14,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Column([ft.Row([table]), empty_box]),
            ),
        ],
        expand=True,
        spacing=16,
    )
    return control, refresh
