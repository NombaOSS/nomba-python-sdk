from __future__ import annotations

from nomba.lib.paginate import paginate


def test_paginate_yields_items_across_pages():
    pages = [(["a", "b"], "cursor2"), (["c"], None)]

    def fetch_page(cursor):
        return pages.pop(0)

    assert list(paginate(fetch_page)) == ["a", "b", "c"]


def test_paginate_passes_cursor_through():
    seen_cursors = []
    pages = [(["a"], "c2"), (["b"], "c3"), (["c"], None)]

    def fetch_page(cursor):
        seen_cursors.append(cursor)
        return pages.pop(0)

    assert list(paginate(fetch_page)) == ["a", "b", "c"]
    assert seen_cursors == [None, "c2", "c3"]


def test_paginate_single_page():
    def fetch_page(cursor):
        return (["only"], None)

    assert list(paginate(fetch_page)) == ["only"]


def test_paginate_is_lazy():
    calls = {"n": 0}
    pages = [(["a"], "c2"), (["b"], None), (["unreachable"], None)]

    def fetch_page(cursor):
        calls["n"] += 1
        return pages.pop(0)

    gen = paginate(fetch_page)
    assert calls["n"] == 0
    first = next(gen)
    assert first == "a"
    assert calls["n"] == 1
