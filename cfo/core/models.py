"""Core data models."""

from datetime import datetime
from pydantic import BaseModel, Field


VALID_PERIODS = ("monthly", "quarterly", "annual")
VALID_CURRENCIES = ("EUR", "USD", "GBP", "CHF", "CAD", "AUD", "JPY")


class BudgetLine(BaseModel):
    id: int | None = None
    budget_id: int | None = None
    category: str
    amount: float = Field(gt=0)
    currency: str = "EUR"
    created_at: datetime | None = None


class Budget(BaseModel):
    id: int | None = None
    name: str
    period: str = "monthly"
    lines: list[BudgetLine] = []
    created_at: datetime | None = None

    @property
    def total(self) -> dict[str, float]:
        """Return total amounts grouped by currency."""
        totals: dict[str, float] = {}
        for line in self.lines:
            totals[line.currency] = totals.get(line.currency, 0.0) + line.amount
        return totals


class Expense(BaseModel):
    id: int | None = None
    budget_id: int | None = None
    category: str
    amount: float = Field(gt=0)
    currency: str = "EUR"
    date: str
    note: str | None = None
    created_at: datetime | None = None
