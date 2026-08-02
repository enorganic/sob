from __future__ import annotations

import io
import json
from copy import copy, deepcopy
from datetime import date, datetime
from pathlib import Path
from types import ModuleType

import pytest

import sob
from sob.thesaurus import (
    Synonyms,
    Thesaurus,
    get_class_meta_attribute_assignment_source,
)

THESAURUS_JSON: Path = Path(__file__).parent / "static-data" / "thesaurus.json"
THESAURUS_MODEL_PY: Path = (
    Path(__file__).parent / "regression-data" / "thesaurus_model.py"
)


def test_thesaurus() -> None:
    with open(THESAURUS_JSON) as thesaurus_io:
        thesaurus: Thesaurus = Thesaurus(json.load(thesaurus_io))
    if THESAURUS_MODEL_PY.exists():
        assert thesaurus.get_module_source().strip() == (
            THESAURUS_MODEL_PY.read_text().strip()
        )
    else:
        thesaurus.save_module(THESAURUS_MODEL_PY)


# region Synonyms construction/inference


def test_synonyms_add_type_error() -> None:
    error_caught: bool = False
    try:
        Synonyms().add(object())  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_synonyms_int_after_float_stays_float() -> None:
    synonyms: Synonyms = Synonyms([1.5, 2])
    assert synonyms._type == {float}  # noqa: SLF001


def test_synonyms_base64_inference() -> None:
    synonyms: Synonyms = Synonyms(["aGVsbG8=", "d29ybGQ="])
    assert list(synonyms._iter_simple_types()) == [bytes]  # noqa: SLF001


def test_synonyms_date_inference() -> None:
    synonyms: Synonyms = Synonyms(["2020-01-01", "2021-02-02"])
    assert list(synonyms._iter_simple_types()) == [date]  # noqa: SLF001


def test_synonyms_datetime_inference() -> None:
    synonyms: Synonyms = Synonyms(
        ["2020-01-01T00:00:00", "2021-02-02T00:00:00"]
    )
    assert list(synonyms._iter_simple_types()) == [  # noqa: SLF001
        datetime
    ]


def test_synonyms_always_null_property() -> None:
    thesaurus: Thesaurus = Thesaurus(
        {
            "item": [
                {"always_null": None, "name": "a"},
                {"always_null": None, "name": "b"},
            ]
        }
    )
    source: str = thesaurus.get_module_source()
    assert 'sob.Property(\n            name="always_null"' in source


def test_synonyms_file_like_input() -> None:
    synonyms: Synonyms = Synonyms()
    synonyms.add(io.StringIO("[42]"))
    assert list(synonyms) == [42]
    synonyms_bytes: Synonyms = Synonyms()
    synonyms_bytes.add(io.BytesIO(b"[42]"))
    assert list(synonyms_bytes) == [42]


# endregion
# region Synonyms mutation/set-algebra


def test_synonyms_mutation() -> None:
    synonyms: Synonyms = Synonyms(["a", "b", "c"])
    synonyms.discard("a")
    assert "a" not in synonyms
    synonyms.remove("b")
    assert "b" not in synonyms
    popped: str = synonyms.pop()  # type: ignore
    assert popped == "c"
    assert len(synonyms) == 0


def test_synonyms_set_algebra() -> None:
    synonyms_a: Synonyms = Synonyms(["a", "b"])
    synonyms_b: Synonyms = Synonyms(["b", "c"])
    assert set(synonyms_a & synonyms_b) == {"b"}
    assert set(synonyms_a ^ synonyms_b) == {"a", "c"}
    assert set(synonyms_a - synonyms_b) == {"a"}
    assert Synonyms(["a"]) <= synonyms_a
    assert Synonyms(["a"]) < synonyms_a
    assert synonyms_a > Synonyms(["a"])
    assert synonyms_a >= Synonyms(["a", "b"])
    assert synonyms_a == Synonyms(["a", "b"])
    assert "a" in synonyms_a
    assert synonyms_a.isdisjoint(Synonyms(["z"]))
    assert not synonyms_a.isdisjoint(synonyms_b)
    assert copy(synonyms_a) == synonyms_a
    assert deepcopy(synonyms_a) == synonyms_a


# endregion
# region Synonyms.get_models guards


def test_synonyms_get_models_name_type_error() -> None:
    error_caught: bool = False
    try:
        list(Synonyms(["a"]).get_models("ptr", name=123))  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_synonyms_get_models_runtime_error() -> None:
    error_caught: bool = False
    try:
        list(Synonyms([sob.NULL]).get_models("ptr"))
    except RuntimeError:
        error_caught = True
    assert error_caught


# endregion
# region metadata-merge chain


