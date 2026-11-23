import datetime
import decimal
import uuid

from collections.abc import Callable

import flet as ft

from expynses.contracts.credit_payments import NewCreditPaymentDto
from expynses.contracts.debits import (
    DebitTemplateDto,
    Frequency,
    NewDebitTemplateDto,
    UpdateDebitTemplateDto,
)
from expynses.contracts.expenses import NewExpenseDto
from expynses.contracts.incomes import NewIncomeDto
from expynses.services.credit_payments import add_credit_payment
from expynses.services.debits import add_debit_template, update_debit_template
from expynses.services.expenses import add_expense
from expynses.services.expenses_types import get_expense_types
from expynses.services.incomes import add_income
from expynses.services.totals import credit_balance
from expynses.ui import theme
from expynses.ui.expense_type_icons import icon_for_type


DATE_FORMAT = "%d-%m-%Y"  # dd-MM-yyyy


def picked_date(value: datetime.datetime) -> datetime.date:
    """Flet hands back the picked day as a UTC datetime; convert to local so
    zones ahead of UTC don't land on the previous day."""
    if value.tzinfo is not None:
        value = value.astimezone()
    return value.date()
TOAST_WIDTH = 300


def show_toast(page: ft.Page, message: str) -> None:
    """A floating notification in the bottom-right corner."""
    # A floating SnackBar is centred by default; a left margin pushes it right.
    left = max((page.width or 0) - TOAST_WIDTH - 24, 0)
    page.show_dialog(
        ft.SnackBar(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.GREEN, size=20),
                    ft.Text(message, color=theme.TEXT),
                ],
                spacing=10,
            ),
            bgcolor=theme.SURFACE_HIGH,
            shape=ft.RoundedRectangleBorder(radius=12),
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin.only(left=left, right=24, bottom=24),
            duration=3000,
        )
    )


def expense_form(
    page: ft.Page,
    on_saved: Callable[[bool], None] | None = None,
    default_date: datetime.date | None = None,
) -> ft.Control:
    """The 'add expense' fields.

    After an expense is stored, on_saved(add_another) is called, where
    add_another says whether the user ticked "Add another".
    """
    start_date = default_date or datetime.date.today()

    # --- The input controls ---
    date_field = ft.TextField(
        label="Date",
        value=start_date.strftime(DATE_FORMAT),
        read_only=True,
        suffix_icon=ft.Icons.CALENDAR_MONTH,
        border_radius=10,
        on_click=lambda: pick_date(),
    )
    price = ft.TextField(
        label="Price",
        prefix="£",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
    )
    notes = ft.TextField(label="Notes", multiline=True, min_lines=2, border_radius=10)
    is_credit = ft.Switch(label="Paid by credit card")
    add_another = ft.Switch(label="Add another after saving", value=True)
    expense_type = ft.Dropdown(
        label="Type",
        border_radius=10,
        expand=True,
        options=[
            ft.DropdownOption(
                key=str(et.id),
                text=et.name,
                leading_icon=icon_for_type(et.name),
            )
            for et in get_expense_types()
        ],
    )

    # --- The date picker pop-up ---
    def date_picked():
        if date_picker.value is None:
            return
        date_field.value = picked_date(date_picker.value).strftime(DATE_FORMAT)
        page.update()

    date_picker = ft.DatePicker(value=start_date, on_change=date_picked)

    def pick_date():
        page.show_dialog(date_picker)

    # --- The Save button ---
    async def save():
        # Validate the inputs first, collecting messages on the controls.
        price.error = None
        expense_type.error_text = None

        try:
            price_value = decimal.Decimal(price.value or "")
        except decimal.InvalidOperation:
            price.error = "Enter a valid price"
            price_value = None

        if expense_type.value is None:
            expense_type.error_text = "Pick a type"

        if price_value is None or expense_type.value is None:
            page.update()
            return

        add_expense(
            NewExpenseDto(
                date=datetime.datetime.strptime(date_field.value, DATE_FORMAT).date(),
                price=price_value,
                notes=notes.value or "",
                is_credit=is_credit.value,
                expense_type_id=uuid.UUID(expense_type.value),
            )
        )

        # Keep the date, type and card choice for the next entry in a run;
        # clear what is different every time.
        keep_open = bool(add_another.value)
        if keep_open:
            price.value = ""
            notes.value = ""

        # on_saved may close the dialog this form lives in, so it runs before
        # the toast; otherwise closing would dismiss the toast instead.
        if on_saved is not None:
            on_saved(keep_open)
        show_toast(page, "Expense saved")
        page.update()
        if keep_open:
            await price.focus()

    # --- Layout: the fields stacked top to bottom ---
    return ft.Column(
        width=360,
        tight=True,
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            date_field,
            price,
            ft.Row([expense_type]),
            notes,
            is_credit,
            add_another,
            ft.FilledButton(
                "Save expense",
                icon=ft.Icons.SAVE,
                on_click=save,
                height=44,
            ),
        ],
    )


