import flet as ft

# UI-only: which icon to show for each expense type, by name.
# Types missing from this list (e.g. ones the user creates later) get the default.
_ICONS_BY_TYPE_NAME = {
    "Eating Out": ft.Icons.RESTAURANT,
    "Grocery": ft.Icons.SHOPPING_CART,
    "Travel": ft.Icons.FLIGHT,
    "Games": ft.Icons.SPORTS_ESPORTS,
    "Bills": ft.Icons.RECEIPT_LONG,
    "Shopping": ft.Icons.SHOPPING_BAG,
    "Car": ft.Icons.DIRECTIONS_CAR,
    "Withdrawal": ft.Icons.ATM,
    "Other": ft.Icons.MORE_HORIZ,
}

_DEFAULT_ICON = ft.Icons.CATEGORY


def icon_for_type(name: str) -> ft.IconData:
    return _ICONS_BY_TYPE_NAME.get(name, _DEFAULT_ICON)
