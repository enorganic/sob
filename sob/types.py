from copy import deepcopy
from typing import Any, Iterable, Optional, Tuple, Type, Union

from . import abc
from .utilities.types import TYPES as _TYPES
from .utilities.inspect import qualified_name
from .utilities.types import Null

TYPES: Tuple[type, ...] = _TYPES + (
    abc.model.Model,
)


# noinspection PyUnresolvedReferences
@abc.types.Types.register
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
                Iterable[
                    Union[
                        type,
                        abc.properties.Property
                    ]
                ],
                type,
                abc.properties.Property
            ]
        ] = None
    ) -> None:
        if isinstance(items, (type, abc.properties.Property)):
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

    def __setitem__(  # type: ignore
        self,
        index: int,
        value: Union[type, abc.properties.Property]
    ) -> Any:
        self._mutability_check()
        _validate_type_or_property(value)
        super().__setitem__(index, value)

    def append(
        self,
        value: Union[type, abc.properties.Property]
    ) -> None:
        self._mutability_check()
        _validate_type_or_property(value)
        super().append(value)

    def __delitem__(self, index: Union[int, slice]) -> None:
        self._mutability_check()
        super().__delitem__(index)

    def pop(self, index: int = -1) -> Union[type, abc.properties.Property]:
        self._mutability_check()
        return super().pop(index)

    def __copy__(self) -> 'Types':
        return self.__class__(self)

    # noinspection PyArgumentList
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


# noinspection PyUnresolvedReferences
@abc.types.Types.register
@abc.types.ImmutableTypes.register
class ImmutableTypes(Types):

    _mutable: bool = False


def _validate_type_or_property(
    type_or_property: Union[
        Type[abc.properties.Property], abc.properties.Property
    ]
) -> None:
    if not (
        isinstance(type_or_property, (type, abc.properties.Property)) and
        (
            (type_or_property is Null) or
            (
                isinstance(type_or_property, type) and
                issubclass(
                    type_or_property, TYPES
                )
            ) or
            isinstance(type_or_property, abc.properties.Property)
        )
    ):
        raise TypeError(type_or_property)