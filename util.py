"""Provide shared helpers for graph connections."""


def get_sorted_key(s1: str, s2: str) -> tuple[str, str]:
    """Return an order-independent key for two connection endpoints.

    Args:
        s1: First endpoint name.
        s2: Second endpoint name.

    Returns:
        Endpoint names sorted in ascending order.
    """
    first, second = sorted((s1, s2))
    return first, second
