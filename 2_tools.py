
"""
Tools available to our M&A agent.
"""


def calculate_equity_value(
    enterprise_value: float,
    debt: float,
    cash: float
) -> float:
    """
    Calculate equity value using EV - debt + cash.

    All values must use the same currency and units.
    Assumes no other equity bridge adjustments.
    """
    return enterprise_value - debt + cash