def income_form(
    page: ft.Page,
    on_saved: Callable[[bool], None] | None = None,
    default_date: datetime.date | None = None,
) -> ft.Control:
    """The 'add income' fields; on_saved(add_another) is called after storing."""
    start_date = default_date or datetime.date.today()

    date_field = ft.TextField(
        label="Date",
        value=start_date.strftime(DATE_FORMAT),
        read_only=True,
        suffix_icon=ft.Icons.CALENDAR_MONTH,
        border_radius=10,
        on_click=lambda: pick_date(),
    )
    amount = ft.TextField(
        label="Amount",
        prefix="£",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
    )
    source = ft.TextField(label="Source", border_radius=10)
    add_another = ft.Switch(label="Add another after saving", value=True)

    def date_picked():
        if date_picker.value is None:
            return
        date_field.value = picked_date(date_picker.value).strftime(DATE_FORMAT)
        page.update()

    date_picker = ft.DatePicker(value=start_date, on_change=date_picked)

    def pick_date():
        page.show_dialog(date_picker)

    async def save():
        amount.error = None
        source.error = None

        try:
            amount_value = decimal.Decimal(amount.value or "")
        except decimal.InvalidOperation:
            amount.error = "Enter a valid amount"
            amount_value = None

        if not (source.value or "").strip():
            source.error = "Enter a source"

        if amount_value is None or source.error:
            page.update()
            return

        add_income(
            NewIncomeDto(
                date=datetime.datetime.strptime(date_field.value, DATE_FORMAT).date(),
                amount=amount_value,
                source=source.value.strip(),
            )
        )

        keep_open = bool(add_another.value)
        if keep_open:
            amount.value = ""
            source.value = ""

        if on_saved is not None:
            on_saved(keep_open)
        show_toast(page, "Income saved")
        page.update()
        if keep_open:
            await amount.focus()

    return ft.Column(
        width=360,
        tight=True,
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            date_field,
            amount,
            source,
            add_another,
            ft.FilledButton("Save income", icon=ft.Icons.SAVE, on_click=save, height=44),
        ],
    )


def credit_payment_form(
    page: ft.Page,
    on_saved: Callable[[bool], None] | None = None,
    default_date: datetime.date | None = None,
) -> ft.Control:
    """The 'add credit repayment' fields; on_saved(add_another) is called after storing."""
    start_date = default_date or datetime.date.today()

    date_field = ft.TextField(
        label="Date",
        value=start_date.strftime(DATE_FORMAT),
        read_only=True,
        suffix_icon=ft.Icons.CALENDAR_MONTH,
        border_radius=10,
        on_click=lambda: pick_date(),
    )
    amount = ft.TextField(
        label="Amount",
        prefix="£",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
    )
    add_another = ft.Switch(label="Add another after saving", value=False)

    def date_picked():
        if date_picker.value is None:
            return
        date_field.value = picked_date(date_picker.value).strftime(DATE_FORMAT)
        page.update()

    date_picker = ft.DatePicker(value=start_date, on_change=date_picked)

    def pick_date():
        page.show_dialog(date_picker)

    async def save():
        amount.error = None

        try:
            amount_value = decimal.Decimal(amount.value or "")
        except decimal.InvalidOperation:
            amount.error = "Enter a valid amount"
            amount_value = None

        if amount_value is not None and amount_value <= 0:
            amount.error = "Amount must be more than zero"
            amount_value = None

        payment_date = datetime.datetime.strptime(date_field.value, DATE_FORMAT).date()
        if amount_value is not None:
            owed = credit_balance(to_date=payment_date)
            if amount_value > owed:
                amount.error = f"Only {theme.money(max(owed, decimal.Decimal(0)))} owed on the card by this date"
                amount_value = None

        if amount_value is None:
            page.update()
            return

        add_credit_payment(
            NewCreditPaymentDto(
                date=payment_date,
                amount=amount_value,
            )
        )

        keep_open = bool(add_another.value)
        if keep_open:
            amount.value = ""

        if on_saved is not None:
            on_saved(keep_open)
        show_toast(page, "Repayment saved")
        page.update()
        if keep_open:
            await amount.focus()

    return ft.Column(
        width=360,
        tight=True,
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            date_field,
            amount,
            add_another,
            ft.FilledButton("Save repayment", icon=ft.Icons.SAVE, on_click=save, height=44),
        ],
    )


