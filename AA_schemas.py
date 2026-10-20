
"""
Structured data models for our M&A agent.
"""

from pydantic import BaseModel


class Transaction(BaseModel):
    buyer: str | None
    target: str | None
    announcement_date: str | None
    transaction_value: str | None
    buy_side_advisor: str | None
    sell_side_advisor: str | None
