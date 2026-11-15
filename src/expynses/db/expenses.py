import datetime
import decimal
import uuid

from ._engine import get_session
from ._models import Expense


def add_expense(
    date: datetime.date,
    price: decimal.Decimal,
    notes: str,
    is_credit: bool,
    expense_type_id: uuid.UUID,
) -> uuid.UUID:
    
    price_pence=round(price * 100)

    expense = Expense(
        date=date,
        price_pence=price_pence,
        notes=notes,
        is_credit=is_credit,
        expense_type_id=expense_type_id,
    )

    with get_session() as session:
        session.add(expense)
        session.commit()
        return expense.id