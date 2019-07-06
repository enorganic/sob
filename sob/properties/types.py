from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
   print_function, unicode_literals
)
from sob.utilities import compatibility
compatibility.backport()
from future.utils import native_str
import numbers
import decimal
import collections
from copy import deepcopy
from datetime import date, datetime
from ..utilities import compatibility, qualified_name
from .. import abc
from ..abc.properties import Property

compatibility.backport()

collections_abc = compatibility.collections_abc
Generator = compatibility.Generator
Union = compatibility.typing.Union
Optional = compatibility.typing.Optional
Sequence = compatibility.typing.Sequence
Mapping = compatibility.typing.Mapping
Set = compatibility.typing.Set
Callable = compatibility.typing.Callable
Dict = compatibility.typing.Dict
Any = compatibility.typing.Any
Hashable = compatibility.typing.Hashable
Collection = compatibility.typing.Collection
Tuple = compatibility.typing.Tuple

if Any is not None:
    _TypeOrProperty = Union[type, abc.properties.Property]
    _ItemsParameter = Optional[
        Union[
            Sequence[
                _TypeOrProperty
            ],
            type,
            abc.properties.Property
        ]
    ]


NoneType = type(None)
NULL = None


class DefinitionExistsError(Exception):

    pass


class Null(object):  # noqa - inheriting from `object` needed for python 2x
    """
    Instances of this class represent an *explicit* null value, rather than the
    absence of a property/attribute/element, as would be inferred from a value
    of `None`.
    """

    def __init__(self):
        if NULL is not None:
            raise DefinitionExistsError(
                '%s may only be defined once.' % repr(self)
            )

    def __bool__(self):
        # type: (...) -> bool
        return False

    def __eq__(self, other):
        # type: (Any) -> bool
        return id(other) == id(self)

    def __hash__(self):
        # type: (...) -> int
        return 0

    def __str__(self):
        # type: (...) -> str
        return 'null'

    def _marshal(self):
        # type: (...) -> None
        return None

    def __repr__(self):
        # type: (...) -> str
        return (
            'NULL'
            if self.__module__ in ('__main__', 'builtins', '__builtin__') else
            '%s.NULL' % self.__module__
        )

    def __copy__(self):
        # type: (...) -> Null
        return self

    def __deepcopy__(self, memo):
        # type: (Dict[Hashable, Any]) -> Null
        return self


locals()['NULL'] = Null()


TYPES = tuple(
    # We first put all the types in a `set` so that when `native_str` and `str`
    # are the same--they are not duplicated
    {
        str, bytes, bool,
        dict, collections.OrderedDict,
        collections_abc.Set, collections_abc.Sequence, Generator,
        native_str,
        numbers.Number, decimal.Decimal,
        date, datetime,
        abc.model.Model,
        Null
    }
)


def _validate_type_or_property(type_or_property):
    # type: (_TypeOrProperty) -> _TypeOrProperty
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
        items=None  # type: _ItemsParameter
    ):
        if isinstance(items, (type, Property)):
            items = (items,)
        if items is None:
            super().__init__()
        else:
            super().__init__(items)

    def __setitem__(self, index, value):
        # type: (int, Union[type, Property]) -> None
        super().__setitem__(index, _validate_type_or_property(value))
        if value is str and (native_str is not str) and (
            native_str not in self
        ):
            super().append(native_str)

    def append(self, value):
        # type: (Union[type, Property]) -> None
        super().append(_validate_type_or_property(value))
        if value is str and (native_str is not str) and (
            native_str not in self
        ):
            super().append(native_str)

    def __delitem__(self, index):
        # type: (int) -> None
        value = self[index]
        super().__delitem__(index)
        if (value is str) and (native_str in self):
            self.remove(native_str)

    def pop(self, index=-1):
        # type: (int) -> Union[type, Property]
        value = super().pop(index)
        if (value is str) and (native_str in self):
            self.remove(native_str)
        return value

    def __copy__(self):
        # type: () -> Types
        return self.__class__(self)

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Types
        return self.__class__(
            tuple(
                deepcopy(v, memo=memo)
                for v in self
            )
        )

    def __repr__(self):

        representation = [
            qualified_name(type(self)) + '('
        ]

        if self:

            representation[0] += '['

            for value in self:
                value_representation = (
                    qualified_name(value) if isinstance(value, type) else
                    repr(value)
                )
                lines = value_representation.split('\n')
                if len(lines) > 1:
                    indented_lines = [lines[0]]
                    for indented_line in lines[1:]:
                        indented_lines.append('    ' + indented_line)
                    value_representation = '\n'.join(indented_lines)
                representation.append(
                    '    %s,' % value_representation
                )

            representation[-1] = representation[-1].rstrip(',')
            representation.append(
                ']'
            )

        representation[-1] += ')'

        return '\n'.join(representation) if len(representation) > 2 else ''.join(representation)


abc.properties.Types.register(Types)