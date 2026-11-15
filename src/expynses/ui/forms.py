import datetime

import flet as ft

# Placeholder list until the form reads expense types from the database.
EXPENSE_TYPES = ["Food", "Transport", "Bills", "Other"]


def expense_form(page: ft.Page) -> ft.Control:
    """The 'add expense' form. It doesn't save anything yet."""

    # --- The input controls ---
    date_text = ft.Text(datetime.date.today().isoformat())
    price = ft.TextField(label="Price", prefix="£", keyboard_type=ft.KeyboardType.NUMBER)
    notes = ft.TextField(label="Notes", multiline=True)
    is_credit = ft.Checkbox(label="This is money coming in (credit)")
    expense_type = ft.Dropdown(
        label="Type",
        options=[ft.DropdownOption(key=name, text=name) for name in EXPENSE_TYPES],
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
        summary = f"{date_text.value} | £{price.value} | {expense_type.value} | {notes.value}"
        page.show_dialog(ft.SnackBar(ft.Text(f"Not saved yet: {summary}")))

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
