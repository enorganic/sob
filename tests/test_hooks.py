from __future__ import annotations

from typing import IO, TYPE_CHECKING

import pytest

import sob

if TYPE_CHECKING:
    from collections.abc import Sequence

# region Declare classes


class HookedObject(sob.Object):
    __slots__: tuple[str, ...] = ("value",)

    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        value: str | None = None,
    ) -> None:
        self.value: str | None = value
        super().__init__(_data)


sob.get_writable_object_meta(HookedObject).properties = sob.Properties(
    [("value", sob.StringProperty())]
)


class HookedArray(sob.Array):
    def __init__(
        self,
        items: Sequence[str] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_array_meta(HookedArray).item_types = sob.Types([str])


class HookedDictionary(sob.Dictionary):
    def __init__(
        self,
        items: dict[str, str] | str | bytes | IO | None = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_dictionary_meta(HookedDictionary).value_types = sob.Types(
    [str]
)


class PlainObjectA(sob.Object):
    pass


class PlainObjectB(sob.Object):
    pass


class PlainObjectC(sob.Object):
    pass


# endregion


def test_object_hooks() -> None:
    calls: list[tuple[str, str, str | None]] = []

    def before_setattr(
        instance: sob.Object, name: str, value: str | None
    ) -> tuple[str, str | None]:
        calls.append(("before_setattr", name, value))
        return name, value

    def after_setattr(
        instance: sob.Object, name: str, value: str | None
    ) -> None:
        calls.append(("after_setattr", name, value))

    sob.write_model_hooks(
        HookedObject,
        sob.ObjectHooks(
            before_setattr=before_setattr,  # type: ignore
            after_setattr=after_setattr,  # type: ignore
        ),
    )
    instance: HookedObject = HookedObject()
    instance.value = "hi"
    assert ("before_setattr", "value", "hi") in calls
    assert ("after_setattr", "value", "hi") in calls


def test_array_hooks() -> None:
    calls: list[tuple[str, str]] = []

    def before_append(array: sob.Array, value: str) -> str:
        calls.append(("before_append", value))
        return value

    def after_append(array: sob.Array, value: str) -> None:
        calls.append(("after_append", value))

    sob.write_model_hooks(
        HookedArray,
        sob.ArrayHooks(
            before_append=before_append,  # type: ignore
            after_append=after_append,  # type: ignore
        ),
    )
    array: HookedArray = HookedArray()
    array.append("x")
    assert ("before_append", "x") in calls
    assert ("after_append", "x") in calls


def test_dictionary_hooks() -> None:
    calls: list[tuple[str, str, str]] = []

    def before_setitem(
        dictionary: sob.Dictionary, key: str, value: str
    ) -> tuple[str, str]:
        calls.append(("before_setitem", key, value))
        return key, value

    def after_setitem(
        dictionary: sob.Dictionary, key: str, value: str
    ) -> None:
        calls.append(("after_setitem", key, value))

    sob.write_model_hooks(
        HookedDictionary,
        sob.DictionaryHooks(
            before_setitem=before_setitem,  # type: ignore
            after_setitem=after_setitem,  # type: ignore
        ),
    )
    dictionary: HookedDictionary = HookedDictionary()
    dictionary["k"] = "v"
    assert ("before_setitem", "k", "v") in calls
    assert ("after_setitem", "k", "v") in calls


def test_read_model_hooks_type_error() -> None:
    error_caught: bool = False
    try:
        sob.read_model_hooks("not-a-model")  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_writable_model_hooks_class_creates_and_persists() -> None:
    hooks1: sob.abc.Hooks = sob.get_writable_model_hooks(PlainObjectA)
    assert isinstance(hooks1, sob.ObjectHooks)
    hooks2: sob.abc.Hooks | None = sob.read_model_hooks(PlainObjectA)
    assert hooks2 is hooks1


def test_get_writable_model_hooks_instance_creates() -> None:
    instance: PlainObjectB = PlainObjectB()
    instance_hooks: sob.abc.Hooks = sob.get_writable_model_hooks(instance)
    assert isinstance(instance_hooks, sob.ObjectHooks)


def test_get_writable_model_hooks_type_error() -> None:
    error_caught: bool = False
    try:
        sob.get_writable_model_hooks(42)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_writable_object_hooks() -> None:
    assert isinstance(
        sob.get_writable_object_hooks(HookedObject), sob.ObjectHooks
    )


def test_get_writable_array_hooks() -> None:
    assert isinstance(
        sob.get_writable_array_hooks(HookedArray), sob.ArrayHooks
    )


def test_get_writable_dictionary_hooks() -> None:
    assert isinstance(
        sob.get_writable_dictionary_hooks(HookedDictionary),
        sob.DictionaryHooks,
    )


def test_get_model_hooks_type() -> None:
    assert sob.get_model_hooks_type(HookedObject) is sob.ObjectHooks
    assert sob.get_model_hooks_type(HookedObject()) is sob.ObjectHooks
    assert sob.get_model_hooks_type(HookedArray) is sob.ArrayHooks
    assert sob.get_model_hooks_type(HookedDictionary) is sob.DictionaryHooks


def test_get_model_hooks_type_non_type_type_error() -> None:
    # Neither a `type`, `Object`, `Dictionary`, nor `Array` instance.
    error_caught: bool = False
    try:
        sob.get_model_hooks_type(42)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_model_hooks_type_wrong_class_type_error() -> None:
    # A real `type`, but not a `Model` subclass.
    error_caught: bool = False
    try:
        sob.get_model_hooks_type(str)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_write_model_hooks_value_error() -> None:
    error_caught: bool = False
    try:
        sob.write_model_hooks(HookedObject, sob.ArrayHooks())
    except ValueError:
        error_caught = True
    assert error_caught


def test_write_model_hooks_instance_clears_hooks() -> None:
    # `PlainObjectC` has no class-level hooks, so instance-level state is
    # unambiguous: assigning `None` after assigning real hooks clears it.
    instance: PlainObjectC = PlainObjectC()
    sob.write_model_hooks(instance, sob.ObjectHooks())
    assert sob.read_model_hooks(instance) is not None
    sob.write_model_hooks(instance, None)
    assert sob.read_model_hooks(instance) is None


def test_write_model_hooks_type_error() -> None:
    # A real `type`, but not a `Model` subclass.
    error_caught: bool = False
    try:
        sob.write_model_hooks(str, None)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
