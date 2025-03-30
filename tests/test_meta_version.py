"""
This module tests the application of version-specific properties and types to
model instances
"""

from __future__ import annotations

from typing import IO, TYPE_CHECKING

import pytest

import sob

if TYPE_CHECKING:
    from collections.abc import Sequence

# region Declare classes


class MemberObjectA(sob.model.Object):
    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        property_a: int | None = None,
        property_b: str | None = None,
        property_c: str | int | sob.types.Null | None = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        super().__init__(_data)


class MemberObjectB(sob.model.Object):
    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        property_a: str | int | sob.types.Null | None = None,
        property_b: int | None = None,
        property_c: str | None = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        super().__init__(_data)


class MemberObjectC(sob.model.Object):
    def __init__(
        self,
        _data: str | bytes | dict | Sequence | IO | None = None,
        property_a: str | int | sob.types.Null | None = None,
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


class VersionedObject(sob.model.Object):
    """
    This class has metadata which dynamically alters constraints on the
    object's polymorphic potential, based on a specification + version.
    """

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
        sob.meta.version(self, "test-specification", str(version))  # type: ignore
        self.version = version
        self.versioned_simple_type = versioned_simple_type
        self.versioned_container = versioned_container


# endregion
# region Metadata

sob.meta.writable(VersionedObject).properties = [
    (
        "version",
        sob.properties.Property(
            types=[
                # For versions prior to 1.2, the property value *must* be a
                # string
                sob.properties.String(versions=["test-specification<1.2"]),
                # For versions greater than or equal to 1.2 and less than 2.0,
                # the property value can be a string, float, or integer.
                sob.properties.Number(versions=["test-specification~=1.2"]),
            ]
        ),
    ),
    (
        "versioned_simple_type",
        # Simple types can be identified with either an instance of
        # `sob.properties.Property`, *or* the `type` itself.
        sob.properties.Property(name="versionedSimpleType", types=[str, int]),
    ),
    (
        "versioned_container",
        sob.properties.Property(name="versionedContainer"),
    ),
]

sob.meta.writable(MemberObjectA).properties = [
    ("property_a", sob.properties.Integer(name="propertyA"))
]

# endregion


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


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
