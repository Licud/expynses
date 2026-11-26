import datetime
import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = "expenses"
    expense_type: Mapped[ExpenseType] = relationship()

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


class CreditPayment(Base):
    __tablename__ = "credit_payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    date: Mapped[datetime.date]
    amount_pence: Mapped[int]
    is_external: Mapped[bool]


class DebitFrequency(Base):
    __tablename__ = "debit_frequencies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]


class DebitTemplate(Base):
    __tablename__ = "debit_templates"
    frequency: Mapped[DebitFrequency] = relationship()

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    date: Mapped[datetime.date]
    amount_pence: Mapped[int]
    frequency_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("debit_frequencies.id"))
    is_savings: Mapped[bool]
    is_active: Mapped[bool]


class DebitPayment(Base):
    __tablename__ = "debit_payments"
    __table_args__ = (UniqueConstraint("template_id", "date"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    date: Mapped[datetime.date]
    amount_pence: Mapped[int]
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("debit_templates.id"))
