# Releasing

Every push to `main` runs CI and works out the next SemVer version from the Conventional Commit PR titles since the last tag. Nothing is committed back to `main` — the git tag is the source of truth, and `version` in `pyproject.toml` stays at `0.0.0`.

## Steps

1. Merge a PR to `main` with a [Conventional Commits](https://www.conventionalcommits.org) title (`feat:`, `fix:`, `feat!:`, etc.) — enforced by the `pr-title` check.
2. The **Release** workflow computes the next version, builds the sdist and wheel, and checks the wheel installs and imports.
3. A release manager other than whoever merged approves the `pypi` environment.
4. The workflow uploads to PyPI with trusted publishing and attestations, then tags the commit `v<version>` and creates the GitHub Release with auto-generated notes.

## Choosing the version

| PR title prefix                                                       | Bump                         |
| --------------------------------------------------------------------- | ---------------------------- |
| `feat:`                                                               | Minor                        |
| `fix:`, `perf:`, `revert:`                                            | Patch                        |
| `feat!:` (or any `!:` / breaking)                                     | Major (minor while on `0.x`) |
| anything else (`docs:`, `chore:`, `ci:`, `style:`, `test:`, `build:`) | No release                   |

Only the PR title counts — `BREAKING CHANGE:` footers in commit messages are ignored. With no `v*` tag yet, the first release is `0.2.0`, after the `nomba` 0.1.x releases from the earlier SDK.

## After publishing

If a run uploaded a version but failed to tag it, create the `v<version>` GitHub Release on the commit it was built from, then re-run the workflow.

## One-time setup (repo owner)

- `pypi` environment in GitHub Actions, with a PyPI trusted publisher for `nomba` pointing at this repository, `release.yml` and the `pypi` environment.
