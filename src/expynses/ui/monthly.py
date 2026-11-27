import calendar
import datetime
import decimal

from collections.abc import Sequence

import flet as ft

from expynses.contracts.credit_payments import CreditPaymentDto, CreditPaymentFilterDto
from expynses.contracts.debits import DebitPaymentFilterDto
from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto
from expynses.contracts.incomes import IncomeDto, IncomeFilterDto
from expynses.services.credit_payments import delete_credit_payment, search_credit_payments
from expynses.services.expenses import search_expenses
from expynses.services.incomes import delete_income, search_incomes
from expynses.services.totals import balance, credit_balance, total_debit_payments
from expynses.ui import theme
from expynses.ui.credit_payment_list import credit_payment_card
from expynses.ui.debit_list import ticked_debits_card
from expynses.ui.debit_month_dialog import MonthDebit, month_debits, open_month_debits, pending, toggle_debit
from expynses.ui.dialogs import confirm_delete, open_add_dialog
from expynses.ui.expense_list import category_card, transactions_card
from expynses.ui.forms import credit_payment_form, expense_form, income_form
from expynses.ui.income_list import income_card
from expynses.ui.month_picker import open_month_picker
from expynses.ui.reports_data import NoSpendDays, left_to_spend, no_spend_days

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


def _side_stat(
    icon: ft.IconData, color: str, caption: str, value: str, tooltip: str | None = None
) -> ft.Control:
    row = ft.Row(
        [
            theme.icon_tile(icon, color, size=30),
            ft.Text(caption, size=13, color=theme.MUTED, expand=True),
            ft.Text(value, size=15, weight=ft.FontWeight.W_600, color=theme.TEXT),
        ],
        spacing=12,
    )
    return ft.Container(content=row, tooltip=tooltip) if tooltip else row


def _no_spend_stat(no_spend: NoSpendDays, is_current_month: bool) -> ft.Control:
    """Days with nothing bought, out of the days so far."""
    if not no_spend.days:
        return _side_stat(ft.Icons.NOT_INTERESTED, theme.GREEN, "No-spend days", "—")
    tip = f"Longest run: {no_spend.longest_run} {'day' if no_spend.longest_run == 1 else 'days'}"
    if is_current_month:
        tip += f" · current run: {no_spend.current_run} {'day' if no_spend.current_run == 1 else 'days'}"
    return _side_stat(
        ft.Icons.NOT_INTERESTED, theme.GREEN, "No-spend days", f"{no_spend.no_spend} of {no_spend.days}", tip
    )