def _setting_row(title: str, detail: str, switch: ft.Switch) -> ft.Control:
    """A switch with a title and a line of explanation, on a soft panel."""
    return ft.Container(
        padding=ft.Padding.only(left=14, right=8, top=10, bottom=10),
        border_radius=theme.RADIUS_SM,
        bgcolor=theme.SURFACE_HIGH,
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(title, size=14, weight=ft.FontWeight.W_500, color=theme.TEXT),
                        ft.Text(detail, size=12, color=theme.MUTED),
                    ],
                    spacing=1,
                    expand=True,
                ),
                switch,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def debit_template_form(
    page: ft.Page,
    on_saved: Callable[[bool], None] | None = None,
    default_date: datetime.date | None = None,
    template: DebitTemplateDto | None = None,
) -> ft.Control:
    """The 'add debit' fields, or 'edit debit' when a template is given.

    on_saved(add_another) is called after storing; editing never adds another.
    """
    editing = template is not None
    start_date = template.date if template else (default_date or datetime.date.today())
    start_frequency = template.frequency if template else Frequency.MONTHLY

    name = ft.TextField(
        label="Name",
        value=template.name if template else "",
        hint_text="Rent, phone, rainy day pot…",
        border_radius=10,
        autofocus=not editing,
    )
    amount = ft.TextField(
        label="Amount",
        prefix="£",
        value=f"{template.amount:.2f}" if template else "",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
    )

    # How often it is collected. Yearly debits also need the month they land in.
    frequency = ft.SegmentedButton(
        segments=[
            ft.Segment(value=Frequency.MONTHLY.value, label="Monthly", icon=ft.Icons.EVENT_REPEAT),
            ft.Segment(value=Frequency.YEARLY.value, label="Yearly", icon=ft.Icons.EVENT),
        ],
        selected=[start_frequency.value],
        show_selected_icon=False,
        on_change=lambda: frequency_changed(),
    )

    date_field = ft.TextField(
        label="Collected on",
        value=start_date.strftime(DATE_FORMAT),
        read_only=True,
        suffix_icon=ft.Icons.CALENDAR_MONTH,
        border_radius=10,
        helper="Shows up in this month every year",
        on_click=lambda: pick_date(),
        visible=start_frequency is Frequency.YEARLY,
    )

    def selected_frequency() -> Frequency:
        return Frequency(frequency.selected[0])

    def frequency_changed():
        date_field.visible = selected_frequency() is Frequency.YEARLY
        page.update()

    def date_picked():
        if date_picker.value is None:
            return
        date_field.value = picked_date(date_picker.value).strftime(DATE_FORMAT)
        page.update()

    date_picker = ft.DatePicker(value=start_date, on_change=date_picked)

    def pick_date():
        page.show_dialog(date_picker)

    is_savings = ft.Switch(value=template.is_savings if template else False, disabled=editing)
    is_active = ft.Switch(value=template.is_active if template else True)
    add_another = ft.Switch(label="Add another after saving", value=False, visible=not editing)

    async def save():
        name.error = None
        amount.error = None

        if not (name.value or "").strip():
            name.error = "Give it a name"

        try:
            amount_value = decimal.Decimal(amount.value or "")
        except decimal.InvalidOperation:
            amount.error = "Enter a valid amount"
            amount_value = None

        if amount_value is not None and amount_value <= 0:
            amount.error = "Amount must be more than zero"
            amount_value = None

        if amount_value is None or name.error:
            page.update()
            return

        chosen = selected_frequency()
        # Monthly debits don't use the date; keep whatever it was.
        if chosen is Frequency.YEARLY:
            date_value = datetime.datetime.strptime(date_field.value, DATE_FORMAT).date()
        else:
            date_value = start_date

        if template:
            update_debit_template(
                template.id,
                UpdateDebitTemplateDto(
                    name=name.value.strip(),
                    date=date_value,
                    amount=amount_value,
                    frequency=chosen,
                    is_active=bool(is_active.value),
                ),
            )
        else:
            add_debit_template(
                NewDebitTemplateDto(
                    name=name.value.strip(),
                    date=date_value,
                    amount=amount_value,
                    frequency=chosen,
                    is_savings=bool(is_savings.value),
                    is_active=bool(is_active.value),
                )
            )

        keep_open = bool(add_another.value) and not editing
        if keep_open:
            name.value = ""
            amount.value = ""

        if on_saved is not None:
            on_saved(keep_open)
        show_toast(page, "Debit updated" if editing else "Debit saved")
        page.update()
        if keep_open:
            await name.focus()

    savings_detail = (
        "Fixed once a debit is created"
        if editing
        else "Money put aside rather than spent. Can't be changed later"
    )

    return ft.Column(
        width=380,
        tight=True,
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            name,
            amount,
            ft.Column([theme.label("Collected"), frequency], spacing=8),
            date_field,
            _setting_row("Savings", savings_detail, is_savings),
            _setting_row("Active", "Inactive debits can't be ticked off in a month", is_active),
            add_another,
            ft.FilledButton(
                "Save changes" if editing else "Save debit",
                icon=ft.Icons.SAVE,
                on_click=save,
                height=44,
            ),
        ],
    )
