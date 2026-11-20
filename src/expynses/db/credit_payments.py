
from ._engine import get_session
from ._models import CreditPayment

from sqlalchemy import func, select, delete
from collections.abc import Iterable

from expynses.contracts.credit_payments import CreditPaymentDto, CreditPaymentFilterDto, NewCreditPaymentDto
import decimal
import uuid


def add_credit_payment(
    new_credit_payment: NewCreditPaymentDto
) -> uuid.UUID:
    
    amount_pence=round(new_credit_payment.amount * 100)

    credit_payment = CreditPayment(
        date=new_credit_payment.date,
        amount_pence=amount_pence,
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

        query = query.order_by(CreditPayment.date.desc())
        credit_payments = session.scalars(query).all()

    return [
        CreditPaymentDto(
            id=credit_payment.id,
            date=credit_payment.date,
            amount=decimal.Decimal(credit_payment.amount_pence) / 100
        ) for credit_payment in credit_payments
    ]


def total_credit_payments(filter: CreditPaymentFilterDto) -> decimal.Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(CreditPayment.amount_pence), 0))

        if filter.from_date is not None:
            query = query.where(CreditPayment.date >= filter.from_date)
        if filter.to_date is not None:
            query = query.where(CreditPayment.date <= filter.to_date)
        if filter.id is not None:
            query = query.where(CreditPayment.id == filter.id)

        total = session.scalars(query).one()

    return decimal.Decimal(total) / 100


def delete_credit_payment(id: uuid.UUID):

    with get_session() as session:
        session.execute(delete(CreditPayment).where(CreditPayment.id == id))
        session.commit()