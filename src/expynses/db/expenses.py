import uuid

from decimal import Decimal
from collections.abc import Iterable

from sqlalchemy import func, select, extract

from expynses.contracts.expenses import ExpenseDto, ExpenseFilterDto, NewExpenseDto
from expynses.db.expense_types import list_expense_types
from expynses.contracts.totals import MonthTotalDto

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
            price=Decimal(expense.price_pence) / 100,
            notes=expense.notes,
            is_credit=expense.is_credit,
            expense_type=types_by_id[expense.expense_type_id],
        )
        for expense in expenses
    ]


def total_expenses(filter: ExpenseFilterDto) -> Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(Expense.price_pence), 0))

        if filter.from_date is not None:
            query = query.where(Expense.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(Expense.date <= filter.to_date)
        if filter.is_credit is not None:
            query = query.where(Expense.is_credit == filter.is_credit)

        total = session.scalars(query).one()

    return Decimal(total) / 100


def total_year_expenses(year: int, is_credit: bool) -> Iterable[MonthTotalDto]:

    with get_session() as session:
        month = extract("month", Expense.date).label("month")

        query = (
            select(month, func.coalesce(func.sum(Expense.price_pence), 0).label("total"))
            .where(extract("year", Expense.date) == year, Expense.is_credit == is_credit)
            .group_by(month)
            .order_by(month)
        )

        rows = session.execute(query).all()

    totals = {}

    for row in rows:
        totals[row.month] = row.total

    for month in range(1, 13):
        total_as_decimal = Decimal(totals.get(month, 0)) / 100
        yield MonthTotalDto(month=month, total=total_as_decimal)