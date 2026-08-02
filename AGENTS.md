# AGENTS.md

`sob` is a type-enforced JSON serialization/deserialization library for
authoring introspective client-side data models, developed to support
[oapi](https://github.com/enorganic/oapi) (OpenAPI SDK generation).
Python ~=3.10, no runtime deps besides `iso8601` and `typing-extensions`.

## Commands

Everything runs through [hatch](https://hatch.pypa.io) (`pipx install hatch`):

- `make` — create all hatch environments (first-time setup)
- `make test` — lint check + mypy + full test matrix (slow)
- `hatch test` — tests only, current Python
- `hatch test -- tests/test_model.py` — single test file
- `make format` — ruff format + lint --fix + mypy (run before committing)
- `make refresh-test-data` — regenerate `tests/regression-data/` then test
- `make docs` — build & serve mkdocs site

## Layout

- `src/sob/` — the package. Key modules: `model.py` (Object/Array/Dictionary
  model classes, serialization), `properties.py` (property/type declarations),
  `meta.py` (model metadata), `abc.py` (abstract base classes declaring all
  public interfaces), `thesaurus.py` (infer models from example data),
  `hooks.py`, `errors.py`, `utilities.py`. Underscore-prefixed modules are
  internal.
- `tests/` — pytest; `tests/regression-data/` holds generated fixtures
  (excluded from lint).
- `docs/` — mkdocs-material + mkdocstrings; API pages map 1:1 to modules.

## Style & constraints

- Line length 79 (ruff, black-style formatting). Strict-ish mypy:
  all defs fully typed (`disallow_untyped_defs`).
- Doctests run in CI (`--doctest-modules`) — keep docstring examples valid,
  and wrap docstrings to 79 chars.
- When changing a public class/function signature, update the matching
  interface in `src/sob/abc.py` and the docs page under `docs/api/`.
- Support Python 3.10–3.13; avoid syntax/stdlib features newer than 3.10.

## Gotchas

- **Merging a `pyproject.toml` change to `main` triggers a PyPI release**
  (`distribute.yml` tags the version and publishes). Do not bump `version`
  unless a release is intended.
- CI (`test.yml`) runs `hatch fmt --check && hatch run mypy` plus the test
  matrix on Linux/macOS/Windows × 3.10–3.13.
- Dependency pins are managed with `dependence` via `make upgrade` /
  `make requirements` — don't hand-edit pinned versions.
