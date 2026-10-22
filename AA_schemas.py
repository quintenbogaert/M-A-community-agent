
"""
Shared data structures for our M&A AI agent.

Transaction: Structured information about an M&A deal.
SearchSource: Metadata about a retrieved source.
SearchResult: Standardized output of a search operation.
"""

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """
    Structured M&A transaction information.
    """

    buyer: str | None
    target: str | None
    announcement_date: str | None
    transaction_value: str | None
    buy_side_advisor: str | None
    sell_side_advisor: str | None



class SearchSource(BaseModel):
    """
    A source discovered during web research.
    """
    title: str | None = None
    url: str
    provider: str
    cited: bool = False


class SearchResult(BaseModel):
    """
    Standardized research result.
    """
    query: str
    provider: str
    answer: str

    # Sources cited in the final research answer
    sources: list[SearchSource] = Field(default_factory=list)

    # Additional sources encountered during searching
    consulted_sources: list[SearchSource] = Field(
        default_factory=list
    )

    search_events: int = 0

    # True when retrieved from our local database
    from_cache: bool = False
