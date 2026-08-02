# Close remaining test-coverage gaps in `sob`

**Status:** Implemented (2026-08-01). Overall coverage 84%→87%; most
modules hit or exceeded target (see plan's Task 15 for final numbers).
`abc.py` (74%, all remaining lines are non-goal abstract stubs),
`model.py` (85%, target 90%+), and `thesaurus.py` (82%, target 85%+)
fell short of their per-module targets, and overall coverage (87%)
fell short of the ≥95% target — the remaining gaps are deep/low-value
branches (see plan for details). Four real bugs found and fixed along
the way: two hidden by a no-op doctest assertion, `indent()`'s
negative-`stop` sign error, `Properties.__eq__` comparing the wrong
operand, and two related polymorphism-merge bugs in `thesaurus.py`.
**Scope:** `src/sob/**` (all 16 modules), `tests/**`

## 1. Goal

Bring every module in `src/sob` up from its current measured coverage to
as close to 100% as is meaningful, using **real integration tests** —
constructing actual `sob` model/property/meta/hooks objects and exercising
them end-to-end — rather than mocks or patched internals. This matches the
existing test suite's own convention: `grep -rl "mock\|Mock\|monkeypatch"
tests/ src/` returns nothing today, and every existing test builds real
`sob.Object`/`sob.Array`/`sob.Dictionary` subclasses (see
`tests/test_model.py`, `tests/test_version.py`, `tests/test_utilities.py`).
This spec preserves that convention; no new test dependency (e.g.
`pytest-mock`, `unittest.mock`) should be introduced.

## 2. Current state (baseline)

Measured via `hatch test --cover` on 2026-08-01 (Python 3.10 leg):

```
Name                    Stmts   Miss  Cover
-------------------------------------------
src/sob/__init__.py        11      0   100%
src/sob/_datetime.py       28      2    93%
src/sob/_inspect.py        11      0   100%
src/sob/_io.py             19      4    79%
src/sob/_types.py          57      4    93%
src/sob/_utilities.py      28      3    89%
src/sob/abc.py            529     13    98%
src/sob/errors.py          59      7    88%
src/sob/hooks.py          110     60    45%
src/sob/meta.py           463     98    79%
src/sob/model.py         1308    176    87%
src/sob/properties.py     228     10    96%
src/sob/thesaurus.py      465    168    64%
src/sob/types.py           70     13    81%
src/sob/utilities.py      315     46    85%
src/sob/version.py         96     19    80%
-------------------------------------------
TOTAL                    3797    623    84%
```

`pyproject.toml` sets `fail_under = 70` — already passing overall, but
`hooks.py` (45%) and `thesaurus.py` (64%) are both individually below that
bar, and several modules have entire classes of behavior (error branches,
direct-construction paths, mapping-protocol methods) with zero exercise.

**Target:** every module ≥ 90%, `hooks.py` and `thesaurus.py` ≥ 85%,
overall ≥ 95%. Some lines (documented in §4) are genuinely low-value or
unreachable and are called out as explicit non-goals rather than chased.

## 3. Important finding: the doctest harness doesn't fail on doctest errors

Every `test_doctest()` function across the suite (e.g.
`tests/test_utilities.py:13`, `tests/test_datetime.py:11`) does:

```python
def test_doctest() -> None:
    doctest.testmod(utilities)
```

`doctest.testmod()` returns a `TestResults(failed, attempted)` tuple and
**never raises** on failure — it just prints a report to stdout. Since
nothing asserts on the return value, these test functions always pass
regardless of whether the docstring examples in the module actually work.
Confirmed by running `hatch test --cover` (33 passed, no failures reported)
versus running pytest directly with `--doctest-modules` (the flag already
configured in `pyproject.toml` under `[tool.hatch.envs.hatch-test]
extra-args`, which collects each doctest as its own pytest item):

```
src/sob/utilities.py::sob.utilities.suffix_long_lines FAILED
src/sob/_datetime.py::sob._datetime.str2datetime FAILED
2 failed, 49 passed
```

Two real, currently-failing doctests exist in the docstrings today:

- **`sob.utilities.suffix_long_lines`** — the example output doesn't
  include the `# noqa: E501` suffix the function actually appends; looks
  like a stale docstring after a recent edit (see commits `89e906a`,
  `c51259b`, `e3d58f0` — all docstring-wrap fixes).
- **`sob._datetime.str2datetime`** — `str2datetime("2023-10-01T12:00:00Z")`
  is documented to return a UTC-aware `datetime`, but on Python 3.10 it
  returns a **naive** `datetime` (the `Z`-suffix branch differs because
  `datetime.fromisoformat` only gained `Z`-parsing in Python 3.11; on 3.10
  it falls through to the `iso8601.parse_date` fallback, which the
  Python-3.10-only "incorrect UTC offset" correction then strips to naive).
  Since the test matrix covers 3.10–3.13, this doctest's expected output is
  only accurate on 3.11+.

**Decision needed from user before implementation:** should the plan (a)
fix `test_doctest()` in every test file to assert `failed == 0` (e.g.
`assert doctest.testmod(module).failed == 0`), which will immediately turn
these two into real failures that must be fixed as a prerequisite, or (b)
leave the harness as-is and just note the two bugs separately? Recommended:
**(a)** — it's a one-line change per file, it's the highest-leverage single
fix in this whole effort, and leaving it disabled defeats the purpose of
raising coverage elsewhere. The two underlying docstring/behavior bugs it
exposes should be fixed as their own small prerequisite fixes (not silently
adjusted expectations) before the coverage-gap tests are added, so the
gap-filling tests start from a green baseline.

## 4. Non-goals

Do not chase coverage on:

- **`abc.py` abstract-method stub bodies** (`pass` under `@abstractmethod`,
  e.g. lines 470, 757, 824, 966, 993, 1018, 1048, 1070, 1106, 1175, 1188,
  1195) — every concrete subclass overrides these; the stub body itself
  never executes in real usage and testing it would require calling the
  abstract method through a deliberately broken subclass, which tests
  nothing meaningful.
- **`TYPE_CHECKING`-only `assert` statements** (e.g. `model.py:1812`) —
  dead at runtime by construction.
- **`model.py` `_marshal`/`_validate` abstract `pass` bodies** (148, 162,
  166 area) — same reasoning as `abc.py`.
- A handful of deeply-defensive `TypeError`/exec-failure guards in
  `model.py`'s `get_models_source` (3412, 3482, 3491) that would require
  contriving malformed metadata objects bypassing all public constructors
  to trigger — flagged as low-priority, skip unless trivial.

## 5. Per-module test plan

Each subsection lists concrete, mock-free scenarios. Where a module already
has a test file, new tests extend it; naming follows the existing
`test_<behavior>` convention (see `tests/test_model.py`,
`tests/test_types.py`).

### 5.1 `_datetime.py` (93% → ~100%)
File: `tests/test_datetime.py`
- `str2datetime` raises `TypeError` for a non-`str` argument (parallel to
  the existing `test_raise_str2date_type_error`) — covers line 59.
- `str2date` raises `TypeError` for a non-`str` argument — covers line 88.
- (Prerequisite, see §3) fix the `str2datetime("...Z")` docstring/behavior
  mismatch on Python 3.10 before/alongside this work.

### 5.2 `_io.py` (79% → 100%)
File: `tests/test_utilities.py` (or a new `tests/test__io.py`)
- A file-like proxy whose `read()` raises `io.UnsupportedOperation` (and
  has no `readall`) to hit the `except UnsupportedOperation: pass` branch,
  followed by exhausting both method names — e.g. a class with `read` that
  always raises, and no `readall`, confirming the final `TypeError` is
  raised (`f"{file!r} is not a file-like object"`) — covers lines 39-42.
- A plain `object()` (no `seek`/`read`/`readall`) passed to `sob._io.read`
  to hit the `TypeError` path directly too.

### 5.3 `_types.py` (93% → 100%)
File: `tests/test_types.py`
- `hash(sob.UNDEFINED) == 0` — covers line 41.
- `hash(sob.NULL) == 0`, `str(sob.NULL) == "null"`,
  `sob.Null._marshal() is None` — covers lines 102, 105, 109.

### 5.4 `_utilities.py` (89% → 100%)
File: `tests/test_utilities.py`
- Decorate a real function with `sob._utilities.deprecated("message")`,
  call it, and assert (via `pytest.warns(DeprecationWarning, match=...)`)
  that the warning fires and the wrapped function's return value passes
  through — covers line 34. (This one line also silently backs every
  `deprecated`-wrapped alias across `abc.py`, `properties.py`, `meta.py`,
  `hooks.py`, `model.py`, `thesaurus.py`, and `utilities.py` — e.g.
  `sob.hooks.Object`, `sob.meta.read`, `sob.properties.String` — none of
  which is currently invoked anywhere in the test suite. Once this line is
  covered directly, calling a representative one or two of those aliases
  under `pytest.warns(DeprecationWarning)` in their respective module's
  test file is a cheap way to also confirm the aliases themselves are
  wired correctly, though it isn't required to close this specific gap.)
- A proxy object with a non-`str` `.url` attribute →
  `get_readable_url` raises `TypeError` — covers line 50.
- A proxy object with none of `geturl`/`url`/`name` → returns `None` —
  covers line 61.

### 5.5 `abc.py` (98% → ~99%, remainder is §4 non-goals)
No new tests needed beyond what naturally falls out of exercising the
concrete classes elsewhere in this plan (`abc.py`'s only non-non-goal gaps
are abstract stubs).

### 5.6 `errors.py` (88% → 100%)
File: `tests/test_utilities.py` or a new `tests/test_errors.py`
- Construct `sob.errors.DeserializeError(data="bad", message="oops")`
  directly; assert `.data`, `.message`, `repr(error)` (message + `"Could
  not parse:\n..."`), and `str(error) == repr(error)` — covers 57-59, 62,
  68.
- `append_exception_text`: build a real exception with a `strerror`
  attribute (e.g. `OSError(1, "boom")`, which sets `.strerror`) and confirm
  the message is appended to `.strerror` — covers line 161.
- `append_exception_text` on an exception with empty `.args` (e.g.
  `Exception()`) to hit the "not found" `else` branch — covers line 174.

### 5.7 `types.py` (81% → 100%)
File: `tests/test_types.py`
- `sob.Types(str)` (bare type, not wrapped in a sequence) — covers line 43.
- `copy.copy(sob.Types([int, str]))` — covers line 49.
- On a `sob.MutableTypes` instance: `types[0] = float` (`__setitem__`),
  `types.extend([bool])`, `del types[0]` (`__delitem__`), `types += [str]`
  (`__iadd__`), and `new_types = types + [int]` (`__add__`, returning a
  fresh `MutableTypes`) — covers 123-124, 130, 133, 139-140, 145-149.

### 5.8 `properties.py` (96% → 100%)
File: `tests/test_model.py` or a new `tests/test_properties.py`
- `has_mutable_types` with a plain (non-`Property`) argument that is not a
  `type[abc.Property]` subclass → `TypeError` — covers 66-72 (also hits
  both branches of the `isinstance(property_, abc.Property)` check with a
  `Property` instance vs. a `Property` subclass passed as a bare type).
- Attempt to reassign `.types` on a `Property` instance whose class defines
  `_types` at the class level (e.g. `sob.StringProperty().types = [int]`)
  → `TypeError` ("... .types` is immutable") — covers line 163.
- Assign an invalid (non-type, non-`Property`, non-`None`) value to
  `.types` on a property whose `_types` is *not* class-level-fixed (a bare
  `sob.Property().types = "not-a-type"`) → `TypeError` — covers line 172.
- Assign an invalid `.versions` value (e.g. `sob.Property().versions =
  123`) → `TypeError` — covers lines 192, 196.

### 5.9 `version.py` (80% → 100%)
File: `tests/test_version.py`
`sob.Version` is currently only exercised indirectly through
`version_model`/property `versions=` args — no test constructs or compares
`sob.Version` instances directly. Add:
- `sob.version._are_versions_compatible`/`_are_versions_equal` via
  `sob.Version(equals="1.2") == "1.2.0"` and `== "1.2"` (differing
  precision) to cover the truncation/length-mismatch branches (lines 24,
  31, 37-43).
- `sob.version._version_string_as_tuple("not-a-version")` (or
  constructing `sob.Version("not-a-version")`) → `ValueError` — line 81.
- `sob.Version(compatible_with=1.2)` and `sob.Version(compatible_with=
  (1, 2))` (a bare float and a bare sequence, exercising the numeric and
  sequence branches of `_version_as_tuple`) — lines 88, 94, 116-119.
- `sob.version._version_as_tuple(object())` → `TypeError` — line 113.
- `sob.Version(123)` (non-`str` `version_string`) → `TypeError` — line 226.
- `sob.Version("a==1,b==2")` (two different specification prefixes in one
  string) → `ValueError` — line 249.
- `specification` defaults to `""` (verified: a default-built `sob.Version`
  never leaves it `None`), so the `RuntimeError` at line 301 can't be
  triggered through the constructor alone. `specification` is a plain
  public attribute (no property/validation), so directly assigning
  `version.specification = None` after construction and then calling
  `str(version)` is normal use of the public interface, not a mock or
  monkeypatch — use that to cover line 301.

### 5.10 `utilities.py` (85% → ~97%)
File: `tests/test_utilities.py`
- URL helpers: call the internal URL-splitting helper with a malformed URL
  to hit its `ValueError`, and `get_relative_url("https://a.com/x/y",
  "https://a.com/x/z")` plus a case with **no shared prefix** between
  absolute and base URL — covers 389-393, 402-416.
- `_align_indent("no-leading-space")` — covers line 427.
- `_split_long_comment_line` with a short line (no wrap needed) — covers
  line 473.
- `split_long_docstring_lines`: an already-uniformly-indented docstring
  (covers 505, 510-511) and a docstring containing a `"""`/`'''` literal
  that closes on the same or later line, needing the suffix re-appended —
  covers 540-548 (`suffix_long_lines`'s quote-tracking loop).
- `get_qualified_name`: pass an unsupported type → `TypeError` (line 657);
  pass a generic alias like `list[int]` to hit the `__origin__`/`repr()`
  fallback (line 675); construct an object whose type truly can't resolve
  a qualified name to hit the final `TypeError` (line 682).
- `get_calling_module_name`/`get_calling_function_qualified_name`: call
  with `depth` deep enough to exceed the real stack to hit the
  `IndexError`/short-stack `None` returns (745-746, 772, 775-776), and call
  with a non-`int` `depth` → `TypeError` (line 772's guard).
- `_repr_list([])`, `_repr_set(set())`, `_repr_dict({})` — the empty-
  collection short-circuit branches (`"[]"`, `"set()"`, `"{}"`) — covers
  818-819, 842, 852.
- `represent(SomeClass)` (representing a bare `type`, not an instance) —
  covers line 870.
- `get_method`: an object missing the requested method with **no**
  `default` (so `default` stays `sob.UNDEFINED`) → re-raises `AttributeError`
  (910); an object where the attribute exists but isn't callable, with and
  without a `default` → returns default or raises — covers 914-920.

### 5.11 `hooks.py` (45% → ~90%+) — highest-value gap
File: `tests/test_model.py` or a new `tests/test_hooks.py`. Currently
**zero** test in the suite constructs `ObjectHooks`/`ArrayHooks`/
`DictionaryHooks` or calls any `*_hooks` function — `model.py` calls the
read-side internally on every operation (which is why 45% is already
covered passively), but nothing ever registers a hook, so the entire
write/get-writable/dispatch surface is dark.
- `ObjectHooks(before_setattr=fn, after_setattr=fn)` assigned via
  `sob.write_model_hooks(ObjectA, hooks)`; set an attribute on an instance
  and assert both real (non-mock) callables fired with expected arguments
  — covers `ObjectHooks.__init__` (244-257) and the `write_model_hooks`
  body (835-849).
- `ArrayHooks(before_append=fn, after_append=fn)` on `sob.ArrayA`;
  `.append(...)` and assert hooks fired — covers 382-395.
- `DictionaryHooks(before_setitem=fn, after_setitem=fn)` on a `Dictionary`
  subclass; `d["k"] = v` — covers 505-516.
- `sob.read_model_hooks("not-a-model")` → `TypeError` — covers 549-560.
- `sob.get_writable_model_hooks(ObjectA)` on a class with no hooks yet
  assigned → returns a fresh `ObjectHooks`, confirmed idempotent via a
  second `sob.read_model_hooks(ObjectA)` call returning the same object;
  repeat on an instance; and `sob.get_writable_model_hooks(42)` →
  `TypeError` — covers 626, 633, 639, 645, 665-704.
- `sob.get_writable_object_hooks`/`get_writable_array_hooks`/
  `get_writable_dictionary_hooks` called directly on each container type —
  covers 730, 756, 785.
- `sob.get_model_hooks_type(ObjectA)` → `ObjectHooks` (and same for
  `Array`/`Dictionary`, both class and instance); `sob.get_model_hooks_type
  (str)` → `TypeError` — covers 800-820.
- `sob.write_model_hooks(ObjectA, sob.ArrayHooks())` (wrong hooks type) →
  `ValueError`; `sob.write_model_hooks("not-a-model", hooks)` → `TypeError`
  — rounds out 835-849.

### 5.12 `meta.py` (79% → ~93%)
File: `tests/test_model.py` / `tests/test_version.py`
- Assign a bare (non-iterable) type/Property to `DictionaryProperty(
  value_types=sob.StringProperty())` and `ArrayProperty(item_types=str)`
  (not wrapped in a list) — covers 217-219, 271-273.
- Exercise `sob.Properties` mapping protocol directly on
  `sob.get_writable_object_meta(ObjectA).properties`: `.pop("string")`,
  `.popitem()`, `.setdefault("x", sob.StringProperty())`,
  `.get("missing")`, `.clear()`, `copy.copy(properties)`, `repr(...)`,
  equality between two independently-built `Properties` with identical
  items, `properties["bad"] = "not-a-property"` → `TypeError`,
  `.setdefault("x", 5)` → `TypeError`, `.update({...})` with a plain
  `dict` — covers 304-318, 370, 376, 385, 396, 403, 406, 427, 430, 443-445,
  450, 453-455.
- Define a brand-new `sob.Object` subclass with no metadata ever assigned
  and call `sob.read_model_meta(NewClass)` → `None` — covers 488-491.
- `sob.get_writable_object_meta("not-a-model")` and `sob.
  get_writable_object_meta(int)` → `TypeError` — covers 610-619.
- `sob.write_model_meta(ObjectA, sob.ArrayMeta())` → `ValueError`;
  `sob.write_model_meta("not-a-model", None)` → `TypeError` — covers 714,
  716-717, 750, 754-755.
- `sob.meta._read_object_properties`/`_read_object_property_names` on a
  class with no metadata → `None` returns — covers 784, 793, 802.
- `sob.meta.pointer(instance, "/foo/bar")` then re-call with
  `pointer_=None` to hit only the getter; `sob.meta.pointer(123)` →
  `TypeError`; `sob.meta.url(instance, "https://example.com")` — covers
  883-886, 962-963.
- Extend `test_version.py`'s pattern to a versioned **`Array`**/
  **`Dictionary`** (not just `Object`): give `ArrayProperty(item_types=...)`
  or `DictionaryProperty(value_types=...)` a nested `Property` with
  `versions=[...]`, call `sob.meta.version_model(container_instance,
  "test-specification", "1.0")` directly, and assert the container's
  types were filtered — covers 1001, 1022-1097, 1114-1149. Also
  deliberately trigger `sob.errors.VersionError` by setting a
  to-be-removed versioned property's value before calling `version_model`
  with an incompatible version. `sob.meta.version_model(42, "spec", "1.0")`
  → `TypeError` — covers 1182, 1185-1187.
- `sob.meta._copy_model_meta_to` with a non-`abc.Model` `source` (module-
  internal, acceptable to import directly since it's the unit under test)
  — covers 1248, 1274.

### 5.13 `model.py` (87% → ~95%)
File: `tests/test_model.py`. This is the largest module; group tests by
the affected class/function.
- **`Model`/format guard**: `sob.Array(123)`, `sob.Dictionary(123)` →
  `TypeError` (line 148).
- **`Array` protocol**: build `arr = ArrayA([ObjectA(string="a")])` and
  exercise `arr.append(...)`, `arr[0] = ObjectA(string="b")`, `del
  arr[0]`, `arr.sort()`, `arr.extend([...])`, `reversed(arr)`, `arr.pop()`,
  `arr.remove(...)`, `copy.copy(arr)`, `repr(arr)`, `str(arr)`, `arr ==
  ArrayA()` (type and length mismatch), plus real `ArrayHooks`
  (`before_setitem`/`after_setitem`/`before_marshal`/`after_marshal`/
  `before_validate`) assigned via `sob.write_model_hooks` and a
  `sob.validate(arr)` call against an invalid item to hit the
  `ValidationError` raise (lines 391, 414, 436-597, 652-673).
- **`Dictionary` protocol**: build `d = DictionaryA({"a": ObjectA(...)})`
  (mirroring `MemberDictionaryA` from `test_version.py`) and exercise
  `d.update({...}, [("c", ...)], kw=...)`, `d.setdefault(...)`, `d.pop(...)`,
  `d.popitem()`, `"a" in d`, `list(reversed(d))`, `copy.copy(d)`/
  `copy.deepcopy(d)`, `d == DictionaryA()`, construct from a tuple-iterable
  instead of a `dict`, and real `DictionaryHooks` on `__setitem__`/
  `_marshal` (lines 935-1343).
- **`Object` extras/copy-init**: construct `ObjectA(other_object_with_a_
  type-incompatible_property)` to hit `_copy_init`'s exception-
  augmentation path; `obj["extra_key"] = "value"`, read it back, and
  `del obj["extra_key"]` to hit the `_extra` (non-metadata-attribute)
  branches of `__setitem__`/`__getitem__`/`__delitem__`; real
  `ObjectHooks(before_setitem=fn)` on `obj["string"] = "x"` (lines
  1600-1994).
- **Module-level `marshal()`**: call directly (not just via `Object.
  _marshal`) on a raw `dict`, `list`, `set`, `Decimal`, `datetime`, `date`,
  `bytes`, and an unsupported `object()` (→ `ValueError`), plus `marshal(1,
  types=(str,))` (→ `TypeError`) (lines 2013-2129).
- **`unmarshal()`**: `sob.unmarshal({"string": "a"}, types=ObjectA)`
  (single type, not iterable); `sob.unmarshal((x for x in [1, 2]))`
  (generator input); `sob.unmarshal(None)`; a real `before_unmarshal` hook
  registered on `ObjectA` (lines 2171-2381).
- **`serialize`/`deserialize`**: real `before_serialize`/`after_serialize`
  hooks on `ObjectA`; `sob.deserialize(b'{"a": 1}')` (bytes path);
  `sob.deserialize(123)` → `TypeError` (lines 2502-2594).
- **`validate()`**: `sob.validate(ObjectA(), types=(ObjectA,))` (bare type,
  not `Property`) (line 2635).
- **`replace_model_nulls`**: `arr = ArrayA([sob.NULL]);
  sob.replace_model_nulls(arr)`; assert `arr[0] is None` — Array-item NULL
  replacement is untested today (only Object-property NULLs are) (line
  3012).
- **`get_model_from_meta`/`get_models_source`**: extend
  `test_get_model_from_meta_regression` with a `DictionaryMeta`-based
  class and `docstring=`/`pre_init_source=` arguments, and include it in
  the combined `get_models_source(...)` call (lines 3061-3520 area).

### 5.14 `thesaurus.py` (64% → ~88%) — second-highest-value gap
File: `tests/test_thesaurus.py` (currently only 28 lines: one regression
test that round-trips `tests/static-data/thesaurus.json` through
`Thesaurus(...).get_module_source()` against a golden file). `Thesaurus`
infers an `sob` data model from *example* JSON data (rather than a
schema); `Synonyms` is the set-like collection of interchangeable values
used to infer one property's type, `Thesaurus` is the dict-like collection
of named `Synonyms` keyed by pointer/identifier. The single flat fixture
(bools/strings/one array-of-arrays-of-int) never exercises polymorphism-
merging, date/base64/bytes detection, error paths, or most of the
`Synonyms`/`Thesaurus` mapping/set protocol — hence the large gap. Add a
**second, deliberately richer static fixture**
(`tests/static-data/thesaurus_polymorphic.json`, or extend the existing
one) containing: a base64 string, a plain date string, a datetime string,
a key that is sometimes an object and sometimes an array (to trigger the
type-conflict error path), a key whose synonym values include an empty
object `{}` alongside populated ones, and a key that is always `null`.
Then:
- **`Synonyms` construction/inference** (462, 540, 549, 691-698, 800):
  `Synonyms().add(object())` → `TypeError` (line 540); `Synonyms([1.5,
  2])` keeps the inferred type as `float`, not `int` (line 549); a
  `Synonyms` built from base64/date/datetime strings infers `bytes`/
  `date`/`datetime` respectively (691-698, 462); a shared key whose values
  are always `None` falls back to an untyped `Property(name=key)` (800).
- **`Synonyms` file-like input** (71-76): add a real `io.StringIO`/
  `io.BytesIO` containing JSON as a `Synonyms`/`Thesaurus` value and
  confirm it decodes via both the `str` and `bytes` branches of `_read`.
- **`Synonyms` mutation/set-algebra** (540-579, 630-681): build two real
  `Synonyms` from different fixture groups and exercise `.discard(item)`,
  `.remove(item)`, `.pop()`, `&`, `^`, `-`, `<=`, `<`, `>`, `>=`, `==`,
  `in`, `.isdisjoint(...)`, `copy.copy(...)`, `copy.deepcopy(...)`.
- **`Synonyms.get_models` guards** (908, 913-914, 922): `synonyms.
  get_models(pointer, name=123)` (non-callable `name`) → `TypeError`;
  `Synonyms([None]).get_models(pointer)` (nothing inferable) →
  `RuntimeError`.
- **Metadata-merge chain** (`_update_types`, `_update_array_meta`,
  `_update_dictionary_meta`, `_update_object_meta`, the three
  `_update_*_class_from_meta` functions, and `_get_models_from_meta`'s
  memo-hit branches — lines 93-111, 129-143, 161-175, 194-232, 254-269,
  286-291, 311-318, 340-358, 412-413, 417): these only run when the same
  JSON pointer produces metadata twice in one `.get_models()` call.
  - The **error branch** is reachable through the public API: the mixed
    object/array fixture key above should make `.get_models()`/
    `.get_module_source()` raise `TypeError` when the same pointer
    resolves to incompatible container kinds — assert with
    `pytest.raises(TypeError)`.
  - The **success merge** path (two `ObjectMeta`/`ArrayMeta`/
    `DictionaryMeta` at the same pointer with the *same* container kind
    but different properties/types) isn't reachable through nested
    fixture data without contrived recursive pointer collisions; test it
    by calling the module-internal `_update_object_meta`/
    `_update_object_class_from_meta` (and `_array`/`_dictionary`
    counterparts) directly with two real, hand-built `sob.meta` instances
    and two real classes from `sob.model.get_model_from_meta`, then assert
    the merged metadata/class reflects the union.
- **`get_class_meta_attribute_assignment_source`** (989-996): call
  directly with a real `sob.meta.ArrayMeta`/`ObjectMeta` that sets a
  non-default attribute (e.g. `item_types`) and assert the generated
  source string.
- **`Thesaurus` mapping/set protocol** (1124, 1146, 1160-1211): build a
  real `Thesaurus` from fixture data and exercise `.popitem()`,
  `.update(new=[...])`, `.setdefault("k", [...])`, `thesaurus["new"]`
  (auto-vivifying `__getitem__`) vs. `thesaurus["existing"]`, `"k" in
  thesaurus`, `.keys()`, `.values()`, `t1 == t2`, `copy.copy(t)`,
  `reversed(t)`, `copy.deepcopy(t)`, and `t1 += t2` / `t1 + t2` (two real
  `Thesaurus` built from disjoint fixture subsets).
- **`Thesaurus.get_module`/`save_module`** (1275-1276, 1301-1306):
  `thesaurus.get_module()` returns an executed `ModuleType` — assert the
  generated classes are real, importable attributes on it. The existing
  regression test's `save_module` call never exercises the actual file-
  write branch because the golden file already exists on disk; add a
  `tmp_path`-based test that calls `thesaurus.save_module(tmp_path /
  "model.py")` against a path guaranteed not to exist, and confirm the
  file is written and re-importable.

## 6. Testing conventions to follow

- **No mocks.** Every new test builds real `sob` objects (subclasses of
  `sob.Object`/`sob.Array`/`sob.Dictionary`, real `Property`/`Meta`/`Hooks`
  instances) and calls real functions — matching 100% of existing tests.
- **Real callables for hooks**, not `unittest.mock.Mock` — e.g. a closure
  that appends to a list the test asserts against afterward, as already
  done implicitly elsewhere in the codebase's style (plain functions/
  classes as fixtures, e.g. `HTTPResponseProxy1` in `test_utilities.py`).
- Follow the file's existing structure: `from __future__ import
  annotations`, a `test_doctest()` per module (once fixed per §3), plain
  `test_*` functions (no test classes), and the `if __name__ == "__main__":
  pytest.main([__file__, "-s", "-vv"])` trailer.
- Where a module has no test file yet (none currently — every `src/sob/*`
  module maps to a `tests/test_*.py` except the underscore-prefixed
  internals, which are tested from within `tests/test_utilities.py`/
  `tests/test_types.py`), keep using that existing file rather than
  fragmenting into more files, matching current 1:1-ish structure.
- Regression-style tests (`tests/regression-data/`) are the established
  pattern for "build once, compare generated output" cases (see
  `test_thesaurus`, `test_get_model_from_meta_regression`,
  `test_serialization_regression`) — reuse this pattern for new
  `thesaurus.py` and `get_models_source` coverage rather than inventing a
  new fixture mechanism.
- Run `hatch test -- tests/test_<module>.py` per file during development;
  `hatch test --cover` (or `hatch run hatch-test.py3.10:coverage report
  -m`) to confirm line-level coverage before/after.

## 7. Acceptance criteria

- `hatch test -c` passes on all four Python versions (3.10–3.13) with the
  `test_doctest()` fix from §3 applied (i.e. it actually fails if a
  docstring example breaks).
- `coverage report -m` shows every module ≥ 90%, with `hooks.py` and
  `thesaurus.py` ≥ 85%, and overall ≥ 95%.
- No new test uses `unittest.mock`, `pytest-mock`, or monkeypatches any
  `sob` internals — all assertions exercise real, constructed objects.
- Lines listed under §4 (Non-goals) remain uncovered by design and are not
  flagged as regressions in future coverage diffs.
