# Close Remaining Test-Coverage Gaps in `sob` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise `src/sob`'s test coverage from 84% overall (45%/64% on the
two worst modules) to ≥95% overall / ≥90% per module, adding only real
integration tests (no mocks), per
`docs/superpowers/specs/2026-08-01-test-coverage-gaps-design.md`.

**Architecture:** No production behavior changes except two small bug
fixes (a stale docstring example, a Python-3.10-only datetime bug) needed
to make the doctest harness trustworthy. Every other task adds test
functions to the existing `tests/test_*.py` files, constructing real
`sob.Object`/`sob.Array`/`sob.Dictionary`/`sob.Property`/`sob.Meta`/
`sob.Hooks` instances and asserting on their real behavior — mirroring the
100%-mock-free style already used throughout `tests/`.

**Tech Stack:** Python 3.10 (dev)/3.10–3.13 (CI matrix), `hatch`, `pytest`,
`coverage.py` (via `hatch test --cover`), `mypy` (strict on `tests/` too).

## Global Constraints

- **No mocks.** Never import `unittest.mock` or `pytest-mock`; every
  assertion exercises a real, constructed `sob` object calling real code.
  (Source: spec §1/§6 — confirmed by `grep -rl "mock\|Mock\|monkeypatch"
  tests/ src/` returning nothing today.)
- **Line length 79** (ruff/black-style). Wrap docstrings to 79 chars too.
- **Full typing required in tests.** `pyproject.toml`'s `[tool.mypy]`
  applies `disallow_untyped_defs`/`disallow_incomplete_defs` to `tests/`
  as well as `src/` — every new `test_*` function needs a `-> None`
  return annotation and fully-typed locals, matching existing style.
- **Follow existing per-file conventions**: `from __future__ import
  annotations` at the top, plain `test_*` functions (no test classes),
  and an `if __name__ == "__main__": pytest.main([__file__, "-s",
  "-vv"])` trailer at the bottom of every test file touched.
- Run `make format` (ruff format + lint --fix + mypy) before every commit.
- Run `hatch test -- tests/test_<file>.py` for the specific file after
  each task, and `hatch test --cover` (or `hatch run hatch-test.py3.10:
  coverage report -m`) periodically to confirm the target lines listed in
  the spec are actually now covered.
- Do **not** touch `pyproject.toml`'s `version` field — merging a version
  bump to `main` triggers a real PyPI release (see `AGENTS.md`).
- If a task touches `get_models_source`/`get_model_from_meta` regression
  output or the `thesaurus` regression fixture, regenerate with `make
  refresh-test-data` rather than hand-editing golden files under
  `tests/regression-data/`.
- Skip the non-goals listed in spec §4 (abstract-method `pass` stubs,
  `TYPE_CHECKING`-only asserts, a few unreachable defensive guards in
  `get_models_source`) — do not write tests chasing them.

---

## Task 1: Fix the doctest harness and the two bugs it was hiding

**Files:**
- Modify: `tests/test_datetime.py`, `tests/test_io.py`, `tests/test_model.py`,
  `tests/test_thesaurus.py` (no doctest there — skip),
  `tests/test_types.py` (no `test_doctest` — skip), `tests/test_utilities.py`,
  `tests/test_version.py` — every file with a `test_doctest()` function.
- Modify: `src/sob/utilities.py` (docstring fix for `suffix_long_lines`),
  `src/sob/_datetime.py` (behavior fix for `str2datetime`).

**Interfaces:**
- Consumes: `doctest.testmod`.
- Produces: a `test_doctest()` pattern (`assert doctest.testmod(module,
  verbose=False).failed == 0`) that every subsequent task's module can
  rely on to actually fail if a docstring example is wrong.

- [ ] **Step 1: Confirm the two currently-failing doctests**

  Run:
  ```
  hatch run hatch-test.py3.10:python -m pytest -vv --doctest-modules \
    --ignore=.scratch.py src/sob/_datetime.py src/sob/utilities.py
  ```
  Confirm `sob.utilities.suffix_long_lines` and
  `sob._datetime.str2datetime` are the only two `FAILED` items.

- [ ] **Step 2: Change every `test_doctest()` to assert on the result**

  In each of `tests/test_datetime.py`, `tests/test_io.py`,
  `tests/test_model.py`, `tests/test_utilities.py`, `tests/test_version.py`,
  change:
  ```python
  def test_doctest() -> None:
      doctest.testmod(utilities)
  ```
  to:
  ```python
  def test_doctest() -> None:
      results: doctest.TestResults = doctest.testmod(utilities)
      assert results.failed == 0, results
  ```
  (substituting the correct module name per file). This step alone should
  now make `test_utilities.py::test_doctest` and
  `test_datetime.py::test_doctest` fail via `hatch test`.

