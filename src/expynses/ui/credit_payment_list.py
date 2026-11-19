"""Builder for the credit payments card. It takes already-loaded payments; the
page decides when to load and what happens on delete."""

import decimal

from collections.abc import Callable, Sequence

import flet as ft

from expynses.contracts.credit_payments import CreditPaymentDto
from expynses.ui import theme


def _row(payment: CreditPaymentDto, on_delete: Callable[[CreditPaymentDto], None]) -> ft.Control:
    return theme.hoverable(
        ft.Container(
            padding=ft.Padding.only(left=12, right=6, top=8, bottom=8),
            border_radius=theme.RADIUS_SM,
            content=ft.Row(
                [
                    theme.icon_tile(ft.Icons.CREDIT_CARD, theme.AMBER, size=30),
                    ft.Text(
                        payment.date.strftime("%a %d %b"),
                        size=14,
                        weight=ft.FontWeight.W_500,
                        expand=True,
                    ),
                    ft.Text(
                        theme.money(payment.amount),
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=theme.AMBER,
                    ),
                    theme.icon_button(
                        ft.Icons.DELETE_OUTLINE, "Delete", lambda: on_delete(payment), size=28
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )


def credit_payment_card(
    payments: Sequence[CreditPaymentDto],
    on_delete: Callable[[CreditPaymentDto], None],
    title: str = "Credit repayments",
    empty_text: str = "No credit repayments this month",
) -> ft.Control:
    """A card listing credit card repayments, with their total next to the title."""
    total = sum((p.amount for p in payments), decimal.Decimal(0))
    header = ft.Container(
        theme.card_title(
            title,
            ft.Text(theme.money(total), size=13, weight=ft.FontWeight.W_600, color=theme.AMBER),
        ),
        padding=ft.Padding.only(left=12, right=12, bottom=6),
    )
    if payments:
        rows: list[ft.Control] = [_row(p, on_delete) for p in payments]
    else:
        rows = [
            ft.Container(
                ft.Text(empty_text, size=13, color=theme.MUTED),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        ]
    return theme.card(
        ft.Column([header, *rows], spacing=0),
        padding=ft.Padding.only(left=8, right=8, top=18, bottom=10),
    )
