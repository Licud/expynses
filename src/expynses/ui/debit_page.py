"""The 'Debits' page: every recurring debit template, grouped by how often it
is collected, with add, edit, pause and delete."""

import datetime
import decimal

from collections.abc import Callable, Sequence
from functools import partial

import flet as ft

from expynses.contracts.debits import (
    DebitTemplateDto,
    DebitTemplateFilterDto,
    Frequency,
    UpdateDebitTemplateDto,
)
from expynses.services.debits import (
    delete_debit_template,
    search_debit_templates,
    update_debit_template,
)
from expynses.ui import theme
from expynses.ui.dialogs import confirm_delete, open_add_dialog
from expynses.ui.forms import debit_template_form, show_toast

ZERO = decimal.Decimal(0)


# --- Shared look for a single debit, also used by the monthly pop-up ---


def debit_icon(template: DebitTemplateDto) -> ft.Control:
    if template.is_savings:
        return theme.icon_tile(ft.Icons.SAVINGS_OUTLINED, theme.GREEN, size=34)
    return theme.icon_tile(ft.Icons.EVENT_REPEAT, theme.MAUVE, size=34)


def schedule_text(template: DebitTemplateDto) -> str:
    if template.frequency is Frequency.YEARLY:
        return f"Every {template.date.strftime('%B')}"
    return "Every month"


# --- Summary ---


def _stat(caption: str, value: str, detail: str | None = None) -> ft.Control:
    lines: list[ft.Control] = [
        theme.label(caption),
        ft.Text(value, size=18, weight=ft.FontWeight.W_600, color=theme.TEXT),
    ]
    if detail:
        lines.append(ft.Text(detail, size=12, color=theme.MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS))
    return ft.Column(lines, spacing=3, expand=True)


def _divider() -> ft.Control:
    return ft.Container(width=1, height=56, bgcolor=theme.BORDER)


def _next_yearly(yearly: Sequence[DebitTemplateDto], today: datetime.date) -> DebitTemplateDto | None:
    """The yearly debit whose month comes round soonest, counting this month."""
    return min(yearly, key=lambda t: (t.date.month - today.month) % 12, default=None)


def yearly_cost(template: DebitTemplateDto) -> decimal.Decimal:
    """What a debit comes to over a whole year."""
    return template.amount * 12 if template.frequency is Frequency.MONTHLY else template.amount


def _total(templates: Sequence[DebitTemplateDto]) -> decimal.Decimal:
    return sum((t.amount for t in templates), ZERO)


