"""The monthly debits pop-up: every debit due in a month as a grid of tiles,
each with a switch that ticks it off (applies it) for that month."""

import datetime
import decimal
import math

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from expynses.contracts.debits import (
    DebitPaymentDto,
    DebitPaymentFilterDto,
    DebitTemplateDto,
    DebitTemplateFilterDto,
    Frequency,
)
from expynses.services.debits import (
    add_debit_payment,
    delete_debit_payment,
    list_debit_payments,
    search_debit_templates,
)
from expynses.ui import theme
from expynses.ui.debit_page import debit_icon, schedule_text

ZERO = decimal.Decimal(0)

COLUMNS = 3
TILE_WIDTH = 228
TILE_HEIGHT = 124
GAP = 12
GRID_WIDTH = COLUMNS * TILE_WIDTH + (COLUMNS - 1) * GAP
MAX_GRID_HEIGHT = 440


@dataclass(frozen=True)
class MonthDebit:
    """A debit as it stands in one month: its template and, if ticked off, its payment."""

    template: DebitTemplateDto
    payment: DebitPaymentDto | None

    @property
    def applied(self) -> bool:
        return self.payment is not None

    @property
    def amount(self) -> decimal.Decimal:
        # Once applied, the payment keeps the amount it was applied at.
        return self.payment.amount if self.payment else self.template.amount


def _due_in(template: DebitTemplateDto, month: datetime.date) -> bool:
    if template.frequency is Frequency.YEARLY:
        return template.date.month == month.month
    return True


def month_debits(month: datetime.date) -> list[MonthDebit]:
    """The debits that belong in a month: active ones that are due, plus any
    already applied that month even if they've since been paused."""
    templates = search_debit_templates(DebitTemplateFilterDto())
    payments = {
        p.template_id: p
        for p in list_debit_payments(DebitPaymentFilterDto(given_date=month))
    }
    debits = [
        MonthDebit(t, payments.get(t.id))
        for t in templates
        if t.id in payments or (t.is_active and _due_in(t, month))
    ]
    # Monthly first, then yearly, by name; stable so tiles don't jump when toggled.
    return sorted(
        debits,
        key=lambda d: (d.template.frequency is Frequency.YEARLY, d.template.name.lower()),
    )


def pending(debits: list[MonthDebit]) -> list[MonthDebit]:
    """The active debits not yet ticked off."""
    return [d for d in debits if not d.applied and d.template.is_active]