- [ ] **Step 3: Run tests and confirm the two expected failures**

  `hatch test -- tests/test_utilities.py tests/test_datetime.py -vv` should
  show exactly 2 failures now (previously silently swallowed).

- [ ] **Step 4: Fix the `suffix_long_lines` docstring**

  Read `src/sob/utilities.py` around line 580 (the `suffix_long_lines`
  docstring example). The function correctly appends `# noqa: E501` to the
  wrapped long line; the docstring's expected output is stale (missing
  that suffix). Update the expected output in the docstring to match the
  function's real, correct behavior (do not change the function itself
  unless the *behavior*, not just the example, turns out to be wrong on
  inspection).

- [ ] **Step 5: Fix the `str2datetime` Python-3.10 `Z`-suffix bug**

  Read `src/sob/_datetime.py:46-74` (`str2datetime`). On Python 3.10,
  `datetime.fromisoformat` doesn't understand a trailing `Z`, so the
  function falls through to `iso8601.parse_date`, which returns a
  UTC-aware datetime — but the subsequent "iso8601 incorrectly sets the
  UTC offset to 0 instead of None" correction then strips tzinfo entirely,
  even though the original string explicitly ended in `Z` (meaning UTC,
  not "no timezone given"). Fix the condition so it only strips tzinfo
  when the string did **not** explicitly indicate a timezone (i.e., don't
  strip when the fallback was entered specifically because of a trailing
  `Z`) — the corrected behavior must return
  `datetime.datetime(2023, 10, 1, 12, 0, tzinfo=datetime.timezone.utc)`
  for `str2datetime("2023-10-01T12:00:00Z")` on every supported Python
  version (3.10–3.13), matching the module's own docstring.

- [ ] **Step 6: Run the full suite on Python 3.10 and confirm all doctests pass**

  ```
  hatch run hatch-test.py3.10:python -m pytest -vv --doctest-modules \
    --ignore=.scratch.py
  ```
  Expect `0 failed`. Then `hatch test -- -vv` (the asserted `test_doctest`
  functions) should also be green.

- [ ] **Step 7: Run `make format` and commit**

  Commit message should explain both the harness fix and the two
  behavioral fixes it uncovered, e.g. "Assert doctest results in
  test_doctest(); fix suffix_long_lines example and str2datetime Z-suffix
  handling on Python 3.10".

---

## Task 2: `_datetime.py` coverage (93% → 100%)

**Files:**
- Modify: `tests/test_datetime.py`

**Interfaces:**
- Consumes: `sob._datetime.str2datetime`, `sob._datetime.str2date`.

