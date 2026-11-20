import uuid

import expynses.db.debit_template as db_debit_templates
import expynses.db.debit_payment as db_debit_payments

import expynses.contracts.debits as debit_contracts

from collections.abc import Iterable
from datetime import datetime

def add_debit_payment(
    template_id: uuid.UUID,
    date: datetime
) -> uuid.UUID:
    return db_debit_payments.add_debit_payment(template_id, date)


def update_debit_template(
    template_id: uuid.UUID,
    update: db_debit_templates.UpdateDebitTemplateDto
) -> uuid.UUID:
    return db_debit_templates.update_debit_template(id=template_id, updated_debit_template=update)


def list_debit_payments(
    filter: debit_contracts.DebitPaymentFilterDto
) -> Iterable[debit_contracts.DebitPaymentDto]:
    return db_debit_payments.list_debit_payments(filter)


def delete_debit_payment(
    template_id: uuid.UUID,
    date: datetime
):
    return db_debit_payments.delete_debit_payment(template_id, date)


def add_debit_template(
    new_debit_template: debit_contracts.NewDebitTemplateDto
) -> uuid.UUID:
    return db_debit_templates.add_debit_template(new_debit_template)


def search_debit_templates(
    filter: debit_contracts.DebitTemplateFilterDto
) -> Iterable[debit_contracts.DebitTemplateDto]:
    return db_debit_templates.list_debit_templates(filter=filter)


def delete_debit_template(
    id: uuid.UUID
):
    return db_debit_templates.delete_debit_template(id=id)