"""Lazy cursor-based pagination, ported from Node's ``src/lib/paginate.ts``."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TypeVar

T = TypeVar("T")


def paginate[T](
    fetch_page: Callable[[str | None], tuple[list[T], str | None]],
) -> Iterator[T]:
    """Yield items across every page of a cursor-paginated endpoint.

    Fetches one page at a time with the cursor the previous page returned,
    yields its items, and stops once a page returns no next cursor — never
    fetching a page that isn't needed.

    Args:
        fetch_page: Called with the current cursor (``None`` for the first
            page) and returning ``(items, next_cursor)``. ``next_cursor``
            should be falsy on the last page.

    Yields:
        Each item from each page, in order.
    """
    cursor: str | None = None
    while True:
        items, cursor = fetch_page(cursor)
        yield from items
        if not cursor:
            break
