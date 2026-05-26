from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def get_path(value: Any, path: str) -> Any:
    current = value
    if path == "" or path is None:
        return current
    for part in path.split("."):
        current = _get_part(current, part)
    return current


def _get_part(current: Any, part: str) -> Any:
    if isinstance(current, dict):
        if part not in current:
            raise KeyError(part)
        return current[part]

    if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
        try:
            index = int(part)
        except ValueError as exc:
            raise KeyError(part) from exc
        return current[index]

    raise KeyError(part)

