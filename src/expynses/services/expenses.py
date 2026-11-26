import uuid

import expynses.db.expenses as db_expenses
import expynses.contracts.expenses as expense_contracts

from collections.abc import Iterable
from datetime import date


def add_expense(
    new_expense: expense_contracts.NewExpenseDto
) -> uuid.UUID:
    return db_expenses.add_expense(new_expense)


def search_expenses(
    filter: expense_contracts.ExpenseFilterDto
) -> Iterable[expense_contracts.ExpenseDto]:
    return db_expenses.list_expenses(filter=filter)


def spending_by_type(from_date: date, to_date: date) -> Iterable[expense_contracts.TypeMonthTotalDto]:
    filter = expense_contracts.ExpenseFilterDto(
        from_date=from_date,
        to_date=to_date)
    
    return db_expenses.total_expenses_by_type(filter=filter)