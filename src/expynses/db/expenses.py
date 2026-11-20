import decimal
import uuid

from collections.abc import Iterable

from sqlalchemy import func, select

from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto, NewExpenseDto
from expynses.db.expense_types import list_expense_types

from ._engine import get_session
from ._models import Expense


def add_expense(
    new_expense: NewExpenseDto
) -> uuid.UUID:
    
    price_pence=round(new_expense.price * 100)

    expense = Expense(
        date=new_expense.date,
        price_pence=price_pence,
        notes=new_expense.notes,
        is_credit=new_expense.is_credit,
        expense_type_id=new_expense.expense_type_id,
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
        if filter.is_credit is not None:
            query = query.where(Expense.is_credit == filter.is_credit)

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


def total_expenses(filter: ExpenseFilterDto) -> decimal.Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(Expense.price_pence), 0))

        if filter.from_date is not None:
            query = query.where(Expense.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(Expense.date <= filter.to_date)
        if filter.is_credit is not None:
            query = query.where(Expense.is_credit == filter.is_credit)

        total = session.scalars(query).one()

    return decimal.Decimal(total) / 100