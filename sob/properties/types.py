"""
This module defines a class for describing data types associated with a
property.
"""

import collections.abc
import decimal
import numbers
from copy import deepcopy
from datetime import date, datetime
from typing import Any, Dict, Generator, Hashable, Optional, Sequence, Union

from .. import abc
from ..abc.properties import Property
from ..utilities import qualified_name

NoneType = type(None)
NULL: Optional['Null'] = None


class DefinitionExistsError(Exception):

    pass


class Null:
    """
    Instances of this class represent an *explicit* null value, rather than the
    absence of a property/attribute/element, as would be inferred from a value
    of `None`.

    Note: Like the built-in value `None`, only one instance of this class is
    permitted, so this class should never be instantiated, it should always be
    referenced through the constant `NULL` from this same module.
    """

    def __init__(self) -> None:
        if NULL is not None:
            raise DefinitionExistsError(
                '%s may only be defined once.' % repr(self)
            )

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return id(other) == id(self)

    def __hash__(self) -> int:
        return 0

    def __str__(self) -> str:
        return 'null'

    def _marshal(self) -> None:
        return None

    def __repr__(self) -> str:
        return (
            'NULL'
            if self.__module__ in ('__main__', 'builtins', '__builtin__') else
            '%s.NULL' % self.__module__
        )

    def __copy__(self) -> 'Null':
        return self

    def __deepcopy__(self, memo: Dict[Hashable, Any]) -> 'Null':
        return self


locals()['NULL'] = Null()


TYPES = (
    str, bytes, bool,
    dict, collections.OrderedDict,
    collections.abc.Set, collections.abc.Sequence, Generator,
    numbers.Number, decimal.Decimal,
    date, datetime,
    abc.model.Model,
    Null
)


def _validate_type_or_property(
    type_or_property: Union[type, abc.properties.Property]
) -> Union[type, abc.properties.Property]:
    if not isinstance(type_or_property, (type, Property)):
        raise TypeError(type_or_property)
    if not (
        (type_or_property is Null) or
        (
            isinstance(type_or_property, type) and
            issubclass(
                type_or_property,
                TYPES
            )
        ) or
        isinstance(type_or_property, Property)
    ):
        raise TypeError(type_or_property)
    return type_or_property


class Types(list):
    """
    Instances of this class are lists which will only take values which are
    valid types for describing a property definition.
    """

    def __init__(
        self,
        items: Optional[
            Union[
                Sequence[
                    Union[type, abc.properties.Property]
                ],
                type,
                abc.properties.Property
            ]
        ] = None
    ) -> None:
        if isinstance(items, (type, Property)):
            items = (items,)
        if items is None:
            super().__init__()
        else:
            super().__init__(items)

    def __setitem__(self, index: int, value: Union[type, Property]) -> None:
        _validate_type_or_property(value)
        super().__setitem__(index, value)

    def append(
        self,
        value: Union[type, Property]
    ) -> None:
        _validate_type_or_property(value)
        super().append(value)

    def __delitem__(self, index: int) -> None:
        super().__delitem__(index)

    def pop(self, index: int = -1) -> Union[type, Property]:
        return super().pop(index)

    def __copy__(self) -> 'Types':
        return self.__class__(self)

    def __deepcopy__(self, memo: dict = None) -> 'Types':
        return self.__class__(
            tuple(
                deepcopy(v, memo=memo)
                for v in self
            )
        )

    def __repr__(self):
        # Represent the class by it's fully-qualified type name
        representation = [
            qualified_name(type(self)) + '('
        ]
        # If it is not empty--we represent the values as a `list`
        if self:
            representation[0] += '['
            for value in self:
                value_representation: str = '\n'.join(
                    '    ' + line
                    for line in (
                        qualified_name(value)
                        if isinstance(value, type) else
                        repr(value)
                    ).split('\n')
                )
                representation.append(
                    f'{value_representation},'
                )
            representation[-1] = representation[-1].rstrip(',')
            representation.append(
                ']'
            )
        representation[-1] += ')'
        # Return a single-line representation if this is an empty list of
        # types, otherwise--break it into multiple lines
        return (
            '\n'.join(representation)
            if len(representation) > 2 else
            ''.join(representation)
        )


abc.properties.Types.register(Types)
