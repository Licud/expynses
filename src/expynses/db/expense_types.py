from ._engine import get_session
from ._models import ExpenseType
from sqlalchemy import select
from collections.abc import Iterable
from expynses.contracts.expenses_types import ExpenseTypeDto


def list_expense_types() -> Iterable[ExpenseTypeDto]:

    with get_session() as session:
        expense_types = session.scalars(select(ExpenseType)).all()

    return [
        ExpenseTypeDto(id=et.id, name=et.name) 
        for et in expense_types
    ]