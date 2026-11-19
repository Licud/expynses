import uuid

import expynses.db.incomes as db_incomes
import expynses.contracts.incomes as income_contracts
import decimal

from collections.abc import Iterable

def add_income(
    new_income: income_contracts.NewIncomeDto
) -> uuid.UUID:
    return db_incomes.add_income(new_income)


def search_incomes(
    filter: income_contracts.IncomeFilterDto
) -> Iterable[income_contracts.IncomeDto]:
    return db_incomes.list_incomes(filter=filter)


def total_income(
    filter: income_contracts.IncomeFilterDto
) -> decimal.Decimal:
    return db_incomes.total_income(filter=filter)


def delete_income(id: uuid.UUID):
    return db_incomes.delete_income(id=id)