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

## Versioning — IMPORTANT

The version is a static string in `pyproject.toml`, `neutronium/__init__.py`, and
`uv.lock`. It is **not** bumped automatically on merge. **When you open a PR you
must also bump the version**, otherwise no release is cut.

Bump it by running the **Bump Version** GitHub Actions workflow (it commits the
bump to `develop`):

```
gh workflow run "Bump Version" --ref develop -f bump_type=patch
```

Use `patch` unless a larger bump is explicitly called for (`minor` / `major`).

See the `create-merge-pr` skill in `.agents/skills/` for the full PR workflow.
