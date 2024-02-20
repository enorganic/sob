"""
This module tests the application of version-specific properties and types to
model instances
"""

from typing import IO, Dict, List, Optional, Sequence, Set, Union

import sob

# region Declare classes


class MemberObjectA(sob.model.Object):
    def __init__(
        self,
        _data: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        property_a: Optional[int] = None,
        property_b: Optional[str] = None,
        property_c: Optional[Union[str, int, sob.types.Null]] = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        super().__init__(_data)


class MemberObjectB(sob.model.Object):
    def __init__(
        self,
        _data: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        property_a: Optional[Union[str, int, sob.types.Null]] = None,
        property_b: Optional[int] = None,
        property_c: Optional[str] = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        super().__init__(_data)


class MemberObjectC(sob.model.Object):
    def __init__(
        self,
        _data: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        property_a: Optional[Union[str, int, sob.types.Null]] = None,
        property_b: Optional[int] = None,
        property_c: Optional[str] = None,
        property_d: Optional[str] = None,
    ) -> None:
        self.property_a = property_a
        self.property_b = property_b
        self.property_c = property_c
        self.property_d = property_d
        super().__init__(_data)


class MemberDictionaryA(sob.model.Dictionary):
    def __init__(
        self,
        items: Optional[
            Union[Dict[str, MemberObjectA], IO, str, bytes]
        ] = None,
    ) -> None:
        super().__init__(items)


class MemberDictionaryB(sob.model.Dictionary):
    def __init__(
        self,
        items: Optional[
            Union[
                Dict[str, Union[MemberObjectA, MemberObjectB]], IO, str, bytes
            ]
        ] = None,
    ) -> None:
        super().__init__(items)


class MemberDictionaryC(sob.model.Dictionary):
    def __init__(
        self,
        items: Optional[
            Union[
                Dict[
                    str,
                    List[Union[MemberObjectA, MemberObjectB, MemberObjectC]],
                ],
                IO,
                str,
                bytes,
            ]
        ] = None,
    ) -> None:
        super().__init__(items)


class MemberArrayA(sob.model.Array):
    def __init__(
        self,
        items: Optional[
            Union[Sequence[MemberObjectA], Set[MemberObjectA], str, bytes, IO]
        ] = None,
    ) -> None:
        super().__init__(items)


class MemberArrayB(sob.model.Array):
    def __init__(
        self,
        items: Optional[
            Union[Sequence[MemberObjectB], Set[MemberObjectB], str, bytes, IO]
        ] = None,
    ) -> None:
        super().__init__(items)


class MemberArrayC(sob.model.Array):
    def __init__(
        self,
        items: Optional[
            Union[
                Sequence[Union[MemberObjectA, MemberObjectB, MemberObjectC]],
                Set[Union[MemberObjectA, MemberObjectB, MemberObjectC]],
                str,
                bytes,
                IO,
            ]
        ] = None,
    ) -> None:
        super().__init__(items)


class VersionedObject(sob.model.Object):
    """
    This class has metadata which dynamically alters constraints on the
    object's polymorphic potential, based on a specification + version.
    """

    def __init__(
        self,
        _data: Optional[str] = None,
        version: Optional[Union[str, int, float]] = None,
        versioned_simple_type: Optional[Union[str, int]] = None,
        versioned_container: Optional[
            Union[
                MemberObjectA,
                MemberObjectB,
                MemberObjectC,
                MemberArrayA,
                MemberArrayB,
                MemberArrayC,
                MemberDictionaryA,
                MemberDictionaryB,
                MemberDictionaryC,
            ]
        ] = None,
    ) -> None:
        self.version: Optional[str] = None
        self.versioned_simple_type: Optional[Union[str, int]] = None
        self.versioned_container: Optional[
            Union[
                MemberObjectA,
                MemberObjectB,
                MemberObjectC,
                MemberArrayA,
                MemberArrayB,
                MemberArrayC,
                MemberDictionaryA,
                MemberDictionaryB,
                MemberDictionaryC,
            ]
        ] = None
        super().__init__(_data)
        sob.meta.version(self, "test-specification", version)
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


def test_version_1():
    versioned_object: VersionedObject
    caught_error: Exception
    error: Optional[Exception] = None
    # Verify that setting the version to a non-string raises an error
    # when the version is < 1.2
    try:
        VersionedObject(version=1.0)
    except TypeError as caught_error:  # noqa
        error = caught_error
    assert isinstance(error, TypeError)
    # Verify that setting the version to a non-string raises no error
    # when the version is >= 1.2
    VersionedObject(version=1.2)


def test_version_2():
    pass


def test_version_3():
    pass


def test_version_4():
    pass


def test_version_5():
    pass


if __name__ == "__main__":
    test_version_1()
