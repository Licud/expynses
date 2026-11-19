import calendar
import datetime
import decimal

from collections.abc import Sequence

import flet as ft

from expynses.contracts.credit_payments import CreditPaymentDto, CreditPaymentFilterDto
from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto
from expynses.contracts.incomes import IncomeDto, IncomeFilterDto
from expynses.services.credit_payments import delete_credit_payment, search_credit_payments
from expynses.services.expenses import search_expenses
from expynses.services.incomes import search_incomes
from expynses.services.totals import balance, credit_balance
from expynses.ui import theme
from expynses.ui.credit_payment_list import credit_payment_card
from expynses.ui.dialogs import confirm_delete, open_add_dialog
from expynses.ui.expense_list import category_card, transactions_card
from expynses.ui.forms import credit_payment_form, expense_form, income_form
from expynses.ui.income_list import income_card

ZERO = decimal.Decimal(0)
RAIL_WIDTH = 340


def _legend(color: str, caption: str, amount: decimal.Decimal) -> ft.Control:
    return ft.Row(
        [
            theme.dot(color),
            ft.Text(caption, size=12, color=theme.MUTED),
            ft.Text(theme.money(amount), size=12, weight=ft.FontWeight.W_600, color=theme.TEXT_SOFT),
        ],
        spacing=6,
        tight=True,
    )


def _side_stat(icon: ft.IconData, color: str, caption: str, value: str) -> ft.Control:
    return ft.Row(
        [
            theme.icon_tile(icon, color, size=30),
            ft.Text(caption, size=13, color=theme.MUTED, expand=True),
            ft.Text(value, size=15, weight=ft.FontWeight.W_600, color=theme.TEXT),
        ],
        spacing=12,
    )