- [ ] **Step 1: Write the tests**

  Add, parallel to the existing `test_raise_str2date_type_error`:
  ```python
  def test_raise_str2datetime_type_error() -> None:
      error_caught: bool = False
      try:
          sob._datetime.str2datetime(123)  # type: ignore  # noqa: SLF001
      except TypeError:
          error_caught = True
      assert error_caught


  def test_raise_str2date_type_error_non_str() -> None:
      error_caught: bool = False
      try:
          sob._datetime.str2date(123)  # type: ignore  # noqa: SLF001
      except TypeError:
          error_caught = True
      assert error_caught
  ```
  (rename to avoid clashing with the existing `test_raise_str2date_type_error`,
  which currently tests a *different* input — check the existing test
  first and don't duplicate its name or intent).

- [ ] **Step 2: Run and confirm pass**

  `hatch test -- tests/test_datetime.py -vv`

- [ ] **Step 3: Confirm coverage**

  `hatch run hatch-test.py3.10:coverage report -m src/sob/_datetime.py`
  should show 100%.

- [ ] **Step 4: `make format` and commit**

---

## Task 3: `_io.py` coverage (79% → 100%)

**Files:**
- Modify: `tests/test_utilities.py` (it already has `test_io()` calling
  `doctest.testmod(_io)` — add a sibling test function alongside it).

**Interfaces:**
- Consumes: `sob._io.read`.

- [ ] **Step 1: Write the tests**

  ```python
  class UnsupportedReadProxy:
      def read(self) -> str:
          raise UnsupportedOperation

  class NotReadableProxy:
      pass

  def test_read_type_error() -> None:
      error_caught: bool = False
      try:
          _io.read(NotReadableProxy())  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught

  def test_read_unsupported_operation() -> None:
      error_caught: bool = False
      try:
          _io.read(UnsupportedReadProxy())  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught
  ```
  Add `from io import UnsupportedOperation` to the imports.

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_utilities.py -vv`
- [ ] **Step 3: Confirm coverage** — `_io.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 4: `_types.py` coverage (93% → 100%)

**Files:**
- Modify: `tests/test_types.py`

**Interfaces:**
- Consumes: `sob.UNDEFINED`, `sob.NULL`, `sob.Null._marshal`.

- [ ] **Step 1: Write the tests**

  Extend `test_undefined()`:
  ```python
  assert hash(sob.UNDEFINED) == 0
  ```
  Extend `test_null()`:
  ```python
  assert hash(sob.NULL) == 0
  assert str(sob.NULL) == "null"
  assert sob.Null._marshal() is None  # noqa: SLF001
  ```

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_types.py -vv`
- [ ] **Step 3: Confirm coverage** — `_types.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 5: `_utilities.py` coverage (89% → 100%)

**Files:**
- Modify: `tests/test_utilities.py`

**Interfaces:**
- Consumes: `sob._utilities.deprecated`, `sob._utilities.get_readable_url`.

- [ ] **Step 1: Write the tests**

  ```python
  def test_deprecated() -> None:
      @_utilities.deprecated("this is deprecated")
      def old_function(value: int) -> int:
          return value * 2

      with pytest.warns(DeprecationWarning, match="this is deprecated"):
          result: int = old_function(21)
      assert result == 42


  class URLNonStringProxy:
      url = 123


  class NoAttributesProxy:
      pass


  def test_get_readable_url_type_error() -> None:
      error_caught: bool = False
      try:
          get_readable_url(URLNonStringProxy())
      except TypeError:
          error_caught = True
      assert error_caught


  def test_get_readable_url_none() -> None:
      assert get_readable_url(NoAttributesProxy()) is None
  ```
  Import `_utilities` (module) alongside the existing
  `from sob._utilities import get_readable_url`.

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_utilities.py -vv`
- [ ] **Step 3: Confirm coverage** — `_utilities.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 6: `errors.py` coverage (88% → 100%)

**Files:**
- Modify: `tests/test_utilities.py` (or create `tests/test_errors.py` if
  it reads more clearly as its own file — prefer adding to
  `test_utilities.py` unless it grows unwieldy, per the plan's "don't
  fragment files" constraint).

**Interfaces:**
- Consumes: `sob.errors.DeserializeError`, `sob.errors.append_exception_text`.

- [ ] **Step 1: Write the tests**

  ```python
  def test_deserialize_error() -> None:
      error = sob.errors.DeserializeError(data="bad-data", message="oops")
      assert error.data == "bad-data"
      assert error.message == "oops"
      assert repr(error) == "oops\nCould not parse:\nbad-data"
      assert str(error) == repr(error)


  def test_append_exception_text_strerror() -> None:
      error = OSError(1, "boom")
      sob.errors.append_exception_text(error, " (more info)")
      assert error.strerror is not None
      assert error.strerror.endswith(" (more info)")


  def test_append_exception_text_no_string_arg() -> None:
      error = Exception()
      sob.errors.append_exception_text(error, "appended")
      assert error.args == ("appended",)
  ```

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_utilities.py -vv`
- [ ] **Step 3: Confirm coverage** — `errors.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 7: `types.py` coverage (81% → 100%)

**Files:**
- Modify: `tests/test_types.py`

**Interfaces:**
- Consumes: `sob.Types`, `sob.MutableTypes`.

- [ ] **Step 1: Write the tests**

  ```python
  def test_types_bare_type() -> None:
      types_ = sob.Types(str)
      assert list(types_) == [str]


  def test_types_copy() -> None:
      types_ = sob.Types([int, str])
      copied = copy(types_)
      assert copied is not types_
      assert list(copied) == list(types_)


  def test_mutable_types_protocol() -> None:
      types_: sob.MutableTypes = sob.MutableTypes([int, str])
      types_[0] = float
      assert types_[0] is float
      types_.extend([bool])
      assert bool in types_
      del types_[0]
      assert float not in types_
      types_ += [bytes]
      assert bytes in types_
      new_types = types_ + [complex]
      assert complex in new_types
      assert complex not in types_
  ```

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_types.py -vv`
- [ ] **Step 3: Confirm coverage** — `types.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 8: `properties.py` coverage (96% → 100%)

**Files:**
- Modify: `tests/test_model.py` (or a new `tests/test_properties.py` if
  the additions don't fit naturally near existing content).

**Interfaces:**
- Consumes: `sob.properties.has_mutable_types`, `sob.Property`,
  `sob.StringProperty`.

- [ ] **Step 1: Write the tests**

  ```python
  def test_has_mutable_types() -> None:
      assert sob.properties.has_mutable_types(sob.Property())
      assert not sob.properties.has_mutable_types(sob.StringProperty)
      error_caught = False
      try:
          sob.properties.has_mutable_types(object())  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught


  def test_property_types_immutable() -> None:
      string_property = sob.StringProperty()
      error_caught = False
      try:
          string_property.types = [int]  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught


  def test_property_types_invalid() -> None:
      property_ = sob.Property()
      error_caught = False
      try:
          property_.types = "not-a-type"  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught


  def test_property_versions_invalid() -> None:
      property_ = sob.Property()
      error_caught = False
      try:
          property_.versions = 123  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught
  ```

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_model.py -vv`
- [ ] **Step 3: Confirm coverage** — `properties.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 9: `version.py` coverage (80% → 100%)

**Files:**
- Modify: `tests/test_version.py`

**Interfaces:**
- Consumes: `sob.Version`, `sob.version._version_as_tuple` (module-internal,
  acceptable to import directly per spec §5.9).

- [ ] **Step 1: Write the tests**

  ```python
  def test_version_equality_precision() -> None:
      assert sob.Version(equals="1.2") == "1.2.0"
      assert sob.Version(equals="1.2") == "1.2"


  def test_version_string_value_error() -> None:
      error_caught = False
      try:
          sob.Version("not-a-version")
      except ValueError:
          error_caught = True
      assert error_caught


  def test_version_numeric_and_sequence_inputs() -> None:
      assert sob.Version(compatible_with=1.2) == "1.2"
      assert sob.Version(compatible_with=(1, 2)) == "1.2"


  def test_version_as_tuple_type_error() -> None:
      error_caught = False
      try:
          sob.version._version_as_tuple(object())  # type: ignore  # noqa: SLF001
      except TypeError:
          error_caught = True
      assert error_caught


  def test_version_string_type_error() -> None:
      error_caught = False
      try:
          sob.Version(123)  # type: ignore
      except TypeError:
          error_caught = True
      assert error_caught


  def test_version_conflicting_specifications() -> None:
      error_caught = False
      try:
          sob.Version("a==1,b==2")
      except ValueError:
          error_caught = True
      assert error_caught


  def test_version_str_no_specification() -> None:
      version = sob.Version(equals="1.0")
      version.specification = None  # type: ignore
      error_caught = False
      try:
          str(version)
      except RuntimeError:
          error_caught = True
      assert error_caught
  ```

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_version.py -vv`
- [ ] **Step 3: Confirm coverage** — `version.py` should show 100%.
- [ ] **Step 4: `make format` and commit**

---

## Task 10: `utilities.py` coverage (85% → ~97%)

**Files:**
- Modify: `tests/test_utilities.py`

**Interfaces:**
- Consumes: `sob.utilities.get_relative_url`, `_align_indent`,
  `_split_long_comment_line`, `split_long_docstring_lines`,
  `get_qualified_name`, `get_calling_module_name`,
  `get_calling_function_qualified_name`, `_repr_list`, `_repr_set`,
  `_repr_dict`, `represent`, `get_method` (several are private/underscore
  — import directly from `sob.utilities` as the unit under test, matching
  how `tests/test_utilities.py` already imports `_io`/`_types` directly).

- [ ] **Step 1: Write the tests**

  One test function per bullet in spec §5.10 — follow the exact
  scenarios listed there (malformed URL → `ValueError`; two URLs with no
  shared prefix for `get_relative_url`; `_align_indent` on a no-indent
  line; a short line through `_split_long_comment_line`; an
  already-uniform-indent docstring and one containing a `"""`/`'''`
  literal through `split_long_docstring_lines`; unsupported-type,
  generic-alias, and unresolvable-name cases for `get_qualified_name`;
  out-of-range and non-`int` `depth` for the calling-frame helpers; empty
  `list`/`set`/`dict` through `_repr_list`/`_repr_set`/`_repr_dict`;
  `represent` on a bare `type`; `get_method` with no `default` on a
  missing attribute, and with/without `default` on a non-callable
  attribute). Write these as small, focused `test_*` functions rather
  than one giant test.

- [ ] **Step 2: Run and confirm pass** — `hatch test -- tests/test_utilities.py -vv`
- [ ] **Step 3: Confirm coverage** — `utilities.py` should be ≥ 97%; check
  `coverage report -m` for any remaining lines and decide per spec §4
  whether they're a real gap or a non-goal.
- [ ] **Step 4: `make format` and commit**

---

## Task 11: `hooks.py` coverage (45% → ~90%+) — highest value

**Files:**
- Modify: `tests/test_model.py`, or create `tests/test_hooks.py` if it
  reads more clearly standalone (recommended, given this is the biggest
  net-new test surface in the plan — a dedicated file keeps
  `test_model.py` from growing unwieldy; if created, give it the same
  `from __future__ import annotations` / `if __name__ == "__main__"`
  structure as its siblings).

**Interfaces:**
- Consumes: `sob.ObjectHooks`, `sob.ArrayHooks`, `sob.DictionaryHooks`,
  `sob.write_model_hooks`, `sob.read_model_hooks`,
  `sob.get_writable_model_hooks`, `sob.get_writable_object_hooks`,
  `sob.get_writable_array_hooks`, `sob.get_writable_dictionary_hooks`,
  `sob.get_model_hooks_type`; real `ObjectA`/`ArrayA` classes from
  `tests/test_model.py` (import them if writing a separate file) or a
  small dedicated `Dictionary` subclass.

- [ ] **Step 1: Object hooks test**

  Build a real `Object` subclass, register `ObjectHooks(before_setattr=fn,
  after_setattr=fn)` via `sob.write_model_hooks`, set an attribute, and
  assert both real (plain-function, list-appending) callables fired with
  the arguments you expect.

- [ ] **Step 2: Array hooks test**

  Same pattern with `ArrayHooks(before_append=fn, after_append=fn)` on an
  `Array` subclass and `.append(...)`.

- [ ] **Step 3: Dictionary hooks test**

  Same pattern with `DictionaryHooks(before_setitem=fn, after_setitem=fn)`
  on a `Dictionary` subclass and `d["k"] = v`.

- [ ] **Step 4: `read_model_hooks` type-guard test**

  `sob.read_model_hooks("not-a-model")` → `TypeError`.

- [ ] **Step 5: `get_writable_*_hooks` tests**

  On a fresh class with no hooks assigned: `sob.get_writable_model_hooks
  (cls)` returns a new `ObjectHooks`/`ArrayHooks`/`DictionaryHooks`
  (assert type); a second call / `sob.read_model_hooks(cls)` returns the
  *same* object (idempotency); repeat on an instance; call
  `sob.get_writable_object_hooks`/`get_writable_array_hooks`/
  `get_writable_dictionary_hooks` directly on each container type; and
  `sob.get_writable_model_hooks(42)` → `TypeError`.

- [ ] **Step 6: `get_model_hooks_type` tests**

  Assert `ObjectHooks`/`ArrayHooks`/`DictionaryHooks` returned correctly
  for each container's class and instance; `sob.get_model_hooks_type(str)`
  → `TypeError`.

- [ ] **Step 7: `write_model_hooks` error-branch tests**

  `sob.write_model_hooks(object_cls, sob.ArrayHooks())` (wrong hooks type
  for that model) → `ValueError`; `sob.write_model_hooks("not-a-model",
  hooks)` → `TypeError`.

- [ ] **Step 8: Run and confirm pass**

  `hatch test -- tests/test_hooks.py -vv` (or `tests/test_model.py -vv`).

- [ ] **Step 9: Confirm coverage**

  `hooks.py` should reach ~90%+; check `coverage report -m src/sob/hooks.py`
  against the remaining line numbers in spec §5.11 and decide if any
  residual gap is worth a follow-up test.

- [ ] **Step 10: `make format` and commit**

---

## Task 12: `meta.py` coverage (79% → ~93%)

**Files:**
- Modify: `tests/test_model.py`, `tests/test_version.py`.

**Interfaces:**
- Consumes: `sob.get_writable_object_meta`, `sob.Properties`,
  `sob.read_model_meta`, `sob.write_model_meta`, `sob.meta.pointer`,
  `sob.meta.url`, `sob.meta.version_model`, `sob.meta._copy_model_meta_to`,
  `sob.meta._read_object_properties`, `sob.meta._read_object_property_names`.

- [ ] **Step 1: Bare-type property assignment tests**

  `DictionaryProperty(value_types=sob.StringProperty())` and
  `ArrayProperty(item_types=str)` (single, not wrapped in a list) —
  assert construction succeeds and the resulting `Types` contains the one
  item.

- [ ] **Step 2: `Properties` mapping-protocol tests**

  Using `sob.get_writable_object_meta(ObjectA).properties` (a real,
  already-populated `Properties`): `.pop(...)`, `.popitem()`,
  `.setdefault(...)` (valid and invalid-type cases), `.get("missing")`,
  `.clear()`, `copy.copy(...)`, `repr(...)`, equality between two
  independently-built `Properties` with identical items,
  `properties["bad"] = "not-a-property"` → `TypeError`, `.update({...})`.
  Take care to do this on a **copy** of `ObjectA`'s properties (or a
  freshly-declared test-only `Object` subclass) so mutating/clearing them
  doesn't break other tests that depend on `ObjectA`'s metadata.

- [ ] **Step 3: `read_model_meta`/`get_writable_model_meta` guard tests**

  A brand-new `Object` subclass with no metadata ever assigned →
  `sob.read_model_meta(NewClass)` is `None`; `sob.get_writable_object_meta
  ("not-a-model")` and `sob.get_writable_object_meta(int)` → `TypeError`.

- [ ] **Step 4: `write_model_meta` guard tests**

  `sob.write_model_meta(ObjectA, sob.ArrayMeta())` → `ValueError`;
  `sob.write_model_meta("not-a-model", None)` → `TypeError`.

- [ ] **Step 5: `_read_object_properties`/`_read_object_property_names` tests**

  On a class with no metadata → both return `None`.

- [ ] **Step 6: `pointer`/`url` deprecated-alias tests**

  `sob.meta.pointer(instance, "/foo/bar")` then a getter-only call;
  `sob.meta.pointer(123)` → `TypeError`; `sob.meta.url(instance,
  "https://example.com")`.

- [ ] **Step 7: Versioned `Array`/`Dictionary` tests**

  In `tests/test_version.py`, extend the existing versioning pattern: give
  an `ArrayProperty(item_types=...)` or `DictionaryProperty(value_types=
  ...)` a nested `Property` with `versions=[...]`, call
  `sob.meta.version_model(container_instance, "test-specification", "1.0")`
  directly, and assert the container's types were filtered as expected.
  Also construct a case where a to-be-removed versioned property still
  has a value set, and assert `sob.errors.VersionError` is raised; and
  `sob.meta.version_model(42, "spec", "1.0")` → `TypeError`.

- [ ] **Step 8: `_copy_model_meta_to` guard test**

  Import `sob.meta._copy_model_meta_to` directly and call it with a
  non-`abc.Model` `source` → confirm it raises.

- [ ] **Step 9: Run and confirm pass**

  `hatch test -- tests/test_model.py tests/test_version.py -vv`

- [ ] **Step 10: Confirm coverage**

  `meta.py` should reach ~93%; check `coverage report -m src/sob/meta.py`
  against spec §5.12 for any residual gap worth chasing.

- [ ] **Step 11: `make format` and commit**

---

## Task 13: `model.py` coverage (87% → ~95%)

**Files:**
- Modify: `tests/test_model.py`.

**Interfaces:**
- Consumes: `sob.Array`, `sob.Dictionary`, `sob.marshal`, `sob.unmarshal`,
  `sob.serialize`, `sob.deserialize`, `sob.validate`,
  `sob.replace_model_nulls`, `sob.get_model_from_meta`,
  `sob.get_models_source`, plus real `ObjectA`/`ArrayA` (and a new
  `DictionaryA` test class, mirroring `MemberDictionaryA` from
  `tests/test_version.py`) from this file.

- [ ] **Step 1: `Model`/format-guard test**

  `sob.Array(123)` and `sob.Dictionary(123)` → `TypeError`.

- [ ] **Step 2: `Array` protocol test**

  Build `arr = ArrayA([ObjectA(string="a")])` and exercise `.append(...)`,
  `arr[0] = ...`, `del arr[0]`, `.sort()`, `.extend([...])`,
  `reversed(arr)`, `.pop()`, `.remove(...)`, `copy.copy(arr)`,
  `repr(arr)`, `str(arr)`, `arr == ArrayA()` (type and length mismatch).
  In a follow-up within the same test or a sibling one, assign real
  `ArrayHooks` (`before_setitem`/`after_setitem`/`before_marshal`/
  `after_marshal`/`before_validate`) via `sob.write_model_hooks` and call
  `sob.validate(arr)` against an invalid item to hit the
  `ValidationError` raise.

- [ ] **Step 3: `Dictionary` protocol test**

  Declare `class DictionaryA(sob.Dictionary)` (new test fixture class,
  `item`/`value_types=sob.Types([ObjectA])`, following the `ArrayA`
  pattern already in this file). Build `d = DictionaryA({"a":
  ObjectA(...)})` and exercise `.update({...}, [("c", ...)], kw=...)`,
  `.setdefault(...)`, `.pop(...)`, `.popitem()`, `"a" in d`,
  `list(reversed(d))`, `copy.copy(d)`/`copy.deepcopy(d)`, `d ==
  DictionaryA()`, construction from a tuple-iterable instead of a `dict`,
  and real `DictionaryHooks` on `__setitem__`/`_marshal`.

- [ ] **Step 4: `Object` extras/copy-init test**

  Construct an `ObjectA` from another object with an incompatible
  property type to hit `_copy_init`'s exception-augmentation path;
  `obj["extra_key"] = "value"`, read it back, `del obj["extra_key"]` to
  hit the `_extra` branches; assign a real `ObjectHooks(before_setattr=fn)`
  and set an attribute.

- [ ] **Step 5: `marshal()` direct-call tests**

  `sob.marshal({"a": 1})`, `sob.marshal([1, 2])`, `sob.marshal(Decimal
  ("1.5"))`, `sob.marshal(datetime.now())`, `sob.marshal(b"data")`,
  `sob.marshal(object())` → `ValueError`, `sob.marshal(1, types=(str,))`
  → `TypeError`.

- [ ] **Step 6: `unmarshal()` tests**

  `sob.unmarshal({"string": "a"}, types=ObjectA)` (single type, not
  iterable); `sob.unmarshal((x for x in [1, 2]))` (generator); `sob.
  unmarshal(None)`; a real `before_unmarshal` hook registered on `ObjectA`.

- [ ] **Step 7: `serialize`/`deserialize` tests**

  Real `before_serialize`/`after_serialize` hooks on `ObjectA`; `sob.
  deserialize(b'{"a": 1}')`; `sob.deserialize(123)` → `TypeError`.

- [ ] **Step 8: `validate()` bare-type test**

  `sob.validate(ObjectA(), types=(ObjectA,))`.

- [ ] **Step 9: `replace_model_nulls` on an `Array` test**

  `arr = ArrayA([sob.NULL]); sob.replace_model_nulls(arr); assert arr[0]
  is None`.

- [ ] **Step 10: `get_model_from_meta`/`get_models_source` extension**

  Extend `test_get_model_from_meta_regression` with a `DictionaryMeta`-
  based class and `docstring=`/`pre_init_source=` arguments, and include
  it in the combined `get_models_source(...)` call. Run `make
  refresh-test-data` if this changes the golden regression output, and
  review the diff before committing the regenerated fixture.

- [ ] **Step 11: Run and confirm pass**

  `hatch test -- tests/test_model.py -vv`

- [ ] **Step 12: Confirm coverage**

  `model.py` should reach ~95%; check `coverage report -m src/sob/model.py`
  against spec §5.13 for residual gaps.

- [ ] **Step 13: `make format` and commit**

---

## Task 14: `thesaurus.py` coverage (64% → ~88%)

**Files:**
- Create: a second fixture — either extend
  `tests/static-data/thesaurus.json` or add
  `tests/static-data/thesaurus_polymorphic.json`.
- Modify: `tests/test_thesaurus.py`.

**Interfaces:**
- Consumes: `sob.thesaurus.Synonyms`, `sob.thesaurus.Thesaurus`,
  `sob.thesaurus.get_class_meta_attribute_assignment_source`.

- [ ] **Step 1: Build the richer fixture**

  Add `tests/static-data/thesaurus_polymorphic.json` containing: a base64
  string value, a plain ISO date string, a datetime string, a key whose
  value is sometimes a JSON object and sometimes a JSON array across
  records (to trigger the merge-conflict error path), a key whose
  synonym values include an empty object `{}` alongside populated ones,
  and a key that is always `null`.

- [ ] **Step 2: `Synonyms` construction/inference tests**

  `Synonyms().add(object())` → `TypeError`; `Synonyms([1.5, 2])` keeps
  the inferred type as `float`; a `Synonyms` built from the base64/date/
  datetime fixture values infers `bytes`/`date`/`datetime` respectively;
  a `Synonyms` where every value is `None` yields an untyped property.

- [ ] **Step 3: `Synonyms` file-like input test**

  Add a real `io.StringIO`/`io.BytesIO` containing JSON as a value and
  confirm `Synonyms`/`Thesaurus` decode it correctly.

- [ ] **Step 4: `Synonyms` mutation/set-algebra tests**

  Build two real `Synonyms` from different fixture groups; exercise
  `.discard(item)`, `.remove(item)`, `.pop()`, `&`, `^`, `-`, `<=`, `<`,
  `>`, `>=`, `==`, `in`, `.isdisjoint(...)`, `copy.copy(...)`,
  `copy.deepcopy(...)`.

- [ ] **Step 5: `Synonyms.get_models` guard tests**

  `synonyms.get_models(pointer, name=123)` → `TypeError`;
  `Synonyms([None]).get_models(pointer)` → `RuntimeError`.

- [ ] **Step 6: Metadata-merge error-path test**

  Using the mixed object/array fixture key from Step 1, assert
  `.get_models()`/`.get_module_source()` on the corresponding `Thesaurus`
  raises `TypeError` (incompatible container kinds at the same pointer).

- [ ] **Step 7: Metadata-merge success-path test**

  Since the success-merge branch isn't reachable through nested fixture
  data, call the module-internal `_update_object_meta`/
  `_update_object_class_from_meta` (and `_array`/`_dictionary`
  counterparts) directly with two real, hand-built `sob.meta` instances
  and two real classes from `sob.model.get_model_from_meta`; assert the
  merged metadata/class reflects the union of properties/types.

- [ ] **Step 8: `get_class_meta_attribute_assignment_source` test**

  Call directly with a real `ArrayMeta`/`ObjectMeta` that sets a
  non-default attribute (e.g. `item_types`) and assert the generated
  source string.

- [ ] **Step 9: `Thesaurus` mapping/set-protocol tests**

  Build a real `Thesaurus` from fixture data; exercise `.popitem()`,
  `.update(new=[...])`, `.setdefault("k", [...])`, `thesaurus["new"]`
  (auto-vivifying) vs. `thesaurus["existing"]`, `"k" in thesaurus`,
  `.keys()`, `.values()`, `t1 == t2`, `copy.copy(t)`, `reversed(t)`,
  `copy.deepcopy(t)`, `t1 += t2` / `t1 + t2` (two `Thesaurus` built from
  disjoint fixture subsets).

- [ ] **Step 10: `get_module`/`save_module` tests**

  `thesaurus.get_module()` — assert generated classes are real,
  importable attributes on the returned module. Using pytest's `tmp_path`
  fixture, call `thesaurus.save_module(tmp_path / "model.py")` against a
  path guaranteed not to exist, and confirm the file is written and
  re-importable (e.g. via `importlib` against the written path).

- [ ] **Step 11: Run and confirm pass**

  `hatch test -- tests/test_thesaurus.py -vv`

- [ ] **Step 12: Confirm coverage**

  `thesaurus.py` should reach ~88%; check `coverage report -m
  src/sob/thesaurus.py` against spec §5.14 for residual gaps.

- [ ] **Step 13: `make format` and commit**

---

## Task 15: Final verification against acceptance criteria

**Files:** none (verification only).

**Interfaces:**
- Consumes: the full test suite and coverage report built up by Tasks 1–14.

- [ ] **Step 1: Full local run**

  `hatch test -c -vv` (matches CI's `hatch test -c -py <version>`) on
  Python 3.10. Confirm zero failures, including all `--doctest-modules`
  items.

- [ ] **Step 2: Coverage check against acceptance criteria**

  `hatch run hatch-test.py3.10:coverage report -m`. Confirm: every module
  ≥ 90%, `hooks.py` and `thesaurus.py` ≥ 85%, overall ≥ 95%. If any module
  falls short, check whether the shortfall is an already-documented
  non-goal (spec §4) or a real gap that needs one more small test.

- [ ] **Step 3: Full matrix (optional but recommended before merging)**

  `hatch test -c` across the matrix if time/CI budget allows, or push a
  branch and let GitHub Actions' `test.yml` run all OS/Python
  combinations.

- [ ] **Step 4: `make format && hatch run mypy`**

  Confirm lint/type-check are clean across all touched files (this should
  already be true if `make format` was run after each task, but re-check
  once at the end for cross-task interactions).

- [ ] **Step 5: Update the spec's `Status` line**

  Edit `docs/superpowers/specs/2026-08-01-test-coverage-gaps-design.md`'s
  header from `**Status:** Draft — pending user review` to `**Status:**
  Implemented` (or similar), and commit.
