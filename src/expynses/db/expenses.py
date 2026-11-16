import datetime
import decimal
import uuid

from collections.abc import Iterable

from sqlalchemy import select

from expynses.contracts.expenses import ExpenseDto
from expynses.contracts.expenses import ExpenseFilterDto
from expynses.db.expense_types import list_expense_types

from ._engine import get_session
from ._models import Expense


def add_expense(
    date: datetime.date,
    price: decimal.Decimal,
    notes: str,
    is_credit: bool,
    expense_type_id: uuid.UUID,
) -> uuid.UUID:
    
    price_pence=round(price * 100)

    expense = Expense(
        date=date,
        price_pence=price_pence,
        notes=notes,
        is_credit=is_credit,
        expense_type_id=expense_type_id,
    )

    with get_session() as session:
        session.add(expense)
        session.commit()
        return expense.id


def list_expenses(filter: ExpenseFilterDto) -> Iterable[ExpenseDto]:

    with get_session() as session:
        query = select(Expense)
        
        if filter.id is not None:
            query = query.where(Expense.id == filter.id)
        if filter.from_date is not None:
            query = query.where(Expense.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(Expense.date <= filter.to_date)

        query = query.order_by(Expense.date.desc())
        expenses = session.scalars(query).all()

    types_by_id = {et.id: et for et in list_expense_types()}

    return [
        ExpenseDto(
            id=expense.id,
            date=expense.date,
            price=decimal.Decimal(expense.price_pence) / 100,
            notes=expense.notes,
            is_credit=expense.is_credit,
            expense_type=types_by_id[expense.expense_type_id],
        )
        for expense in expenses
    ]