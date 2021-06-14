import copy
from typing import Iterable, Iterator, List, NoReturn, Optional, Type, Union

from . import abc
from .utilities.inspect import qualified_name
from .utilities.types import Null


class Types(abc.Types):
    def __init__(
        self,
        items: Optional[
            Union[
                abc.Types,
                Iterable[Union[type, abc.Property]],
                type,
                abc.Property,
            ]
        ] = None,
    ) -> None:
        if isinstance(items, (type, abc.Property)):
            items = (items,)
        self._list: List[Union[type, abc.Property]] = []
        if items is not None:
            self._extend(items)

    @classmethod
    def _raise_immutable_type_error(cls) -> NoReturn:
        raise TypeError(
            f"Instances of `{qualified_name(cls)}` cannot be " "modified."
        )

    def __copy__(self) -> abc.Types:
        return self.__class__(self)

    def __deepcopy__(self, memo: Optional[dict] = None) -> abc.Types:
        value: Union[type, abc.Property]
        return self.__class__(
            tuple(
                getattr(copy, "deepcopy")(value, memo=memo) for value in self
            )
        )

    def __repr__(self) -> str:
        # Represent the class by it's fully-qualified type name
        representation = [qualified_name(type(self)) + "("]
        # If it is not empty--we represent the values as a `list`
        if self:
            representation[0] += "["
            for value in self.__iter__():
                value_representation: str = "\n".join(
                    "    " + line
                    for line in (
                        qualified_name(value)
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
            if len(representation) > 2
            else "".join(representation)
        )

    def __contains__(
        self, item: Union[type, abc.Property]  # type: ignore
    ) -> bool:
        return self._list.__contains__(item)

    def __iter__(  # type: ignore
        self,
    ) -> Iterator[Union[type, abc.Property]]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def _append(self, value: Union[type, abc.Property]) -> None:
        _validate_type_or_property(value)
        self._list.append(value)

    def _extend(
        self,
        values: Union[Iterable[Union[type, abc.Property]], abc.Types],
    ) -> None:
        value: Union[type, abc.Property]
        for value in values:
            self._append(value)

    def __getitem__(self, index: int) -> Union[type, abc.Property]:
        return self._list.__getitem__(index)


class MutableTypes(Types, abc.MutableTypes):
    """
    Instances of this class are lists which will only take values which are
    valid types for describing a property definition.

    Parameters:

    - items ([type|sob.properties.Property])
    - mutable (bool)
    """

    def __setitem__(
        self, index: int, value: Union[type, abc.Property]
    ) -> None:
        _validate_type_or_property(value)
        self._list.__setitem__(index, value)

    def append(self, value: Union[type, abc.Property]) -> None:
        self._append(value)

    def extend(self, values: Iterable[Union[type, abc.Property]]) -> None:
        self._extend(values)

    def __delitem__(self, index: Union[int, slice]) -> None:
        self._list.__delitem__(index)

    def pop(self, index: int = -1) -> Union[type, abc.Property]:
        return self._list.pop(index)

    def __iadd__(
        self, other: Iterable[Union[type, abc.Property]]
    ) -> abc.MutableTypes:
        self.extend(other)
        return self

    def __add__(
        self, other: Iterable[Union[type, abc.Property]]
    ) -> abc.MutableTypes:
        new_instance: abc.Types = copy.copy(self)
        assert isinstance(new_instance, abc.MutableTypes)
        new_instance.extend(other)
        return new_instance


def _validate_type_or_property(
    type_or_property: Union[Type[abc.Property], abc.Property]
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
