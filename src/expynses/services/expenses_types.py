
from collections.abc import Iterable

import expynses.db.expense_types as db_expense_types

from expynses.contracts.expenses_types import ExpenseTypeDto

def get_expense_types() -> Iterable[ExpenseTypeDto]:
    return db_expense_types.list_expense_types()