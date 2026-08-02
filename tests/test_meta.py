from __future__ import annotations

import collections.abc
from copy import copy
from typing import IO, TYPE_CHECKING

import pytest

import sob
import sob.meta

if TYPE_CHECKING:
    from collections.abc import Sequence

# region Declare classes


class MetaObjectA(sob.Object):
    __slots__: tuple[str, ...] = ("name",)

    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        name: str | None = None,
    ) -> None:
        self.name: str | None = name
        super().__init__(_data)


sob.get_writable_object_meta(MetaObjectA).properties = sob.Properties(
    [("name", sob.StringProperty())]
)


class MetaObjectNoMeta(sob.Object):
    pass


class MetaArrayA(sob.Array):
    def __init__(
        self,
        items: Sequence[str] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_array_meta(MetaArrayA).item_types = sob.Types([str])


class MetaDictionaryA(sob.Dictionary):
    def __init__(
        self,
        items: dict[str, str] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_dictionary_meta(MetaDictionaryA).value_types = sob.Types(
    [str]
)


class MinimalMapping(collections.abc.Mapping):
    """
    A minimal `Mapping` implementation that is *not* `Reversible`, used to
    exercise the "sorted items" branch of `Properties.update`.
    """

    def __init__(self, data: dict[str, sob.Property]) -> None:
        self._data: dict[str, sob.Property] = data

    def __getitem__(self, key: str) -> sob.Property:
        return self._data[key]

    def __iter__(self) -> collections.abc.Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


# endregion


class BareMetaDictionaryA(sob.Dictionary):
    pass


class BareMetaArrayA(sob.Array):
    pass


def test_dictionary_meta_bare_value_type() -> None:
    dictionary_meta: sob.abc.DictionaryMeta = sob.get_writable_dictionary_meta(
        BareMetaDictionaryA
    )
    dictionary_meta.value_types = sob.StringProperty()  # type: ignore
    assert dictionary_meta.value_types is not None
    assert len(dictionary_meta.value_types) == 1
    assert isinstance(dictionary_meta.value_types[0], sob.StringProperty)


def test_array_meta_bare_item_type() -> None:
    array_meta: sob.abc.ArrayMeta = sob.get_writable_array_meta(BareMetaArrayA)
    array_meta.item_types = str  # type: ignore
    assert array_meta.item_types is not None
    assert len(array_meta.item_types) == 1
    assert array_meta.item_types[0] is str


def test_properties_mapping_protocol() -> None:
    original_properties: sob.abc.Properties | None = (
        sob.get_writable_object_meta(MetaObjectA).properties
    )
    assert original_properties is not None
    properties: sob.abc.Properties = copy(original_properties)
    assert list(properties.values()) == [properties["name"]]
    assert repr(properties)
    assert repr(sob.Properties()) == "sob.Properties()"
    popped: sob.abc.Property = properties.pop("name")
    assert isinstance(popped, sob.StringProperty)
    properties["name"] = popped
    del properties["name"]
    assert "name" not in properties
    properties["name"] = popped
    key, _value = properties.popitem()
    assert key == "name"
    properties.clear()
    assert len(properties) == 0
    assert properties.get("missing") is None
    properties.setdefault("name", sob.StringProperty())
    assert isinstance(properties.get("name"), sob.StringProperty)


def test_properties_setitem_mapped_type() -> None:
    properties: sob.Properties = sob.Properties()
    properties["x"] = str  # type: ignore
    assert isinstance(properties["x"], sob.StringProperty)


def test_properties_setitem_type_error() -> None:
    properties: sob.Properties = sob.Properties()
    error_caught: bool = False
    try:
        properties["bad"] = "not-a-property-or-mapped-type"  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_properties_setdefault_type_error() -> None:
    properties: sob.Properties = sob.Properties()
    error_caught: bool = False
    try:
        properties.setdefault("x", 5)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_properties_update_non_reversible_mapping() -> None:
    properties: sob.Properties = sob.Properties()
    properties.update(MinimalMapping({"name": sob.StringProperty()}))
    assert isinstance(properties["name"], sob.StringProperty)


def test_properties_equality() -> None:
    properties_a: sob.Properties = sob.Properties(
        [("name", sob.StringProperty())]
    )
    properties_b: sob.Properties = sob.Properties(
        [("name", properties_a["name"])]
    )
    assert properties_a == properties_b
    assert properties_a != "not-properties"


def test_read_model_meta_type_error() -> None:
    error_caught: bool = False
    try:
        sob.read_model_meta("not-a-model")  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_read_model_meta_none() -> None:
    assert sob.read_model_meta(MetaObjectNoMeta) is None


def test_get_writable_object_meta_type_error() -> None:
    error_caught: bool = False
    try:
        sob.get_writable_object_meta("not-a-model")  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_model_meta_type() -> None:
    assert sob.meta.get_model_meta_type(MetaObjectA) is sob.ObjectMeta
    assert sob.meta.get_model_meta_type(MetaArrayA) is sob.ArrayMeta
    assert sob.meta.get_model_meta_type(MetaDictionaryA) is sob.DictionaryMeta


def test_get_model_meta_type_errors() -> None:
    error_caught: bool = False
    try:
        sob.meta.get_model_meta_type(42)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught
    error_caught = False
    try:
        sob.meta.get_model_meta_type(str)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_write_model_meta_value_error() -> None:
    error_caught: bool = False
    try:
        sob.write_model_meta(MetaObjectA, sob.ArrayMeta())
    except ValueError:
        error_caught = True
    assert error_caught


def test_write_model_meta_type_error() -> None:
    error_caught: bool = False
    try:
        sob.write_model_meta(str, None)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


class ClassMetaObjectA(sob.Object):
    pass


def test_write_model_meta_class_success() -> None:
    sob.write_model_meta(ClassMetaObjectA, None)
    assert sob.read_model_meta(ClassMetaObjectA) is None
    new_meta: sob.ObjectMeta = sob.ObjectMeta()
    sob.write_model_meta(ClassMetaObjectA, new_meta)
    assert sob.read_model_meta(ClassMetaObjectA) is new_meta


def test_properties_hash() -> None:
    properties: sob.Properties = sob.Properties(
        [("name", sob.StringProperty())]
    )
    assert isinstance(hash(properties), int)


def test_read_object_properties_no_metadata() -> None:
    assert sob.meta._read_object_properties(MetaObjectNoMeta) is None  # noqa: SLF001
    assert sob.meta._read_object_property_names(MetaObjectNoMeta) is None  # noqa: SLF001


def test_read_object_type_error() -> None:
    class FakeObjectMeta(sob.Object):
        pass

    # Force class-level metadata to be a non-`ObjectMeta` instance,
    # bypassing `write_model_meta`'s own type enforcement, to exercise
    # `_read_object`'s defensive type check.
    FakeObjectMeta._class_meta = sob.ArrayMeta()  # type: ignore  # noqa: SLF001
    error_caught: bool = False
    try:
        sob.meta._read_object(FakeObjectMeta)  # noqa: SLF001
    except TypeError:
        error_caught = True
    assert error_caught


def test_pointer_getter_setter() -> None:
    instance: MetaObjectA = MetaObjectA()
    with pytest.warns(DeprecationWarning):
        assert sob.meta.pointer(instance, "/foo/bar") == "/foo/bar"
        assert sob.meta.pointer(instance) == "/foo/bar"


def test_pointer_type_error() -> None:
    error_caught: bool = False
    try:
        sob.meta.pointer(123)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_set_model_url_type_errors() -> None:
    error_caught: bool = False
    try:
        sob.set_model_url(123, "https://example.com")  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught
    error_caught = False
    try:
        sob.set_model_url(MetaObjectA(), 123)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_url_getter_setter() -> None:
    instance: MetaObjectA = MetaObjectA()
    with pytest.warns(DeprecationWarning):
        assert sob.meta.url(instance, "https://example.com") == (
            "https://example.com"
        )
        assert sob.meta.url(instance) == "https://example.com"


class VersionedItemArray(sob.Array):
    def __init__(
        self,
        items: Sequence[str | int] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_array_meta(VersionedItemArray).item_types = sob.Types(
    [
        sob.StringProperty(versions=["test-meta-spec<1.2"]),
        sob.NumberProperty(versions=["test-meta-spec~=1.2"]),
    ]
)


class VersionedValueDictionary(sob.Dictionary):
    def __init__(
        self,
        items: dict[str, str | int] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_dictionary_meta(
    VersionedValueDictionary
).value_types = sob.Types(
    [
        sob.StringProperty(versions=["test-meta-spec<1.2"]),
        sob.NumberProperty(versions=["test-meta-spec~=1.2"]),
    ]
)


def test_version_model_array() -> None:
    array: VersionedItemArray = VersionedItemArray(["a", "b"])
    sob.meta.version_model(array, "test-meta-spec", "1.5")
    item_types: sob.abc.Types | None = sob.read_array_meta(array).item_types  # type: ignore
    assert item_types is not None
    assert len(item_types) == 1
    assert isinstance(item_types[0], sob.NumberProperty)


def test_version_model_dictionary() -> None:
    dictionary: VersionedValueDictionary = VersionedValueDictionary({"a": "x"})
    sob.meta.version_model(dictionary, "test-meta-spec", "1.5")
    value_types: sob.abc.Types | None = sob.read_dictionary_meta(
        dictionary
    ).value_types  # type: ignore
    assert value_types is not None
    assert len(value_types) == 1
    assert isinstance(value_types[0], sob.NumberProperty)


class NoMetaVersionedObject(sob.Object):
    pass


def test_version_model_no_metadata_runtime_error() -> None:
    error_caught: bool = False
    try:
        sob.meta.version_model(NoMetaVersionedObject(), "spec", "1.0")
    except RuntimeError:
        error_caught = True
    assert error_caught


class NestedItemArray(sob.Array):
    def __init__(
        self,
        items: Sequence[MetaObjectA] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_array_meta(NestedItemArray).item_types = sob.Types(
    [MetaObjectA]
)


class NestedValueDictionary(sob.Dictionary):
    def __init__(
        self,
        items: dict[str, MetaObjectA] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_dictionary_meta(
    NestedValueDictionary
).value_types = sob.Types([MetaObjectA])


def test_version_model_recurses_into_array_items() -> None:
    array: NestedItemArray = NestedItemArray([MetaObjectA(name="a")])
    sob.meta.version_model(array, "test-meta-spec", "1.0")
    assert isinstance(array[0], MetaObjectA)


def test_version_model_recurses_into_dictionary_values() -> None:
    dictionary: NestedValueDictionary = NestedValueDictionary(
        {"a": MetaObjectA(name="a")}
    )
    sob.meta.version_model(dictionary, "test-meta-spec", "1.0")
    assert isinstance(dictionary["a"], MetaObjectA)


def test_version_model_type_errors() -> None:
    error_caught: bool = False
    try:
        sob.meta.version_model(42, "spec", "1.0")  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught
    error_caught = False
    try:
        sob.meta.version_model(
            MetaObjectA(),
            "spec",
            object(),  # type: ignore
        )
    except TypeError:
        error_caught = True
    assert error_caught


def test_copy_model_meta_to_type_errors() -> None:
    error_caught: bool = False
    try:
        sob.meta._copy_model_meta_to(  # noqa: SLF001
            "not-a-model",  # type: ignore
            MetaObjectA(),
        )
    except TypeError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
