# Contributing to the Nomba Python SDK

Thanks for helping developers get to work quickly with Nomba's APIs. Every contribution must follow the rules below. Pull requests that break them will not be merged.

## The rules

### 1. Match the Nomba documentation exactly

The SDK is a faithful client for the official Nomba API docs.

- Endpoints, HTTP methods, headers, auth flows, request and response fields, types, required/optional flags, and error formats must match the docs.
- Never guess or invent API behavior. If the docs are unclear or silent, ask in the issue or PR before writing code.
- Link the relevant docs page in your PR description for every endpoint you add or change.

### 2. Keep it simple

The best code is the code never written.

- Add only what is needed now. No speculative abstractions, config for values that never change, or scaffolding "for later".
- Reuse existing helpers and patterns in this repo before writing new ones.
- Prefer the standard library and Python's standard library. Do not add a dependency for something a few lines can do.
- Mark deliberate shortcuts with a known limit using a `limit:` comment that names the limit and the upgrade path.

### 3. Test your changes

- Every behavior change comes with tests that fail if the logic breaks.
- Tests must assert against the documented request and response shapes, not against your own assumptions.
- All tests must pass before you open a PR.

### 4. Get a review

- Review your own diff before requesting review. Remove dead code, debug output, and unrelated changes.
- Every PR needs at least one approving review from a maintainer.
- Address review comments in the PR. Do not resolve a thread without a fix or a reply.

## Pull requests

- Keep each PR focused on one change.
- Describe what changed and why, and link the docs page(s) it follows.
- Use [Conventional Commits](https://www.conventionalcommits.org) for PR titles (`feat:`, `fix:`, `feat!:` for breaking changes, `docs:`, `chore:`). A required check enforces this. PRs are squash-merged, and every merge to `main` can release to PyPI: `feat` bumps the minor version, `fix`, `perf` and `revert` bump the patch version, and a breaking change (`!` in the PR title, e.g. `feat!:`) bumps the major version (the minor version while we're on 0.x). Only the PR title counts; `BREAKING CHANGE:` footers in commits are ignored. Other types don't release. Release notes are on GitHub Releases. Don't edit `version` in `pyproject.toml` or `__version__`; they stay at `0.0.0` and the release tag sets the published version.
- Requires Python 3.12 or newer (see `.python-version`). Code lives in `src/nomba/` and is type-checked with mypy in strict mode; lint and format with [Ruff](https://docs.astral.sh/ruff/). Tests use pytest, under `tests/`. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` and `uv run pytest` before pushing. CI runs the same.
- Layout: `src/nomba/http.py` and `src/nomba/lib/` are the unversioned shared core (transport, errors, outcomes, token store, webhooks, utilities). Everything else is split by Nomba API version: `src/nomba/v1/` and `src/nomba/v2/`, one package per API area, mirrored under `tests/`. Each service is exposed on the `Nomba` client (e.g. `client.transfers`).
- Never commit secrets, API keys, or real credentials, including in tests and examples.
- Update the README or usage docs if public behavior changes.
- **Safety invariants**: the retry/idempotency rules, redirect refusal, webhook signature comparison and path-id validation described in [SECURITY.md](SECURITY.md) live in `src/nomba/http.py` and `src/nomba/lib/`. Changes there need a CODEOWNERS review and must keep their tests passing.
