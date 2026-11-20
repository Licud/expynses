import uuid

import expynses.db.expenses as db_expenses

from collections.abc import Iterable
import expynses.contracts.expenses as expense_contracts

def add_expense(
    new_expense: expense_contracts.NewExpenseDto
) -> uuid.UUID:
    return db_expenses.add_expense(new_expense)


def search_expenses(
    filter: expense_contracts.ExpenseFilterDto
) -> Iterable[expense_contracts.ExpenseDto]:
    return db_expenses.list_expenses(filter=filter)
