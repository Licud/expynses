
import uuid
import decimal

from sqlalchemy import select, delete

from expynses.contracts.debits import DebitTemplateDto, DebitTemplateFilterDto, Frequency, NewDebitTemplateDto, UpdateDebitTemplateDto
from expynses.db._engine import get_session

from collections.abc import Iterable

from expynses.db._models import DebitFrequency, DebitPayment, DebitTemplate

def add_debit_template(
    new_debit_template: NewDebitTemplateDto
) -> uuid.UUID:
    
    amount_pence=round(new_debit_template.amount * 100)

    with get_session() as session:
        frequency = session.scalars(
            select(DebitFrequency).where(DebitFrequency.name == new_debit_template.frequency.value)
        ).one()

        debit_template = DebitTemplate(
            date=new_debit_template.date,
            amount_pence=amount_pence,
            name=new_debit_template.name,
            frequency=frequency,
            is_savings=new_debit_template.is_savings,
            is_active=new_debit_template.is_active
        )

        session.add(debit_template)
        session.commit()
        return debit_template.id


def update_debit_template(
    id: uuid.UUID,
    updated_debit_template: UpdateDebitTemplateDto
) -> uuid.UUID:

    amount_pence=round(updated_debit_template.amount * 100)

    with get_session() as session:
        frequency = session.scalars(
            select(DebitFrequency).where(DebitFrequency.name == updated_debit_template.frequency.value)
        ).one()

        debit_template = session.scalars(
            select(DebitTemplate).where(DebitTemplate.id == id)
        ).one()

        debit_template.date = updated_debit_template.date
        debit_template.amount_pence = amount_pence
        debit_template.name = updated_debit_template.name
        debit_template.frequency = frequency
        debit_template.is_active = updated_debit_template.is_active
        
        session.commit()
        return debit_template.id


def list_debit_templates(filter: DebitTemplateFilterDto) -> Iterable[DebitTemplateDto]:

    with get_session() as session:
        query = select(DebitTemplate)

        if filter.id is not None:
            query = query.where(DebitTemplate.id == filter.id)
        if filter.is_active is not None:
            query = query.where(DebitTemplate.is_active == filter.is_active)

        query = query.order_by(DebitTemplate.date.desc())
        debit_templates = session.scalars(query).all()

        return [
            DebitTemplateDto(
                id=debit_template.id,
                date=debit_template.date,
                amount=decimal.Decimal(debit_template.amount_pence) / 100,
                name=debit_template.name,
                frequency=Frequency(debit_template.frequency.name),
                is_savings=debit_template.is_savings,
                is_active=debit_template.is_active
            ) for debit_template in debit_templates
    ]


def delete_debit_template(id: uuid.UUID):

    with get_session() as session:
        session.execute(delete(DebitPayment).where(DebitPayment.template_id == id))
        session.execute(delete(DebitTemplate).where(DebitTemplate.id == id))
        session.commit()