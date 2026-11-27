"""Works out the next SemVer version from Conventional Commit subjects.

PRs are squash-merged with the PR title as the subject, and pr-title.yml checks
the title, so each commit on main carries one reviewed bump. Bodies are ignored.
Used by .github/workflows/release.yml (``next``) and pr-title.yml (``check-title``).
"""

from __future__ import annotations

import re
import subprocess
import sys

FIRST_VERSION = "0.2.0"

TYPES = (
    "feat",
    "fix",
    "perf",
    "refactor",
    "docs",
    "style",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)
HEADER = re.compile(r"^(\w+)(?:\([^()]+\))?(!)?: \S")
RANK = {"patch": 1, "minor": 2, "major": 3}
TAG = re.compile(r"^v\d+\.\d+\.\d+$")


def parse_header(header: str) -> tuple[str, bool] | None:
    match = HEADER.match(header)
    if not match or match.group(1) not in TYPES:
        return None
    return match.group(1), match.group(2) == "!"


def bump_for(subject: str) -> str | None:
    parsed = parse_header(subject)
    if parsed is None:
        return None
    kind, breaking = parsed
    if breaking:
        return "major"
    if kind == "feat":
        return "minor"
    if kind in ("fix", "perf", "revert"):
        return "patch"
    return None


def next_version(last_version: str | None, subjects: list[str]) -> str | None:
    if last_version is None:
        return FIRST_VERSION
    bump: str | None = None
    for subject in subjects:
        b = bump_for(subject)
        if b and (bump is None or RANK[b] > RANK[bump]):
            bump = b
    if bump is None:
        return None
    major, minor, patch = (int(p) for p in last_version.split("."))
    if bump == "major" and major == 0:
        bump = "minor"
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _last_tag() -> str | None:
    if _git("rev-parse", "--is-shallow-repository") == "true":
        raise SystemExit("Shallow clone: tags and history are incomplete.")
    tags = _git("tag", "--list", "--merged", "HEAD", "--sort=-v:refname", "v*")
    return next((t for t in tags.splitlines() if TAG.match(t)), None)


def main(argv: list[str]) -> int:
    command = argv[0] if argv else ""
    if command == "check-title":
        title = argv[1] if len(argv) > 1 else ""
        if parse_header(title) is None:
            print(
                f'PR title is not a Conventional Commit: "{title}"\n'
                'Use "<type>: <summary>", e.g. "feat: add transfers", '
                '"fix(auth): refresh expired token", "feat!: drop Python 3.12".\n'
                f"Types: {', '.join(TYPES)}",
                file=sys.stderr,
            )
            return 1
        return 0
    if command == "next":
        tag = _last_tag()
        subjects = (
            _git("log", "--format=%s", f"{tag}..HEAD").splitlines() if tag else []
        )
        print(next_version(tag[1:] if tag else None, subjects) or "")
        return 0
    print("Usage: release_version.py next | check-title <title>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
