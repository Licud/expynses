import uuid

import expynses.db.incomes as db_incomes
import expynses.contracts.incomes as income_contracts

from collections.abc import Iterable

def add_income(
    new_income: income_contracts.NewIncomeDto
) -> uuid.UUID:
    return db_incomes.add_income(new_income)


def search_incomes(
    filter: income_contracts.IncomeFilterDto
) -> Iterable[income_contracts.IncomeDto]:
    return db_incomes.list_incomes(filter=filter)


def delete_income(id: uuid.UUID):
    return db_incomes.delete_income(id=id)