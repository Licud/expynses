import datetime
import decimal
import uuid

from collections.abc import Callable

import flet as ft

from expynses.contracts.expenses import NewExpenseDto
from expynses.services.expenses import add_expense
from expynses.services.expenses_types import get_expense_types


DATE_FORMAT = "%d-%m-%Y"  # dd-MM-yyyy
TOAST_WIDTH = 300


def show_toast(page: ft.Page, message: str) -> None:
    """A floating notification in the bottom-right corner."""
    # A floating SnackBar is centred by default; a left margin pushes it right.
    left = max((page.width or 0) - TOAST_WIDTH - 24, 0)
    page.show_dialog(
        ft.SnackBar(
            ft.Text(message),
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin.only(left=left, right=24, bottom=24),
            duration=3000,
        )
    )


def expense_form(
    page: ft.Page, on_saved: Callable[[], None] | None = None
) -> ft.Control:
    """The 'add expense' form. Calls on_saved after an expense is stored."""

    # --- The input controls ---
    date_field = ft.TextField(
        label="Date",
        value=datetime.date.today().strftime(DATE_FORMAT),
        read_only=True,
        suffix_icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda: pick_date(),
    )
    price = ft.TextField(label="Price", prefix="£", keyboard_type=ft.KeyboardType.NUMBER)
    notes = ft.TextField(label="Notes", multiline=True)
    is_credit = ft.Checkbox(label="Paid by credit card")
    expense_type = ft.Dropdown(
        label="Type",
        options=[
            ft.DropdownOption(key=str(et.id), text=et.name)
            for et in get_expense_types()
        ],
    )

    # --- The date picker pop-up ---
    def date_picked():
        if date_picker.value is None:
            return
        date_field.value = date_picker.value.strftime(DATE_FORMAT)
        page.update()

    date_picker = ft.DatePicker(value=datetime.date.today(), on_change=date_picked)

    def pick_date():
        page.show_dialog(date_picker)

    # --- The Save button ---
    def save():
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

        # Reset the form for the next entry.
        price.value = ""
        notes.value = ""
        is_credit.value = False
        expense_type.value = None
        show_toast(page, "Expense saved")
        page.update()
        if on_saved is not None:
            on_saved()

    # --- Layout: everything stacked top to bottom ---
    return ft.Column(
        width=400,
        controls=[
            ft.Text("Add expense", size=24),
            date_field,
            price,
            expense_type,
            notes,
            is_credit,
            ft.Button("Save", on_click=save),
        ],
    )
