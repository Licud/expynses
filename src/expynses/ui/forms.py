import datetime
import decimal
import uuid

import flet as ft

from expynses.contracts.expenses import NewExpenseDto
from expynses.services.expenses import add_expense
from expynses.services.expenses_types import get_expense_types


def expense_form(page: ft.Page) -> ft.Control:
    """The 'add expense' form."""

    # --- The input controls ---
    date_text = ft.Text(datetime.date.today().isoformat())
    price = ft.TextField(label="Price", prefix="£", keyboard_type=ft.KeyboardType.NUMBER)
    notes = ft.TextField(label="Notes", multiline=True)
    is_credit = ft.Checkbox(label="This is money coming in (credit)")
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
        date_text.value = date_picker.value.strftime("%Y-%m-%d")
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
                date=datetime.date.fromisoformat(date_text.value),
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
        page.show_dialog(ft.SnackBar(ft.Text("Expense saved")))
        page.update()

    # --- Layout: everything stacked top to bottom ---
    return ft.Column(
        width=400,
        controls=[
            ft.Text("Add expense", size=24),
            ft.Row([ft.Button("Pick date", on_click=pick_date), date_text]),
            price,
            expense_type,
            notes,
            is_credit,
            ft.Button("Save", on_click=save),
        ],
    )