def _hero(
    expenses: Sequence[ExpenseDto],
    incomes: Sequence[IncomeDto],
    payments: Sequence[CreditPaymentDto],
    card_balance: decimal.Decimal,
    carried_over: decimal.Decimal,
    debits: decimal.Decimal,
    daily: decimal.Decimal,
    no_spend: NoSpendDays,
    is_current_month: bool,
) -> ft.Control:
    """The month at a glance: what's left, a spend bar and the key numbers."""
    income = sum((i.amount for i in incomes), ZERO)
    spent = sum((e.price for e in expenses), ZERO)
    on_credit = sum((e.price for e in expenses if e.is_credit), ZERO)
    paid = spent - on_credit
    card_paid = sum((p.amount for p in payments), ZERO)
    # Credit card spending isn't paid from this month's income; what comes off
    # what's left is paid-in-full spending, the card payments made this month from
    # the account (external ones only clear the card) and the debits ticked off
    # this month (savings included, never shown apart).
    # Whatever was left over from earlier months rolls in on top of this month's income.
    available = income + carried_over
    used = paid + debits
    left = left_to_spend(expenses, incomes, payments, carried_over, debits)
    # The bar is measured against what's available, or against what's used if that is bigger.
    scale = max(available, used)
    parts = [
        (float(paid / scale) if scale else 0.0, theme.ACCENT),
        (float(debits / scale) if scale else 0.0, theme.MAUVE),
    ]

    out = f"{theme.money(paid)} paid"
    if debits:
        out += f" + {theme.money(debits)} debits"
    if available > 0:
        caption = f"{out} of {theme.money(available)} available · {used / available:.0%} used"
    else:
        caption = f"{out} · nothing available this month"
    if carried_over:
        caption += f" · {theme.money(carried_over)} carried over"

    cash_legend = [_legend(theme.ACCENT, "Paid in full", paid)]
    if debits:
        cash_legend.append(_legend(theme.MAUVE, "Debits", debits))
    if left > 0:
        cash_legend.append(_legend(theme.SURFACE_HOVER, "Remaining", left))

    # The card bar mirrors its legend: amber is the total still owed on the card,
    # slate is what was repaid this month, both measured against their sum.
    owed = max(card_balance, ZERO)
    card_scale = owed + card_paid
    card_parts = [
        (float(owed / card_scale) if card_scale else 0.0, theme.AMBER),
        (float(card_paid / card_scale) if card_scale else 0.0, theme.SLATE),
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

    side = ft.Container(
        width=RAIL_WIDTH - 40,
        content=ft.Column(
            [
                _side_stat(ft.Icons.ARROW_DOWNWARD, theme.GREEN, "Income", theme.money(income)),
                _side_stat(ft.Icons.ARROW_UPWARD, theme.ACCENT_TEXT, "Spent", theme.money(spent)),
                _side_stat(ft.Icons.EVENT_REPEAT, theme.MAUVE, "Debits", theme.money(debits)),
                _side_stat(ft.Icons.CREDIT_CARD, theme.AMBER, "Credit card owed", theme.money(card_balance)),
                _side_stat(ft.Icons.SHOW_CHART, theme.SLATE, "Daily average", theme.money(daily)),
                _no_spend_stat(no_spend, is_current_month),
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

    def daily_average(expenses: Sequence[ExpenseDto]) -> decimal.Decimal:
        """Spending per day: for this month, only the days so far and the
        expenses dated up to today; for other months, the whole month."""
        start, end = date_range()
        if start == this_month:
            so_far = sum((e.price for e in expenses if e.date <= today), ZERO)
            return so_far / today.day
        return sum((e.price for e in expenses), ZERO) / end.day

    hero_box = ft.Container()
    transactions_box = ft.Container(expand=True)
    categories_box = ft.Container()
    incomes_box = ft.Container()
    payments_box = ft.Container()
    debits_button_box = ft.Container()
    debits_box = ft.Container()

    def open_debits():
        open_month_debits(page, month["start"], on_changed=refresh)

    def untick(debit: MonthDebit):
        toggle_debit(debit, month["start"], on=False)
        refresh()

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

    def ask_delete_income(income: IncomeDto):
        def delete():
            delete_income(income.id)
            refresh()

        confirm_delete(
            page,
            f"Delete the {theme.money(income.amount)} income from {income.source}?",
            delete,
        )

    def load():
        start, end = date_range()
        expenses = list(search_expenses(ExpenseFilterDto(from_date=start, to_date=end)))
        incomes = list(search_incomes(IncomeFilterDto(from_date=start, to_date=end)))
        payments = list(search_credit_payments(CreditPaymentFilterDto(from_date=start, to_date=end)))
        month_title.value = start.strftime("%B %Y")
        carried_over = balance(to_date=start - datetime.timedelta(days=1))
        debits = total_debit_payments(DebitPaymentFilterDto(given_date=start))
        # Only the days so far count: today is included, like the daily average above.
        no_spend = no_spend_days(expenses, start, min(end, today))
        hero_box.content = _hero(
            expenses, incomes, payments, credit_balance(to_date=end), carried_over, debits, daily_average(expenses),
            no_spend, start == this_month,
        )
        this_months_debits = month_debits(start)
        # The pill on the Debits button counts what still needs ticking off.
        debits_button_box.content = theme.action_button(
            "Debits",
            ft.Icons.EVENT_REPEAT,
            open_debits,
            primary=False,
            count=len(pending(this_months_debits)),
            accent=theme.MAUVE,
        )
        debits_box.content = ticked_debits_card(this_months_debits, on_untick=untick, on_open=open_debits)
        transactions_box.content = transactions_card(expenses)
        categories_box.content = category_card(expenses)
        incomes_box.content = income_card(
            incomes, on_delete=ask_delete_income, title="Income", empty_text="No income this month", show_date=False
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

    def go_to_month(start: datetime.date):
        month["start"] = start
        refresh()

    def pick_month():
        open_month_picker(page, month["start"], go_to_month)

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
                theme.icon_button(ft.Icons.CALENDAR_MONTH, "Pick a month", pick_month, size=30),
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
            debits_button_box,
            theme.action_button(
                "Repayment",
                ft.Icons.CREDIT_CARD,
                lambda: add_dialog("Add credit repayment", credit_payment_form),
                primary=False,
                accent=theme.AMBER,
            ),
            theme.action_button(
                "Income",
                ft.Icons.ADD,
                lambda: add_dialog("Add income", income_form),
                primary=False,
                accent=theme.GREEN,
            ),
            theme.action_button("Expense", ft.Icons.ADD, lambda: add_dialog("Add expense", expense_form)),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )

    main_column = ft.Column([hero_box, transactions_box], spacing=20, expand=True)
    rail = ft.Column(
        [categories_box, incomes_box, payments_box, debits_box],
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
