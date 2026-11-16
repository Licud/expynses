import uuid

import expynses.db.expenses as db_expenses

from expynses.contracts.expenses import NewExpenseDto

def add_expense(
    new_expense: NewExpenseDto
) -> uuid.UUID:
    return db_expenses.add_expense(
        date=new_expense.date,
        price=new_expense.price,
        notes=new_expense.notes,
        is_credit=new_expense.is_credit,
        expense_type_id=new_expense.expense_type_id,
    )