import uuid
from decimal import Decimal

from ._engine import get_session
from ._models import CreditPayment

from sqlalchemy import func, select, delete, extract
from collections.abc import Iterable

from expynses.contracts.credit_payments import CreditPaymentDto, CreditPaymentFilterDto, NewCreditPaymentDto
from expynses.contracts.totals import MonthTotalDto


def add_credit_payment(
    new_credit_payment: NewCreditPaymentDto
) -> uuid.UUID:
    
    amount_pence=round(new_credit_payment.amount * 100)

    credit_payment = CreditPayment(
        date=new_credit_payment.date,
        amount_pence=amount_pence,
        is_external=new_credit_payment.is_external
    )

    with get_session() as session:
        session.add(credit_payment)
        session.commit()
        return credit_payment.id


def list_credit_payments(filter: CreditPaymentFilterDto) -> Iterable[CreditPaymentDto]:

    with get_session() as session:
        query = select(CreditPayment)

        if filter.from_date is not None:
            query = query.where(CreditPayment.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(CreditPayment.date <= filter.to_date)
        if filter.id is not None:
            query = query.where(CreditPayment.id == filter.id)
        if filter.is_external is not None:
            query = query.where(CreditPayment.is_external == filter.is_external)

        query = query.order_by(CreditPayment.date.desc())
        credit_payments = session.scalars(query).all()

    return [
        CreditPaymentDto(
            id=credit_payment.id,
            date=credit_payment.date,
            amount=Decimal(credit_payment.amount_pence) / 100,
            is_external=credit_payment.is_external
        ) for credit_payment in credit_payments
    ]


def total_credit_payments(filter: CreditPaymentFilterDto) -> Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(CreditPayment.amount_pence), 0))

        if filter.from_date is not None:
            query = query.where(CreditPayment.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(CreditPayment.date <= filter.to_date)
        if filter.id is not None:
            query = query.where(CreditPayment.id == filter.id)
        if filter.is_external is not None:
            query = query.where(CreditPayment.is_external == filter.is_external)

        total = session.scalars(query).one()

    return Decimal(total) / 100


def delete_credit_payment(id: uuid.UUID):

    with get_session() as session:
        session.execute(delete(CreditPayment).where(CreditPayment.id == id))
        session.commit()


def total_year_credit_payments(year: int, is_external: bool | None = None) -> Iterable[MonthTotalDto]:

    with get_session() as session:
        month = extract("month", CreditPayment.date).label("month")


        query = (
            select(month, func.coalesce(func.sum(CreditPayment.amount_pence), 0).label("total"))
            .where(extract("year", CreditPayment.date) == year)   
        )
        
        if is_external is not None:
            query = query.where(CreditPayment.is_external == is_external)

        query = query.group_by(month).order_by(month)

        rows = session.execute(query).all()

    totals = {}

    for row in rows:
        totals[row.month] = row.total

    for month in range(1, 13):
        total_as_decimal = Decimal(totals.get(month, 0)) / 100
        yield MonthTotalDto(month=month, total=total_as_decimal)
