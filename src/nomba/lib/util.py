"""Small helpers shared across domain modules.

Used from a domain's own file (e.g. ``nomba/accounts.py``) when building a
request path or response object — not meant to be imported by SDK users.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any, TypeVar
from urllib.parse import quote, urlencode

T = TypeVar("T")


def _path_id(v: str) -> str:
    """URL-encode a path segment, rejecting values that could escape it (empty, ``.``, ``..``)."""
    if not v or v in (".", ".."):
        raise ValueError(f"Invalid id {v!r}")
    return quote(v, safe="")


def _query(params: Mapping[str, Any]) -> str:
    """Build a ``?key=value&...`` query string like Node's transport: ``None`` is dropped,
    booleans are ``true``/``false``, and an empty ``cursor`` (last page) is not sent."""
    clean = {
        k: ("true" if v else "false") if isinstance(v, bool) else v
        for k, v in params.items()
        if v is not None and not (k == "cursor" and v == "")
    }
    return f"?{urlencode(clean)}" if clean else ""


def _build[T](cls: type[T], data: dict[str, Any]) -> T:
    """Construct a frozen dataclass from a response dict, ignoring unknown keys.

    Tolerates the API adding undocumented fields without breaking construction.
    """
    known = {f.name for f in dataclasses.fields(cls)}  # type: ignore[arg-type]
    return cls(**{k: v for k, v in data.items() if k in known})
