
from expynses.contracts.credit_payments import CreditPaymentDto, CreditPaymentFilterDto, NewCreditPaymentDto

from collections.abc import Iterable

import expynses.db.credit_payments as db_credit_payments

import uuid

def add_credit_payment(new_payment: NewCreditPaymentDto) -> uuid.UUID:
    return db_credit_payments.add_credit_payment(new_payment)


def search_credit_payments(filter: CreditPaymentFilterDto) -> Iterable[CreditPaymentDto]:
    return db_credit_payments.list_credit_payments(filter=filter)


def delete_credit_payment(id: uuid.UUID):
    return db_credit_payments.delete_credit_payment(id=id)