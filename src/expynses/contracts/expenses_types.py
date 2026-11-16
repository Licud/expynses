
import uuid

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ExpenseTypeDto:
    id: uuid.UUID
    name: str