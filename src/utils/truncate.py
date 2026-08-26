from typing import Any


def truncate(value: Any, max_len: int = 500) -> str:
    s = str(value)
    return s[:max_len] + ('...' if len(s) > max_len else '')
