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


def format_path(from_: str, dest: str) -> str:
    """Return two path endpoints in the required movement format.

    Args:
        from_: Source zone name.
        dest: Destination zone name.

    Returns:
        Endpoints joined by a hyphen, such as ``start-goal``.
    """
    return f"{from_}-{dest}"


def format_drone_id(drone_id: int) -> str:
    """Return a drone identifier in the required output format.

    Args:
        drone_id: Numeric drone identifier.

    Returns:
        Identifier prefixed with ``D``, such as ``D1``.
    """
    return f"D{drone_id}"
