
from typing import Iterable

from ._engine import get_session
from ._models import Income

from sqlalchemy import func, select, delete, extract

from expynses.contracts.incomes import IncomeDto, IncomeFilterDto, NewIncomeDto
from expynses.contracts.totals import MonthTotalDto

from decimal import Decimal
import uuid



def add_income(
    new_income: NewIncomeDto
) -> uuid.UUID:
    
    amount_pence=round(new_income.amount * 100)

    income = Income(
        date=new_income.date,
        amount_pence=amount_pence,
        source=new_income.source,
    )

    with get_session() as session:
        session.add(income)
        session.commit()
        return income.id


def list_incomes(filter: IncomeFilterDto) -> Iterable[IncomeDto]:

    with get_session() as session:
        query = select(Income)

        if filter.from_date is not None:
            query = query.where(Income.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(Income.date <= filter.to_date)
        if filter.take is not None:
            query = query.limit(filter.take)

        query = query.order_by(Income.date.desc())
        incomes = session.scalars(query).all()

    return [
        IncomeDto(
            id=income.id,
            date=income.date,
            amount=Decimal(income.amount_pence) / 100,
            source=income.source
        ) for income in incomes
    ]


def total_income(filter: IncomeFilterDto) -> Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(Income.amount_pence), 0))

        if filter.from_date is not None:
            query = query.where(Income.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(Income.date <= filter.to_date)
        if filter.take is not None:
            query = query.limit(filter.take)

        total = session.scalars(query).one()

    return Decimal(total) / 100


def delete_income(id: uuid.UUID):

    with get_session() as session:
        session.execute(delete(Income).where(Income.id == id))
        session.commit()


def total_year_income(year: int) -> Iterable[MonthTotalDto]:

    with get_session() as session:
        month = extract("month", Income.date).label("month")

        query = (
            select(month, func.coalesce(func.sum(Income.amount_pence), 0).label("total"))
            .where(extract("year", Income.date) == year)
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