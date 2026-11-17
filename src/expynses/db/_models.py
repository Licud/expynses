import datetime
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    date: Mapped[datetime.date]
    price_pence: Mapped[int] 
    notes: Mapped[str]
    is_credit: Mapped[bool]
    expense_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expense_types.id"))


class ExpenseType(Base):
    __tablename__ = "expense_types"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]


class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    date: Mapped[datetime.date]
    amount_pence: Mapped[int]
    source: Mapped[str]