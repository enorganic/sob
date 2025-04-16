from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from typing_extensions import Self

from sob import abc
from sob._types import NULL, UNDEFINED, NoneType, Null, Undefined
from sob.utilities import get_qualified_name

__all__: tuple[str, ...] = (
    "Null",
    "NULL",
    "Undefined",
    "UNDEFINED",
    "Types",
    "MutableTypes",
    "NoneType",
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


class Types(abc.Types):
    """
    Instances of this class are immutable lists of types and/or
    property definitions.
    """

    __module__: str = "sob"

    def __init__(
        self,
        items: abc.Types
        | Iterable[type | abc.Property]
        | type
        | abc.Property
        | None = None,
    ) -> None:
        if isinstance(items, (type, abc.Property)):
            items = (items,)
        self._list: list[type | abc.Property] = []
        if items is not None:
            self._extend(items)

    def __copy__(self) -> abc.Types:
        return self.__class__(self)

    def __deepcopy__(self, memo: dict | None = None) -> abc.Types:
        value: type | abc.Property
        return self.__class__(
            tuple(copy.deepcopy(value, memo=memo) for value in self)
        )

    def __repr__(self) -> str:
        # Represent the class by it's fully-qualified type name
        representation = [get_qualified_name(type(self)) + "("]
        # If it is not empty--we represent the values as a `list`
        if self:
            representation[0] += "["
            for value in self.__iter__():
                value_representation: str = "\n".join(
                    "    " + line
                    for line in (
                        get_qualified_name(value)
                        if isinstance(value, type)
                        else repr(value)
                    ).split("\n")
                )
                representation.append(f"{value_representation},")
            representation[-1] = representation[-1].rstrip(",")
            representation.append("]")
        representation[-1] += ")"
        # Return a single-line representation if this is an empty list of
        # types, otherwise--break it into multiple lines
        return (
            "\n".join(representation)
            if len(representation) > 2  # noqa: PLR2004
            else "".join(representation)
        )

    def __contains__(
        self,
        item: type | abc.Property,  # type: ignore
    ) -> bool:
        return self._list.__contains__(item)

    def __iter__(
        self,
    ) -> Iterator[type | abc.Property]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def _append(self, value: type | abc.Property) -> None:
        _validate_type_or_property(value)
        self._list.append(value)

    def _extend(
        self,
        values: Iterable[type | abc.Property] | abc.Types,
    ) -> None:
        value: type | abc.Property
        for value in values:
            self._append(value)

    def __getitem__(self, index: int) -> type | abc.Property:
        return self._list.__getitem__(index)


class MutableTypes(Types, abc.MutableTypes):
    """
    Instances of this class are (mutable) lists of types and/or
    property definitions.
    """

    __module__: str = "sob"

    def __setitem__(self, index: int, value: type | abc.Property) -> None:
        _validate_type_or_property(value)
        self._list.__setitem__(index, value)

    def append(self, value: type | abc.Property) -> None:
        self._append(value)

    def extend(self, values: Iterable[type | abc.Property]) -> None:
        self._extend(values)

    def __delitem__(self, index: int | slice) -> None:
        self._list.__delitem__(index)

    def pop(self, index: int = -1) -> type | abc.Property:
        return self._list.pop(index)

    def __iadd__(self, other: Iterable[type | abc.Property]) -> Self:
        self.extend(other)
        return self

    def __add__(
        self, other: Iterable[type | abc.Property]
    ) -> abc.MutableTypes:
        new_instance: abc.Types = copy.copy(self)
        if not isinstance(new_instance, abc.MutableTypes):
            raise TypeError(new_instance)
        new_instance.extend(other)
        return new_instance


def _validate_type_or_property(
    type_or_property: type[abc.Property] | abc.Property,
) -> None:
    if not (
        isinstance(type_or_property, (type, abc.Property))
        and (
            (type_or_property is Null)
            or (
                isinstance(type_or_property, type)
                and issubclass(type_or_property, abc.MARSHALLABLE_TYPES)
            )
            or isinstance(type_or_property, abc.Property)
        )
    ):
        raise TypeError(type_or_property)
