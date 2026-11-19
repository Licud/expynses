
import datetime

from expynses.contracts.credit_payments import CreditPaymentFilterDto

import expynses.contracts.incomes as income_contracts
import expynses.contracts.expenses as expense_contracts
import expynses.contracts.credit_payments as credit_payments_contracts

import expynses.db.incomes as db_incomes
import expynses.db.credit_payments as db_credit_payments
import expynses.db.expenses as db_expenses

import decimal
    

def total_income(
    filter: income_contracts.IncomeFilterDto
) -> decimal.Decimal:
    return db_incomes.total_income(filter=filter)


def total_credit_payments(filter: CreditPaymentFilterDto) -> decimal.Decimal:
    return db_credit_payments.total_credit_payments(filter=filter)


def credit_balance(to_date: datetime.date | None = None) -> decimal.Decimal:

    expenses_filter = expense_contracts.ExpenseFilterDto(is_credit=True, to_date=to_date)

    expenses = db_expenses.total_expenses(expenses_filter)

    credit_payments_filter = CreditPaymentFilterDto(to_date=to_date)
    
    total_credit_payments = db_credit_payments.total_credit_payments(filter=credit_payments_filter)

    return expenses - total_credit_payments


def balance(to_date: datetime.date | None = None) -> decimal.Decimal:

    income = db_incomes.total_income(income_contracts.IncomeFilterDto(to_date=to_date))

    paid = db_expenses.total_expenses(expense_contracts.ExpenseFilterDto(is_credit=False, to_date=to_date))

    repaid = db_credit_payments.total_credit_payments(credit_payments_contracts.CreditPaymentFilterDto(to_date=to_date))
    
    return income - paid - repaid