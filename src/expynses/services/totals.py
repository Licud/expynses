
from collections.abc import Iterable

from expynses.contracts.credit_payments import CreditPaymentFilterDto
from expynses.contracts.totals import MonthFiguresDto
from decimal import Decimal

import calendar
import datetime
import expynses.contracts.incomes as income_contracts
import expynses.contracts.credit_payments as credit_payments_contracts
import expynses.contracts.expenses as expense_contracts
import expynses.contracts.debits as debit_payment_contracts

import expynses.db.incomes as db_incomes
import expynses.db.credit_payments as db_credit_payments
import expynses.db.expenses as db_expenses
import expynses.db.debit_payment as db_debit_payments

def total_income(
    filter: income_contracts.IncomeFilterDto
) -> Decimal:
    return db_incomes.total_income(filter=filter)


def total_credit_payments(filter: CreditPaymentFilterDto) -> Decimal:
    return db_credit_payments.total_credit_payments(filter=filter)


def total_debit_payments(filter: debit_payment_contracts.DebitPaymentFilterDto) -> Decimal:
    return db_debit_payments.total_debit_payments(filter)


def credit_balance(to_date: datetime.date | None = None) -> Decimal:

    expenses_filter = expense_contracts.ExpenseFilterDto(is_credit=True, to_date=to_date)

    expenses = db_expenses.total_expenses(expenses_filter)

    credit_payments_filter = CreditPaymentFilterDto(to_date=to_date)
    
    total_credit_payments = db_credit_payments.total_credit_payments(filter=credit_payments_filter)

    return expenses - total_credit_payments


def balance(to_date: datetime.date | None = None) -> Decimal:

    income = db_incomes.total_income(income_contracts.IncomeFilterDto(to_date=to_date))

    paid = db_expenses.total_expenses(expense_contracts.ExpenseFilterDto(is_credit=False, to_date=to_date))

    repaid = db_credit_payments.total_credit_payments(credit_payments_contracts.CreditPaymentFilterDto(to_date=to_date))

    debit_payments = db_debit_payments.total_debit_payments(debit_payment_contracts.DebitPaymentFilterDto(to_date=to_date))
    
    return income - paid - repaid - debit_payments


def monthly_figures(year: int) -> Iterable[MonthFiguresDto]:

    monthly_figures = []

    end_of_last_year = datetime.date(year - 1, 12, 31)
    running_balance = balance(to_date=end_of_last_year)
    running_owed = credit_balance(to_date=end_of_last_year)

    incomes_by_month = db_incomes.total_year_income(year)
    income = {i.month: i.total for i in incomes_by_month}

    paid_expenses_by_month = db_expenses.total_year_expenses(year, is_credit=False)
    paid_expenses = {i.month: i.total for i in paid_expenses_by_month}

    credit_expenses_by_month = db_expenses.total_year_expenses(year, is_credit=True)
    credit_expenses = {i.month: i.total for i in credit_expenses_by_month}

    credit_payments_by_month = db_credit_payments.total_year_credit_payments(year)
    credit_payments = {i.month: i.total for i in credit_payments_by_month}

    debits_by_month = db_debit_payments.total_year_debit_payments(year)
    debits = {i.month: i.total for i in debits_by_month}

    for month in range(1, 13):

        first_day_of_month_date=datetime.date(year, month, 1)

        running_balance += income[month] - paid_expenses[month] - credit_payments[month] - debits[month]
        running_owed += credit_expenses[month] - credit_payments[month]

        is_future = first_day_of_month_date > datetime.date.today()

        figures = MonthFiguresDto(
            month=month,
            income=income[month],
            paid=paid_expenses[month],
            on_credit=credit_expenses[month],
            card_repaid=credit_payments[month],
            debits=debits[month],
            balance=None if is_future else running_balance,
            card_owed=None if is_future else running_owed,
        )

        monthly_figures.append(figures)

    return monthly_figures