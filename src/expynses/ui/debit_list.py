"""Builder for the ticked-off debits card on the Monthly page. It takes the
month's debits already loaded; the page decides what happens on untick."""

import decimal

from collections.abc import Callable, Sequence

import flet as ft

from expynses.ui import theme
from expynses.ui.debit_month_dialog import MonthDebit
from expynses.ui.debit_page import schedule_text


def _row(debit: MonthDebit, on_untick: Callable[[MonthDebit], None]) -> ft.Control:
    # Savings look like any other debit here: the Monthly page never singles them out.
    return theme.hoverable(
        ft.Container(
            padding=ft.Padding.only(left=12, right=6, top=8, bottom=8),
            border_radius=theme.RADIUS_SM,
            content=ft.Row(
                [
                    theme.icon_tile(ft.Icons.EVENT_REPEAT, theme.MAUVE, size=30),
                    ft.Column(
                        [
                            ft.Text(
                                debit.template.name,
                                size=14,
                                weight=ft.FontWeight.W_500,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(schedule_text(debit.template), size=12, color=theme.MUTED),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.Text(
                        theme.money(debit.amount),
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=theme.MAUVE,
                    ),
                    theme.icon_button(ft.Icons.REMOVE_DONE, "Untick", lambda: on_untick(debit), size=28),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )


def ticked_debits_card(
    debits: Sequence[MonthDebit],
    on_untick: Callable[[MonthDebit], None],
    on_open: Callable[[], None],
) -> ft.Control:
    """A card listing the debits ticked off this month, with their total next to
    the title and a nudge for any still to tick off."""
    ticked = [d for d in debits if d.applied]
    to_go = sum(1 for d in debits if not d.applied and d.template.is_active)
    total = sum((d.amount for d in ticked), decimal.Decimal(0))

    header = ft.Container(
        theme.card_title(
            "Debits",
            ft.Text(theme.money(total), size=13, weight=ft.FontWeight.W_600, color=theme.MAUVE),
        ),
        padding=ft.Padding.only(left=12, right=12, bottom=6),
    )

    if ticked:
        rows: list[ft.Control] = [_row(d, on_untick) for d in ticked]
    else:
        rows = [
            ft.Container(
                ft.Text("Nothing ticked off yet", size=13, color=theme.MUTED),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        ]

    if to_go:
        rows.append(
            theme.hoverable(
                ft.Container(
                    margin=ft.Margin.only(top=4),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=theme.RADIUS_SM,
                    on_click=lambda _: on_open(),
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.PENDING_ACTIONS, size=16, color=theme.MAUVE),
                            ft.Text(
                                f"{to_go} still to tick off",
                                size=13,
                                weight=ft.FontWeight.W_500,
                                color=theme.MAUVE,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=theme.MAUVE),
                        ],
                        spacing=8,
                    ),
                ),
                theme.tinted(theme.MAUVE, 0.10),
            )
        )

    return theme.card(
        ft.Column([header, *rows], spacing=0),
        padding=ft.Padding.only(left=8, right=8, top=18, bottom=10),
    )
