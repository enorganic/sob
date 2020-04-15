import decimal
import numbers
from abc import ABCMeta
from collections import abc, OrderedDict
from datetime import date, datetime
from types import GeneratorType
from typing import Any, Optional, Dict, Hashable, Tuple, List, TypeVar

__all__: List[str] = [
    'UNDEFINED',
    'Undefined',
    'NoneType',
    'NULL',
    'DefinitionExistsError',
    'Null',
    'TYPES',
    'JSON_TYPES'
]

UNDEFINED: Optional['Undefined'] = None


class Undefined:
    """
    This class is intended to indicate that a parameter has not been passed
    to a keyword argument in situations where `None` is to be used as a
    meaningful value.
    """

    def __init__(self) -> None:
        """
        Only one instance of `Undefined` is permitted, so initialization
        checks to make sure this is the first use.
        """
        if UNDEFINED is not None:
            raise RuntimeError(
                '%s may only be instantiated once.' % repr(self)
            )

    def __repr__(self) -> str:
        """
        Represent instances of this class using the qualified name for the
        constant `UNDEFINED`.
        """
        representation = 'UNDEFINED'
        if self.__module__ not in (
            '__main__', 'builtins', '__builtin__', __name__
        ):
            representation = ''.join([
                type(self).__module__,
                '.',
                representation
            ])
        return representation

    def __bool__(self) -> bool:
        """
        `UNDEFINED` cast as a boolean is `False` (as with `None`)
        """
        return False

    def __hash__(self) -> int:
        return 0

    def __eq__(self, other: Any) -> bool:
        """
        Another object is only equal to this if it shares the same id, since
        there should only be one instance of this class defined
        """
        return other is self


locals()['UNDEFINED'] = Undefined()


class NoneType(metaclass=ABCMeta):

    pass


# noinspection PyUnresolvedReferences
NoneType.register(type(None))
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


TYPES: Tuple[type, ...] = (
    str, bytes, bool,
    dict,
    abc.Set, abc.Sequence, GeneratorType,
    numbers.Number, decimal.Decimal,
    date, datetime,
    Null
)
JSON_TYPES: Tuple[type, ...] = (
    str, dict, list, int, float, bool, NoneType
)
