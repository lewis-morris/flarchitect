# Repository Guidelines

## Project Structure & Module Organization
- Source: `flarchitect/` (core, authentication, database, schemas, specs, utils, graphql, html).
- Tests: `tests/` (pytest suite). Keep new tests alongside related features.
- Docs & demos: `docs/`, `demo/` (runnable examples and reference snippets).
- Packaging & config: `pyproject.toml` (build, lint, test), `uv.lock`, `LICENSE`, `README.md`.
- Build outputs: `dist/`, coverage: `htmlcov/` (generated).

## Build, Test, and Development Commands
- Setup env: `python -m venv venv && source venv/bin/activate && pip install -e .[dev]`
- Lint/format: `ruff --fix .` (configured via `[tool.ruff]`).
- Run tests (quiet): `pytest -q`
- Filter tests: `pytest -k name -q`
- Coverage: `pytest --cov=flarchitect --cov-report=term-missing`
- Build sdist/wheel: `python -m build` (uses Hatchling backend).

## Coding Style & Naming Conventions
- Python 3.10+, spaces for indent, line length 200, double quotes by default.
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Imports: sorted (ruff `I` rule). Keep public APIs stable under `flarchitect/__init__.py`.
- Avoid logic in module top‑level; prefer functions/classes and explicit exports.

## Testing Guidelines
- Framework: `pytest` (+ `pytest-cov`). Test files: `tests/test_*.py`; test functions: `test_*`.
- JWT tests require env: `export ACCESS_SECRET_KEY=access; export REFRESH_SECRET_KEY=refresh`.
- Aim to cover new code paths and error handling; add fixtures to `tests/conftest.py` when reusable.

## Commit & Pull Request Guidelines
- Use Conventional Commits (parsed by semantic‑release):
  - Examples: `feat: add rate limit helpers`, `fix(auth): prevent token leak`, `docs: clarify quickstart`.
- PRs must include: clear summary, rationale, linked issues, test updates, and any docs/demo updates.
- Before pushing: `ruff --fix . && pytest`; for releases, the CI handles tagging/publishing from `master`.

## Security & Configuration Tips
- Never commit secrets. Use environment variables for keys/tokens (see README).
- Keep HTTP error handling consistent via helpers in `flarchitect.exceptions` and `flarchitect.utils`.