def test_thesaurus_mixed_object_array_conflict() -> None:
    """
    The same JSON pointer resolving to both an object and an array (across
    different records sharing a key) is a real, reachable error via the
    public API.
    """
    thesaurus: Thesaurus = Thesaurus(
        {
            "item": [
                {"tags": {"id": 1}},
                {"tags": [{"id": 1}, {"id": 2}]},
            ]
        }  # type: ignore
    )
    error_caught: bool = False
    try:
        thesaurus.get_module_source()
    except TypeError:
        error_caught = True
    assert error_caught


def test_update_object_class_from_meta_merges_new_properties() -> None:
    """
    Regression test: `_update_object_meta` used to compute
    `metadata_keys - new_metadata_keys` (properties unique to the
    *existing* metadata) when deciding which properties to copy over from
    `new_metadata`, then look those keys up *in* `new_metadata` -- which
    doesn't have them. This either silently added nothing (when the
    existing metadata's properties were a subset of the new metadata's)
    or raised a `KeyError` (when the existing metadata had properties the
    new metadata didn't). Fixed to compute
    `new_metadata_keys - metadata_keys` instead, so properties introduced
    by a later-encountered, differently-shaped record actually get merged
    in, per this function's own docstring.
    """
    initial_meta: sob.ObjectMeta = sob.ObjectMeta()
    initial_meta.properties = sob.Properties(
        [
            ("a", sob.StringProperty()),
            ("c", sob.BooleanProperty()),
        ]
    )
    model_class: type = sob.get_model_from_meta(
        "MergeTarget", initial_meta, module="__main__"
    )
    new_meta: sob.ObjectMeta = sob.ObjectMeta()
    new_meta.properties = sob.Properties(
        [
            ("a", sob.StringProperty()),
            ("b", sob.IntegerProperty()),
        ]
    )
    sob.thesaurus._update_object_class_from_meta(  # noqa: SLF001
        model_class, new_meta, memo={}
    )
    updated_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(model_class)
    assert updated_meta is not None
    assert updated_meta.properties is not None
    assert set(updated_meta.properties.keys()) == {"a", "b", "c"}


# endregion


def test_get_class_meta_attribute_assignment_source() -> None:
    array_meta: sob.ArrayMeta = sob.ArrayMeta(item_types=[str])
    source: str = get_class_meta_attribute_assignment_source(
        "MyClass", "item_types", array_meta
    )
    assert "MyClass" in source
    assert "item_types" in source


# region Thesaurus mapping/set protocol


def test_thesaurus_mapping_protocol() -> None:
    thesaurus: Thesaurus = Thesaurus({"a": ["x", "y"], "b": ["z"]})
    assert set(thesaurus.keys()) == {"a", "b"}
    assert isinstance(thesaurus["a"], Synonyms)
    # Auto-vivifying `__getitem__`
    assert isinstance(thesaurus["new"], Synonyms)
    thesaurus.update(c=["w"])
    assert "c" in thesaurus
    thesaurus.setdefault("d", ["v"])
    assert "d" in thesaurus
    key: str
    key, _synonyms = thesaurus.popitem()
    assert key not in thesaurus
    assert copy(thesaurus) == thesaurus
    assert deepcopy(thesaurus) == thesaurus
    assert list(reversed(thesaurus).keys()) == list(  # type: ignore
        reversed(list(thesaurus.keys()))
    )


def test_thesaurus_add() -> None:
    thesaurus_a: Thesaurus = Thesaurus({"a": ["x"]})
    thesaurus_b: Thesaurus = Thesaurus({"b": ["y"]})
    combined: Thesaurus = thesaurus_a + thesaurus_b
    assert set(combined.keys()) == {"a", "b"}
    thesaurus_a += thesaurus_b
    assert set(thesaurus_a.keys()) == {"a", "b"}


def test_thesaurus_iadd_type_error() -> None:
    thesaurus: Thesaurus = Thesaurus({"a": ["x"]})
    error_caught: bool = False
    try:
        thesaurus += "not-a-thesaurus"  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


# endregion
# region get_module()/save_module()


def test_thesaurus_get_module() -> None:
    thesaurus: Thesaurus = Thesaurus({"item": [{"name": "a"}, {"name": "b"}]})
    module: ModuleType = thesaurus.get_module()
    assert hasattr(module, "Item")
    assert issubclass(module.Item, sob.Object)


def test_thesaurus_save_module(tmp_path: Path) -> None:
    thesaurus: Thesaurus = Thesaurus({"item": [{"name": "a"}, {"name": "b"}]})
    module_path: Path = tmp_path / "generated_model.py"
    assert not module_path.exists()
    thesaurus.save_module(module_path)
    assert module_path.exists()
    assert "class Item" in module_path.read_text()


# endregion


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