def _tile(debit: MonthDebit, on_toggle: Callable[[MonthDebit, bool], None]) -> ft.Control:
    template = debit.template
    locked = not template.is_active

    if locked:
        detail = "Paused · resume it in Debits"
    elif debit.payment and debit.payment.amount != template.amount:
        detail = f"Ticked at old amount · now {theme.money(template.amount)}"
    else:
        detail = schedule_text(template) + (" · Savings" if template.is_savings else "")

    switch = ft.Switch(
        value=debit.applied,
        disabled=locked,
        scale=0.85,
        active_color=theme.ON_ACCENT,
        active_track_color=theme.MAUVE,
        on_change=lambda e: on_toggle(debit, bool(e.control.value)),
    )

    resting = theme.tinted(theme.MAUVE, 0.08) if debit.applied else theme.SURFACE_HIGH
    tile = ft.Container(
        width=TILE_WIDTH,
        height=TILE_HEIGHT,
        padding=ft.Padding.only(left=14, right=6, top=10, bottom=12),
        border_radius=theme.RADIUS,
        bgcolor=resting,
        border=ft.Border.all(1, theme.tinted(theme.MAUVE, 0.35) if debit.applied else theme.BORDER),
        opacity=0.55 if locked else 1.0,
        # The whole tile is a big switch.
        on_click=None if locked else (lambda _: on_toggle(debit, not debit.applied)),
        content=ft.Column(
            [
                ft.Row(
                    [debit_icon(template), ft.Container(expand=True), switch],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Text(
                    template.name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=theme.TEXT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Row(
                    [
                        ft.Text(
                            theme.money(debit.amount),
                            size=15,
                            weight=ft.FontWeight.W_600,
                            color=theme.MAUVE if debit.applied else theme.TEXT_SOFT,
                        ),
                        ft.Text(
                            detail,
                            size=11,
                            color=theme.MUTED,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=2,
        ),
    )
    if locked:
        return tile
    hover = theme.tinted(theme.MAUVE, 0.14) if debit.applied else theme.SURFACE_HOVER
    return theme.hoverable(tile, hover)


def _section(title: str, debits: list[MonthDebit], on_toggle) -> list[ft.Control]:
    if not debits:
        return []
    ticked = sum(1 for d in debits if d.applied)
    header = ft.Row(
        [
            theme.label(title),
            theme.badge(f"{ticked}/{len(debits)}", theme.MAUVE if ticked == len(debits) else theme.MUTED),
        ],
        spacing=8,
    )
    grid = ft.Row(
        [_tile(d, on_toggle) for d in debits],
        wrap=True,
        spacing=GAP,
        run_spacing=GAP,
        width=GRID_WIDTH,
    )
    return [header, grid]


def _section_height(count: int) -> int:
    rows = math.ceil(count / COLUMNS)
    return 28 + rows * TILE_HEIGHT + (rows - 1) * GAP if count else 0


def _progress(debits: list[MonthDebit]) -> ft.Control:
    applied = [d for d in debits if d.applied]
    total = sum((d.amount for d in debits), ZERO)
    done = sum((d.amount for d in applied), ZERO)
    fraction = float(done / total) if total else 0.0
    all_done = len(applied) == len(debits)

    status = (
        ft.Row(
            [
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.GREEN, size=16),
                ft.Text("All ticked off", size=12, weight=ft.FontWeight.W_600, color=theme.GREEN),
            ],
            spacing=5,
            tight=True,
        )
        if all_done
        else ft.Text(f"{len(applied)} of {len(debits)} ticked off", size=12, color=theme.MUTED)
    )

    return ft.Column(
        [
            ft.Row(
                [
                    theme.heading(theme.money(done), size=30),
                    ft.Text(f"of {theme.money(total)}", size=14, color=theme.MUTED),
                    ft.Container(expand=True),
                    status,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.BASELINE,
            ),
            theme.bar([(fraction, theme.MAUVE)], height=8),
        ],
        spacing=10,
    )


def _empty() -> ft.Control:
    return ft.Container(
        width=GRID_WIDTH,
        padding=ft.Padding.symmetric(vertical=36),
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                theme.icon_tile(ft.Icons.EVENT_AVAILABLE, theme.MAUVE, size=48),
                ft.Text("Nothing due this month", size=15, weight=ft.FontWeight.W_600),
                ft.Text(
                    "Add debits from the Debits page and they'll show up here.",
                    size=13,
                    color=theme.MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=8,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def toggle_debit(debit: MonthDebit, month: datetime.date, on: bool) -> None:
    """Tick a debit off for a month, or untick it."""
    if on and not debit.applied:
        add_debit_payment(debit.template.id, month)
    elif not on and debit.applied:
        delete_debit_payment(debit.template.id, month)


def open_month_debits(page: ft.Page, month: datetime.date, on_changed: Callable[[], None]) -> None:
    """Show the debits due in `month`. on_changed runs after every switch, so the
    page behind can refresh its totals."""
    body = ft.Column(spacing=18, tight=True, width=GRID_WIDTH)
    apply_all_box = ft.Container()

    def toggle(debit: MonthDebit, on: bool):
        toggle_debit(debit, month, on)
        render()
        on_changed()

    def apply_all():
        for debit in pending(month_debits(month)):
            add_debit_payment(debit.template.id, month)
        render()
        on_changed()

    def render():
        debits = month_debits(month)
        if not debits:
            body.controls = [_empty()]
            apply_all_box.content = None
            return

        monthly = [d for d in debits if d.template.frequency is Frequency.MONTHLY]
        yearly = [d for d in debits if d.template.frequency is Frequency.YEARLY]
        grid_height = _section_height(len(monthly)) + _section_height(len(yearly)) + (
            GAP if monthly and yearly else 0
        )

        body.controls = [
            _progress(debits),
            ft.Column(
                [*_section("Monthly", monthly, toggle), *_section("Yearly", yearly, toggle)],
                spacing=10,
                scroll=ft.ScrollMode.AUTO if grid_height > MAX_GRID_HEIGHT else None,
                height=min(grid_height, MAX_GRID_HEIGHT),
            ),
        ]
        remaining = len(pending(debits))
        apply_all_box.content = (
            ft.TextButton(
                f"Tick off all {remaining}" if remaining > 1 else "Tick off the last one",
                icon=ft.Icons.DONE_ALL,
                on_click=apply_all,
                style=ft.ButtonStyle(color=theme.MAUVE),
            )
            if remaining
            else None
        )

    def close():
        dialog.open = False
        page.update()

    render()

    dialog = ft.AlertDialog(
        bgcolor=theme.SURFACE,
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(
            [
                ft.Column(
                    [theme.label(month.strftime("%B %Y")), theme.heading("Debits", size=21)],
                    spacing=2,
                ),
                ft.IconButton(ft.Icons.CLOSE, icon_color=theme.MUTED, tooltip="Close", on_click=close),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
            width=GRID_WIDTH,
        ),
        content=body,
        actions=[apply_all_box, ft.TextButton("Done", on_click=close)],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    page.show_dialog(dialog)
