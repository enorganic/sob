"""
This module defines a class for describing data types associated with a
property.
"""

from copy import deepcopy
from typing import Optional, Sequence, Union, List, Tuple

from .. import abc
from ..abc.properties import Property
from ..utilities import qualified_name
from ..utilities.types import Null, NULL, TYPES as _TYPES, NoneType

__all__: List[str] = [
    'NULL',
    'Null',
    'TYPES',
    'Types',
    'ImmutableTypes'
]


TYPES: Tuple[type, ...] = _TYPES + (
    abc.model.Model,
)


def _validate_type_or_property(
    type_or_property: Union[type, abc.properties.Property]
) -> None:
    if not (
        isinstance(type_or_property, (type, Property)) and
        (
            (type_or_property is Null) or
            (
                isinstance(type_or_property, type) and
                issubclass(
                    type_or_property, TYPES
                )
            ) or
            isinstance(type_or_property, Property)
        )
    ):
        raise TypeError(type_or_property)


class Types(list):
    """
    Instances of this class are lists which will only take values which are
    valid types for describing a property definition.

    Parameters:

    - items ([type|sob.properties.Property])
    - mutable (bool)
    """
    _mutable: bool = True

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

    def _mutability_check(self) -> None:
        if not self._mutable:
            raise TypeError(
                f'Instances of `{qualified_name(type(self))}` cannot be '
                'modified.'
            )

    def __setitem__(self, index: int, value: Union[type, Property]) -> None:
        self._mutability_check()
        _validate_type_or_property(value)
        super().__setitem__(index, value)

    def append(
        self,
        value: Union[type, Property]
    ) -> None:
        self._mutability_check()
        _validate_type_or_property(value)
        super().append(value)

    def __delitem__(self, index: int) -> None:
        self._mutability_check()
        super().__delitem__(index)

    def pop(self, index: int = -1) -> Union[type, Property]:
        self._mutability_check()
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


abc.properties.types.Types.register(Types)


class ImmutableTypes(Types):

    _mutable: bool = False


abc.properties.types.Types.register(ImmutableTypes)
abc.properties.types.ImmutableTypes.register(ImmutableTypes)


