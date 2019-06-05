# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from sob.utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

import numbers  # noqa
import decimal  # noqa

from copy import deepcopy  # noqa
from datetime import date, datetime  # noqa

try:
    from typing import Union, Optional, Sequence, Mapping, Set, Sequence, Callable, Dict, Any, Hashable, Collection,\
        Tuple
except ImportError:
    Union = Optional = Sequence = Mapping = Set = Sequence = Callable = Dict = Any = Hashable = Collection = Tuple =\
        Iterable = None

from sob.utilities import collections, collections_abc, qualified_name, Generator

from .. import abc
from ..abc.properties import Property


NoneType = type(None)


NULL = None


class DefinitionExistsError(Exception):

    pass


class Null(object):  # noqa - inheriting from object is intentional, as this is needed for python 2x compatibility
    """
    Instances of this class represent an *explicit* null value, rather than the absence of a
    property/attribute/element, as would be inferred from a value of `None`.
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


NULL = Null()


TYPES = tuple(
    # We first put all the types in a `set` so that when `native_str` and `str` are the same--they are
    # not duplicated
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
    # type: (Union[type, Property]) -> (Union[type, Property])

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
    Instances of this class are lists which will only take values which are valid types for describing a property
    definition.
    """

    def __init__(
        self,
        items=None  # type: Optional[Union[Sequence[Union[type, Property], Types], type, Property]]
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
        if value is str and (native_str is not str) and (native_str not in self):
            super().append(native_str)

    def append(self, value):
        # type: (Union[type, Property]) -> None
        super().append(_validate_type_or_property(value))
        if value is str and (native_str is not str) and (native_str not in self):
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