# neutronium — agent guide

Framework-agnostic Python utilities (text, time, iterables, structured logging,
telemetry primitives, and more). Pure-Python library published to PyPI.

## Repo shape

- Source: `neutronium/`
- Tests: `tests/` — run with `uv run --all-extras pytest`
- Lint + format: `uv run --all-extras ruff check neutronium/ tests/` and `ruff format --check neutronium/ tests/` (config in `pyproject.toml`)
- Default working branch: `develop`. Releases flow `develop` → `main`.

## Branching & releases

- `main` is protected: PRs only, and all checks must pass before merge.
- `develop` is the integration branch and is where version bumps land.
- Publishing to PyPI is automatic once a `develop` → `main` PR merges (a tag is
  cut from the version already in the files, then `publish.yml` ships it). The
  release workflow does **not** bump the version — it only reads it.

## Opening PRs & versioning

The version is a static string (`pyproject.toml`, `neutronium/__init__.py`,
`uv.lock`) and is **not** bumped automatically on merge — it must be bumped
deliberately, or no release is cut.

**Follow the `create-merge-pr` skill** (`.agents/skills/create-merge-pr/`) for the
full PR workflow, including when and how to bump the version.