def _hero(
    expenses: Sequence[ExpenseDto],
    incomes: Sequence[IncomeDto],
    payments: Sequence[CreditPaymentDto],
    card_balance: decimal.Decimal,
    carried_over: decimal.Decimal,
    days_counted: int,
) -> ft.Control:
    """The month at a glance: what's left, a spend bar and the key numbers."""
    income = sum((i.amount for i in incomes), ZERO)
    spent = sum((e.price for e in expenses), ZERO)
    on_credit = sum((e.price for e in expenses if e.is_credit), ZERO)
    paid = spent - on_credit
    card_paid = sum((p.amount for p in payments), ZERO)
    # Credit card spending isn't paid from this month's income; what comes off
    # what's left is paid-in-full spending plus the card payments made this month.
    # Whatever was left over from earlier months rolls in on top of this month's income.
    available = income + carried_over
    left = available - paid - card_paid
    # The bar is measured against what's available, or against paid spending if that is bigger.
    scale = max(available, paid)
    parts = [(float(paid / scale) if scale else 0.0, theme.ACCENT)]

    if available > 0:
        caption = f"{theme.money(paid)} paid of {theme.money(available)} available · {paid / available:.0%} used"
    else:
        caption = f"{theme.money(paid)} paid · nothing available this month"
    if carried_over:
        caption += f" · {theme.money(carried_over)} carried over"

    cash_legend = [_legend(theme.ACCENT, "Paid in full", paid)]
    if left > 0:
        cash_legend.append(_legend(theme.SURFACE_HOVER, "Remaining", left))

    # The card bar shows this month's card spending and how much of it has been
    # repaid: slate is repaid, amber is still owed from this month's spending.
    card_scale = max(on_credit, card_paid)
    repaid_part = min(card_paid, on_credit) if on_credit else card_paid
    card_parts = [
        (float(repaid_part / card_scale) if card_scale else 0.0, theme.SLATE),
        (float((on_credit - repaid_part) / card_scale) if card_scale else 0.0, theme.AMBER),
    ]
    card_legend = [
        _legend(theme.AMBER, "Credit card owed", card_balance),
        _legend(theme.SLATE, "Credit repayments", card_paid),
    ]

    summary = ft.Column(
        [
            theme.label("Left to spend"),
            theme.heading(theme.money(left), size=46, color=theme.TEXT if left >= 0 else theme.RED),
            ft.Text(caption, size=13, color=theme.MUTED),
            ft.Container(height=10),
            theme.bar(parts, height=8),
            ft.Row(cash_legend, spacing=20, wrap=True),
            ft.Container(height=6),
            theme.bar(card_parts, height=8),
            ft.Row(card_legend, spacing=20, wrap=True),
        ],
        spacing=6,
        expand=True,
    )

    daily = spent / days_counted if days_counted else ZERO
    side = ft.Container(
        width=RAIL_WIDTH - 40,
        content=ft.Column(
            [
                _side_stat(ft.Icons.ARROW_DOWNWARD, theme.GREEN, "Income", theme.money(income)),
                _side_stat(ft.Icons.ARROW_UPWARD, theme.ACCENT_TEXT, "Spent", theme.money(spent)),
                _side_stat(ft.Icons.CREDIT_CARD, theme.AMBER, "Credit card owed", theme.money(card_balance)),
                _side_stat(ft.Icons.SHOW_CHART, theme.SLATE, "Daily average", theme.money(daily)),
            ],
            spacing=14,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=28, vertical=24),
        border_radius=theme.RADIUS,
        border=ft.Border.all(1, theme.BORDER),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[theme.tinted(theme.ACCENT, 0.16), theme.SURFACE, theme.SURFACE],
            stops=[0.0, 0.55, 1.0],
        ),
        content=ft.Row(
            [
                summary,
                ft.Container(width=1, height=120, bgcolor=theme.BORDER),
                side,
            ],
            spacing=32,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def monthly_view(page: ft.Page) -> ft.Control:
    """The 'Monthly' page: pick a month, see its money in and out, add entries."""
    today = datetime.date.today()
    this_month = today.replace(day=1)

    # The first day of the month being shown.
    month = {"start": this_month}

    month_title = theme.heading("", size=30)

    def date_range() -> tuple[datetime.date, datetime.date]:
        start = month["start"]
        last_day = calendar.monthrange(start.year, start.month)[1]
        return start, start.replace(day=last_day)

    def days_counted() -> int:
        """Days so far this month, or the whole month for other months."""
        start, end = date_range()
        return today.day if start == this_month else end.day

    hero_box = ft.Container()
    transactions_box = ft.Container(expand=True)
    categories_box = ft.Container()
    incomes_box = ft.Container()
    payments_box = ft.Container()

    def ask_delete_payment(payment: CreditPaymentDto):
        def delete():
            delete_credit_payment(payment.id)
            refresh()

        confirm_delete(
            page,
            f"Delete the {theme.money(payment.amount)} repayment on "
            f"{payment.date.strftime('%d %b')}?",
            delete,
        )

    def load():
        start, end = date_range()
        expenses = list(search_expenses(ExpenseFilterDto(from_date=start, to_date=end)))
        incomes = list(search_incomes(IncomeFilterDto(from_date=start, to_date=end)))
        payments = list(search_credit_payments(CreditPaymentFilterDto(from_date=start, to_date=end)))
        month_title.value = start.strftime("%B %Y")
        carried_over = balance(to_date=start - datetime.timedelta(days=1))
        hero_box.content = _hero(
            expenses, incomes, payments, credit_balance(to_date=end), carried_over, days_counted()
        )
        transactions_box.content = transactions_card(expenses)
        categories_box.content = category_card(expenses)
        incomes_box.content = income_card(
            incomes, title="Income", empty_text="No income this month", show_date=False
        )
        payments_box.content = credit_payment_card(payments, on_delete=ask_delete_payment)

    def refresh():
        load()
        page.update()

    def shift_month(delta: int):
        start = month["start"]
        index = start.year * 12 + (start.month - 1) + delta
        month["start"] = datetime.date(index // 12, index % 12 + 1, 1)
        refresh()

    def go_to_this_month():
        month["start"] = this_month
        refresh()

    def add_dialog(title: str, build_form):
        # Add to the month on screen: today if it's the current month.
        default = today if month["start"] == this_month else month["start"]
        open_add_dialog(page, title, build_form, on_saved=refresh, default_date=default)

    load()

    # A compact segmented control: previous | Today | next.
    divider = ft.Container(width=1, height=18, bgcolor=theme.BORDER)
    month_switcher = ft.Container(
        height=theme.CONTROL_HEIGHT,
        bgcolor=theme.SURFACE,
        border=ft.Border.all(1, theme.BORDER),
        border_radius=theme.RADIUS_SM,
        padding=2,
        content=ft.Row(
            [
                theme.icon_button(ft.Icons.CHEVRON_LEFT, "Previous month", lambda: shift_month(-1), size=30),
                divider,
                theme.hoverable(
                    ft.Container(
                        ft.Text("Today", size=13, weight=ft.FontWeight.W_600, color=theme.TEXT_SOFT),
                        padding=ft.Padding.symmetric(horizontal=12),
                        height=30,
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda _: go_to_this_month(),
                    ),
                    theme.SURFACE_HOVER,
                ),
                divider,
                theme.icon_button(ft.Icons.CHEVRON_RIGHT, "Next month", lambda: shift_month(1), size=30),
            ],
            spacing=2,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    header = ft.Row(
        [
            ft.Column([theme.label("Monthly overview"), month_title], spacing=2),
            ft.Container(expand=True),
            month_switcher,
            ft.Container(width=4),
            theme.action_button(
                "Repayment",
                ft.Icons.CREDIT_CARD,
                lambda: add_dialog("Add credit repayment", credit_payment_form),
                primary=False,
            ),
            theme.action_button("Income", ft.Icons.ADD, lambda: add_dialog("Add income", income_form), primary=False),
            theme.action_button("Expense", ft.Icons.ADD, lambda: add_dialog("Add expense", expense_form)),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )

    main_column = ft.Column([hero_box, transactions_box], spacing=20, expand=True)
    rail = ft.Column(
        [categories_box, incomes_box, payments_box],
        spacing=20,
        width=RAIL_WIDTH,
        scroll=ft.ScrollMode.AUTO,
    )

    body = ft.Row(
        [main_column, rail],
        spacing=20,
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )
    return ft.Column([header, body], spacing=24, expand=True)
