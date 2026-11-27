
from collections.abc import Iterable

from expynses.contracts.credit_payments import CreditPaymentFilterDto
from expynses.contracts.totals import MonthFiguresDto
from decimal import Decimal
from datetime import date

import calendar
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


def credit_balance(to_date: date | None = None) -> Decimal:

    expenses_filter = expense_contracts.ExpenseFilterDto(is_credit=True, to_date=to_date)

    expenses = db_expenses.total_expenses(expenses_filter)

    credit_payments_filter = CreditPaymentFilterDto(to_date=to_date)
    
    total_credit_payments = db_credit_payments.total_credit_payments(filter=credit_payments_filter)

    return expenses - total_credit_payments


def balance(to_date: date | None = None) -> Decimal:

    income = db_incomes.total_income(income_contracts.IncomeFilterDto(to_date=to_date))

    paid = db_expenses.total_expenses(expense_contracts.ExpenseFilterDto(is_credit=False, to_date=to_date))

    repaid = db_credit_payments.total_credit_payments(credit_payments_contracts.CreditPaymentFilterDto(to_date=to_date, is_external=False))

    debit_payments = db_debit_payments.total_debit_payments(debit_payment_contracts.DebitPaymentFilterDto(to_date=to_date))
    
    return income - paid - repaid - debit_payments


def monthly_figures(year: int) -> Iterable[MonthFiguresDto]:

    monthly_figures = []

    end_of_last_year = date(year - 1, 12, 31)
    running_balance = balance(to_date=end_of_last_year)
    running_owed = credit_balance(to_date=end_of_last_year)

    incomes_by_month = db_incomes.total_year_income(year)
    income = {i.month: i.total for i in incomes_by_month}

    paid_expenses_by_month = db_expenses.total_year_expenses(year, is_credit=False)
    paid_expenses = {i.month: i.total for i in paid_expenses_by_month}

    credit_expenses_by_month = db_expenses.total_year_expenses(year, is_credit=True)
    credit_expenses = {i.month: i.total for i in credit_expenses_by_month}

    all_credit_payments_by_month = db_credit_payments.total_year_credit_payments(year)
    all_credit_payments = {i.month: i.total for i in all_credit_payments_by_month}

    own_credit_payments_by_month = db_credit_payments.total_year_credit_payments(year, is_external=False)
    own_credit_payments = {i.month: i.total for i in own_credit_payments_by_month}

    debits_by_month = db_debit_payments.total_year_debit_payments(year)
    debits = {i.month: i.total for i in debits_by_month}

    for month in range(1, 13):

        first_day_of_month_date=date(year, month, 1)

        running_balance += income[month] - paid_expenses[month] - own_credit_payments[month] - debits[month]
        running_owed += credit_expenses[month] - all_credit_payments[month]

        is_future = first_day_of_month_date > date.today()

        figures = MonthFiguresDto(
            month=month,
            income=income[month],
            paid=paid_expenses[month],
            on_credit=credit_expenses[month],
            card_repaid=own_credit_payments[month],
            debits=debits[month],
            balance=None if is_future else running_balance,
            card_owed=None if is_future else running_owed,
        )

        monthly_figures.append(figures)

    return monthly_figures


def left_to_spend_for_month(month_date: date) -> Decimal:
    last_day_index = 1
    last_day=calendar.monthrange(month_date.year, month_date.month)[last_day_index]
    last_day_of_month = date(month_date.year, month_date.month, last_day) 

    income_filter=income_contracts.IncomeFilterDto(to_date=last_day_of_month)
    income_total=db_incomes.total_income(filter=income_filter)

    expense_filter=expense_contracts.ExpenseFilterDto(to_date=last_day_of_month, is_credit=False)
    expense_total=db_expenses.total_expenses(filter=expense_filter)

    debit_payments_filter=debit_payment_contracts.DebitPaymentFilterDto(to_date=last_day_of_month)
    debit_total=db_debit_payments.total_debit_payments(debit_payments_filter)

    credit_payments_filter=credit_payments_contracts.CreditPaymentFilterDto(
        to_date=last_day_of_month,
        is_external=False
    )
    credit_payments_total=db_credit_payments.total_credit_payments(credit_payments_filter)

    return income_total - expense_total - debit_total - credit_payments_total