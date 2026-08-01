"""
This module tests the application of version-specific properties and types to
model instances
"""

from __future__ import annotations

import doctest
from typing import IO, TYPE_CHECKING

import pytest

import sob

if TYPE_CHECKING:
    from collections.abc import Sequence

# region Declare classes


class MemberObjectA(sob.Object):
    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        property_a: int | None = None,
        property_b: str | None = None,
        property_c: str | int | sob.Null | None = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        super().__init__(_data)


class MemberObjectB(sob.Object):
    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        property_a: str | int | sob.Null | None = None,
        property_b: int | None = None,
        property_c: str | None = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        super().__init__(_data)


class MemberObjectC(sob.Object):
    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        property_a: str | int | sob.Null | None = None,
        property_b: int | None = None,
        property_c: str | None = None,
        property_d: str | None = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        self.property_d = property_d
        super().__init__(_data)


class MemberDictionaryA(sob.model.Dictionary):
    def __init__(
        self,
        items: dict[str, MemberObjectA] | IO | str | bytes | None = None,
    ) -> None:
        super().__init__(items)


class MemberDictionaryB(sob.model.Dictionary):
    def __init__(
        self,
        items: dict[str, MemberObjectA | MemberObjectB]
        | IO
        | str
        | bytes
        | None = None,
    ) -> None:
        super().__init__(items)


class MemberDictionaryC(sob.model.Dictionary):
    def __init__(
        self,
        items: dict[str, list[MemberObjectA | MemberObjectB | MemberObjectC]]
        | IO
        | str
        | bytes
        | None = None,
    ) -> None:
        super().__init__(items)


class MemberArrayA(sob.model.Array):
    def __init__(
        self,
        items: Sequence[MemberObjectA]
        | set[MemberObjectA]
        | str
        | bytes
        | IO
        | None = None,
    ) -> None:
        super().__init__(items)


class MemberArrayB(sob.model.Array):
    def __init__(
        self,
        items: Sequence[MemberObjectB]
        | set[MemberObjectB]
        | str
        | bytes
        | IO
        | None = None,
    ) -> None:
        super().__init__(items)


class MemberArrayC(sob.model.Array):
    def __init__(
        self,
        items: Sequence[MemberObjectA | MemberObjectB | MemberObjectC]
        | set[MemberObjectA | MemberObjectB | MemberObjectC]
        | str
        | bytes
        | IO
        | None = None,
    ) -> None:
        super().__init__(items)


class VersionedObject(sob.Object):
    """
    This class has metadata which dynamically alters constraints on the
    object's polymorphic potential, based on a specification + version.
    """

    __slots__: tuple[str, ...] = (
        "version",
        "versioned_container",
        "versioned_simple_type",
    )

    def __init__(
        self,
        _data: str | None = None,
        version: str | float | Sequence[int] | None = None,
        versioned_simple_type: str | int | None = None,
        versioned_container: MemberObjectA
        | MemberObjectB
        | MemberObjectC
        | MemberArrayA
        | MemberArrayB
        | MemberArrayC
        | MemberDictionaryA
        | MemberDictionaryB
        | MemberDictionaryC
        | None = None,
    ) -> None:
        self.version: str | float | Sequence[int] | None = None
        self.versioned_simple_type: str | int | None = None
        self.versioned_container: (
            MemberObjectA
            | MemberObjectB
            | MemberObjectC
            | MemberArrayA
            | MemberArrayB
            | MemberArrayC
            | MemberDictionaryA
            | MemberDictionaryB
            | MemberDictionaryC
            | None
        ) = None
        super().__init__(_data)
        sob.meta.version_model(self, "test-specification", str(version))
        self.version = version
        self.versioned_simple_type = versioned_simple_type
        self.versioned_container = versioned_container


# endregion
# region Metadata


sob.meta.get_writable_object_meta(
    VersionedObject
).properties = sob.meta.Properties(
    [
        (
            "version",
            sob.properties.Property(
                types=[
                    # For versions prior to 1.2, the property value *must* be a
                    # string
                    sob.StringProperty(versions=["test-specification<1.2"]),
                    # For versions greater than or equal to 1.2 and less than
                    # 2.0, the property value can be a string, float, or
                    # integer.
                    sob.NumberProperty(versions=["test-specification~=1.2"]),
                ]
            ),
        ),
        (
            "versioned_simple_type",
            # Simple types can be identified with either an instance of
            # `sob.properties.Property`, *or* the `type` itself.
            sob.properties.Property(
                name="versionedSimpleType", types=[str, int]
            ),
        ),
        (
            "versioned_container",
            sob.properties.Property(name="versionedContainer"),
        ),
    ]
)

sob.meta.get_writable_object_meta(
    MemberObjectA
).properties = sob.meta.Properties(
    [("property_a", sob.IntegerProperty(name="propertyA"))]
)

# endregion


def test_doctest() -> None:
    """
    Run docstring tests
    """
    results: doctest.TestResults = doctest.testmod(sob.version)
    assert results.failed == 0, results


def test_version_1() -> None:
    versioned_object: VersionedObject
    caught_error: Exception
    error: Exception | None = None
    # Verify that setting the version to a non-string raises an error
    # when the version is < 1.2
    try:
        VersionedObject(version=1.0)  # type: ignore
    except TypeError as caught_error:
        error = caught_error
    else:
        message: str = "A float version should raise a TypeError"
        raise RuntimeError(message)
    assert isinstance(error, TypeError), type(error).__name__
    # Verify that setting the version to a non-string raises no error
    # when the version is >= 1.2
    VersionedObject(version=1.2)


def test_version_equality_precision() -> None:
    assert sob.Version(equals="1.2") == "1.2.0"
    assert sob.Version(equals="1.2") == "1.2"


def test_version_compatible_with_precision() -> None:
    # `other` has *less* precision than `compatible_with`
    assert sob.Version(compatible_with="1.2.3") == "1"
    # `compatible_with` has only one version component
    assert sob.Version(compatible_with="1") != "1.5"
    # Ordinary same-minor-version compatibility
    assert sob.Version(compatible_with="1.2") == "1.2.5"


def test_version_string_value_error() -> None:
    error_caught: bool = False
    try:
        bool(sob.Version(equals="1.0") == "not-a-version")
    except ValueError:
        error_caught = True
    assert error_caught


def test_version_numeric_and_sequence_inputs() -> None:
    assert sob.Version(compatible_with=1.2) == "1.2"  # type: ignore
    assert sob.Version(compatible_with=(1, 2)) == "1.2"


def test_version_as_tuple_type_error() -> None:
    error_caught: bool = False
    try:
        sob.version._version_as_tuple(object())  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_version_string_type_error() -> None:
    error_caught: bool = False
    try:
        sob.Version(123)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_version_conflicting_specifications() -> None:
    error_caught: bool = False
    try:
        sob.Version("a==1,b==2")
    except ValueError:
        error_caught = True
    assert error_caught


def test_version_str_no_specification() -> None:
    version: sob.Version = sob.Version(equals="1.0")
    version.specification = None  # type: ignore
    error_caught: bool = False
    try:
        str(version)
    except RuntimeError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
