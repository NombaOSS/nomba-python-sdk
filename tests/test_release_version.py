from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_path = Path(__file__).parent.parent / "scripts" / "operations" / "release_version.py"
_spec = importlib.util.spec_from_file_location("release_version", _path)
assert _spec and _spec.loader
rv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rv)


@pytest.mark.parametrize(
    ("title", "ok"),
    [
        ("feat: add transfers", True),
        ("fix(auth): refresh expired token", True),
        ("feat!: drop Python 3.12", True),
        ("Update ci.yml", False),
        ("feature: nope", False),
        ("feat:missing space", False),
    ],
)
def test_check_title(title: str, ok: bool) -> None:
    assert (rv.parse_header(title) is not None) is ok


def test_first_release_follows_pypi_history() -> None:
    assert rv.next_version(None, []) == "0.2.0"


@pytest.mark.parametrize(
    ("last", "subjects", "expected"),
    [
        ("0.2.0", ["docs: x", "chore: y"], None),
        ("0.2.0", ["fix: x"], "0.2.1"),
        ("0.2.0", ["fix: x", "feat: y"], "0.3.0"),
        ("0.2.0", ["feat!: x"], "0.3.0"),
        ("1.2.3", ["feat!: x"], "2.0.0"),
        ("1.2.3", ["perf: x"], "1.2.4"),
    ],
)
def test_next_version(last: str, subjects: list[str], expected: str | None) -> None:
    assert rv.next_version(last, subjects) == expected
