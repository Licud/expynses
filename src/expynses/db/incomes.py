
from typing import Iterable

from ._engine import get_session
from ._models import Income

from sqlalchemy import func, select

from expynses.contracts.incomes import IncomeDto, IncomeFilterDto, NewIncomeDto
import decimal
import uuid


def add_income(
    new_income: NewIncomeDto
) -> uuid.UUID:
    
    price_pence=round(new_income.amount * 100)

    income = Income(
        date=new_income.date,
        price_pence=price_pence,
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
            amount=decimal.Decimal(income.amount_pence) / 100,
            source=income.source
        ) for income in incomes
    ]


def total_income(filter: IncomeFilterDto) -> decimal.Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(Income.amount_pence), 0))

        if filter.from_date is not None:
            query = query.where(Income.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(Income.date <= filter.to_date)
        if filter.take is not None:
            query = query.limit(filter.take)

        total = session.scalars(query).one()

    return decimal.Decimal(total) / 100