def _summary(templates: Sequence[DebitTemplateDto], today: datetime.date) -> ft.Control:
    active = [t for t in templates if t.is_active]
    monthly = [t for t in active if t.frequency is Frequency.MONTHLY]
    yearly = [t for t in active if t.frequency is Frequency.YEARLY]

    monthly_total = _total(monthly)
    monthly_debits = _total([t for t in monthly if not t.is_savings])
    monthly_savings = _total([t for t in monthly if t.is_savings])
    whole_year = sum((yearly_cost(t) for t in active), ZERO)
    upcoming = _next_yearly(yearly, today)

    headline = ft.Column(
        [
            theme.label("Goes out every month"),
            theme.heading(theme.money(monthly_total), size=40),
            ft.Text(
                f"{len(monthly)} monthly debit{'' if len(monthly) == 1 else 's'}",
                size=12,
                color=theme.MUTED,
            ),
        ],
        spacing=4,
        expand=2,
    )

    if upcoming:
        when = "this month" if upcoming.date.month == today.month else upcoming.date.strftime("in %B")
        next_stat = _stat("Next yearly", theme.money(upcoming.amount), f"{upcoming.name} · {when}")
    else:
        next_stat = _stat("Next yearly", "—", "No yearly debits")

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=28, vertical=22),
        border_radius=theme.RADIUS,
        border=ft.Border.all(1, theme.BORDER),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[theme.tinted(theme.MAUVE, 0.10), theme.SURFACE, theme.SURFACE],
            stops=[0.0, 0.45, 1.0],
        ),
        content=ft.Row(
            [
                headline,
                _divider(),
                _stat("Debits", theme.money(monthly_debits), f"{theme.money(monthly_debits * 12)} a year"),
                _divider(),
                _stat("Savings", theme.money(monthly_savings), f"{theme.money(monthly_savings * 12)} a year"),
                _divider(),
                _stat("Whole year", theme.money(whole_year), f"incl. {theme.money(_total(yearly))} yearly"),
                _divider(),
                next_stat,
            ],
            spacing=28,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


# --- The list ---


def _row(
    template: DebitTemplateDto,
    on_edit: Callable[[DebitTemplateDto], None],
    on_delete: Callable[[DebitTemplateDto], None],
    on_set_active: Callable[[DebitTemplateDto, bool], None],
) -> ft.Control:
    muted = not template.is_active
    tags: list[ft.Control] = []
    if template.is_savings:
        tags.append(theme.badge("Savings", theme.GREEN))
    if muted:
        tags.append(theme.badge("Paused"))

    title = ft.Row(
        [
            ft.Text(
                template.name,
                size=14,
                weight=ft.FontWeight.W_500,
                color=theme.TEXT_SOFT if muted else theme.TEXT,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            *tags,
        ],
        spacing=8,
        tight=True,
    )

    switch = ft.Switch(
        value=template.is_active,
        scale=0.8,
        tooltip="Pause" if template.is_active else "Resume",
        on_change=lambda e: on_set_active(template, bool(e.control.value)),
    )

    return theme.hoverable(
        ft.Container(
            padding=ft.Padding.only(left=12, right=6, top=9, bottom=9),
            border_radius=theme.RADIUS_SM,
            opacity=0.6 if muted else 1.0,
            content=ft.Row(
                [
                    debit_icon(template),
                    ft.Column(
                        [title, ft.Text(schedule_text(template), size=12, color=theme.MUTED)],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                theme.money(template.amount),
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=theme.MUTED if muted else theme.TEXT,
                            ),
                            ft.Text(
                                f"{theme.money(yearly_cost(template))} a year"
                                if template.frequency is Frequency.MONTHLY
                                else "once a year",
                                size=11,
                                color=theme.MUTED,
                            ),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    switch,
                    theme.icon_button(ft.Icons.EDIT_OUTLINED, "Edit", lambda: on_edit(template), size=30),
                    theme.icon_button(ft.Icons.DELETE_OUTLINE, "Delete", lambda: on_delete(template), size=30),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )


def _section(title: str, templates: list[DebitTemplateDto], row: Callable[[DebitTemplateDto], ft.Control]) -> list[ft.Control]:
    if not templates:
        return []
    total = sum((t.amount for t in templates), ZERO)
    header = ft.Container(
        padding=ft.Padding.only(left=12, right=12, top=14, bottom=4),
        content=ft.Row(
            [
                theme.label(title),
                theme.badge(str(len(templates))),
                ft.Container(expand=True),
                ft.Text(theme.money(total), size=12, color=theme.MUTED),
            ],
            spacing=8,
        ),
    )
    return [header, *(row(t) for t in sorted(templates, key=lambda t: t.name.lower()))]


def _templates_card(
    templates: Sequence[DebitTemplateDto],
    row: Callable[[DebitTemplateDto], ft.Control],
) -> ft.Control:
    active = [t for t in templates if t.is_active]
    paused = [t for t in templates if not t.is_active]
    controls = [
        *_section("Monthly", [t for t in active if t.frequency is Frequency.MONTHLY], row),
        *_section("Yearly", [t for t in active if t.frequency is Frequency.YEARLY], row),
        *_section("Paused", paused, row),
    ]
    header = ft.Container(
        theme.card_title("All debits", theme.badge(str(len(templates)))),
        padding=ft.Padding.symmetric(horizontal=12),
    )
    return theme.card(
        ft.Column([header, *controls], spacing=0),
        padding=ft.Padding.only(left=8, right=8, top=18, bottom=10),
    )


def _empty_state(on_add: Callable[[], None]) -> ft.Control:
    return theme.card(
        ft.Column(
            [
                theme.icon_tile(ft.Icons.EVENT_REPEAT, theme.MAUVE, size=56),
                theme.heading("No debits yet", size=22),
                ft.Text(
                    "Add the things that go out on a schedule (rent, bills, subscriptions, "
                    "savings pots) and tick them off on the Monthly page.",
                    size=13,
                    color=theme.MUTED,
                    text_align=ft.TextAlign.CENTER,
                    width=380,
                ),
                ft.Container(height=4),
                theme.action_button("Add your first debit", ft.Icons.ADD, on_add, accent=theme.MAUVE),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=48),
    )


# --- The page ---


def debits_view(page: ft.Page) -> ft.Control:
    """The 'Debits' page: totals up top and every debit template below."""
    summary_box = ft.Container()
    list_box = ft.Container()

    def open_add():
        open_add_dialog(page, "Add debit", debit_template_form, on_saved=refresh)

    def open_edit(template: DebitTemplateDto):
        open_add_dialog(page, "Edit debit", partial(debit_template_form, template=template), on_saved=refresh)

    def set_active(template: DebitTemplateDto, active: bool):
        update_debit_template(
            template.id,
            UpdateDebitTemplateDto(
                name=template.name,
                date=template.date,
                amount=template.amount,
                frequency=template.frequency,
                is_active=active,
            ),
        )
        refresh()
        show_toast(page, f"{template.name} {'resumed' if active else 'paused'}")

    def ask_delete(template: DebitTemplateDto):
        def delete():
            delete_debit_template(template.id)
            refresh()
            show_toast(page, f"{template.name} deleted")

        confirm_delete(
            page,
            f"Delete “{template.name}” for good?",
            delete,
            title="Delete debit?",
            warning=(
                "This also wipes it from every month it was ticked off in, so those "
                "months' left to spend will change. This can't be undone. "
                "To stop it without losing history, pause it instead."
            ),
            confirm_text="Delete forever",
        )

    def row(template: DebitTemplateDto) -> ft.Control:
        return _row(template, open_edit, ask_delete, set_active)

    def load():
        templates = list(search_debit_templates(DebitTemplateFilterDto()))
        if templates:
            summary_box.content = _summary(templates, datetime.date.today())
            summary_box.visible = True
            list_box.content = _templates_card(templates, row)
        else:
            summary_box.visible = False
            list_box.content = _empty_state(open_add)

    def refresh():
        load()
        page.update()

    load()

    header = ft.Row(
        [
            ft.Column([theme.label("Recurring"), theme.heading("Debits", size=30)], spacing=2),
            ft.Container(expand=True),
            theme.action_button("Debit", ft.Icons.ADD, open_add, accent=theme.MAUVE),
        ],
        vertical_alignment=ft.CrossAxisAlignment.END,
    )
    return ft.Column(
        [
            header,
            ft.Column([summary_box, list_box], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True),
        ],
        spacing=24,
        expand=True,
    )
