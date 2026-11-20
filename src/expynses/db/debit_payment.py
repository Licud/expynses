
import uuid
import decimal

from datetime import datetime

from collections.abc import Iterable
from sqlalchemy import func, select, extract

from expynses.contracts.debits import DebitPaymentDto, DebitPaymentFilterDto
from expynses.db._engine import get_session
from expynses.db._models import DebitPayment, DebitTemplate


def add_debit_payment(template_id: uuid.UUID, date: datetime) -> uuid.UUID:

    with get_session() as session:
        template = session.scalars(select(DebitTemplate).where(DebitTemplate.id == template_id)).one()

        date = date.replace(day=1)  # Normalize to the first of the month

        payment = DebitPayment(
            date=date,
            amount_pence=template.amount_pence,
            template_id=template.id
        )

        session.add(payment)
        session.commit()
        return payment.id


def delete_debit_payment(template_id: uuid.UUID, date: datetime):

    with get_session() as session:
        payment = session.scalars(select(DebitPayment).where(
            DebitPayment.template_id == template_id,
            extract("year", DebitPayment.date) == date.year,
            extract("month", DebitPayment.date) == date.month,
        )).one_or_none()

        if payment:
            session.delete(payment)
            session.commit()


def list_debit_payments(filter: DebitPaymentFilterDto) -> Iterable[DebitPaymentDto]:

    with get_session() as session:

        query = select(DebitPayment)

        if filter.id is not None:
            query = query.where(DebitPayment.id == filter.id)
        if filter.to_date is not None:
            query = query.where(DebitPayment.date <= filter.to_date)
        if filter.given_date is not None:
            query = query.where(
            extract("year", DebitPayment.date) == filter.given_date.year,
            extract("month", DebitPayment.date) == filter.given_date.month,
        )

        payments = session.scalars(query).all()

    return [
        DebitPaymentDto(
            id=payment.id,
            date=payment.date,
            amount=decimal.Decimal(payment.amount_pence) / 100,
            template_id=payment.template_id
        ) for payment in payments
    ]


def total_debit_payments(filter: DebitPaymentFilterDto) -> decimal.Decimal:

    with get_session() as session:
        query = select(func.coalesce(func.sum(DebitPayment.amount_pence), 0))

        if filter.id is not None:
            query = query.where(DebitPayment.id == filter.id)
        if filter.to_date is not None:
            query = query.where(DebitPayment.date <= filter.to_date)
        if filter.given_date is not None:
            query = query.where(
            extract("year", DebitPayment.date) == filter.given_date.year,
            extract("month", DebitPayment.date) == filter.given_date.month,
        )

        total = session.scalars(query).one()

    return decimal.Decimal(total) / 100
