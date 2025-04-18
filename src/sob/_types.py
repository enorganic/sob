from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from collections.abc import Hashable

_module_locals: dict[str, Any] = locals()


class Undefined:
    """
    This class is intended to indicate that a parameter has not been passed
    to a keyword argument in situations where `None` is to be used as a
    meaningful value.

    The `Undefined` class is a singleton, so only one instance of this class
    is permitted: `sob.UNDEFINED`.
    """

    __module__ = "sob"

    def __init__(self) -> None:
        # Only one instance of `Undefined` is permitted, so initialization
        # checks to make sure this is the first use.
        if "UNDEFINED" in _module_locals:
            message: str = f"{self!r} may only be instantiated once."
            raise DefinitionExistsError(message)

    def __repr__(self) -> str:
        # Represent instances of this class using the qualified name for the
        # constant `UNDEFINED`.
        return "sob.UNDEFINED"

    def __bool__(self) -> bool:
        # `UNDEFINED` cast as a boolean is `False` (as with `None`)
        return False

    def __hash__(self) -> int:
        return 0

    def __eq__(self, other: object) -> bool:
        # Another object is only equal to this if it shares the same id, since
        # there should only be one instance of this class defined
        return other is self

    def __reduce__(self) -> tuple[Callable[[], Undefined], tuple]:
        return _undefined, ()


UNDEFINED: Undefined = Undefined()
"""
`sob.UNDEFINED` is the singleton instance of `sob.Undefined`, and is used to
indicate that a parameter has not been passed to a function or method keyword.
"""


def _undefined() -> Undefined:
    return UNDEFINED


class NoneType(metaclass=ABCMeta):  # noqa: B024
    pass


NoneType.register(type(None))


class DefinitionExistsError(Exception):
    """
    This error is raised when an attempt is made to redefine
    a singleton class instance.
    """


class Null:
    """
    Instances of this class represent an *explicit* null value, rather than the
    absence of a property/attribute/element, as would be inferred from a value
    of `None`.

    Note: Like the built-in value `None`, only one instance of this class is
    permitted (it's a singleton), so this class should never be instantiated,
    it should always be referenced through the constant `sob.NULL`.
    """

    __module__ = "sob"

    def __init__(self) -> None:
        if "NULL" in _module_locals:
            message: str = f"{self!r} may only be defined once."
            raise DefinitionExistsError(message)

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return id(other) == id(self)

    def __hash__(self) -> int:
        return 0

    def __str__(self) -> str:
        return "null"

    @staticmethod
    def _marshal() -> None:
        return None

    def __repr__(self) -> str:
        return "sob.NULL"

    def __copy__(self) -> Null:
        return self

    def __deepcopy__(self, memo: dict[Hashable, Any]) -> Null:
        return self

    def __reduce__(self) -> tuple[Callable[[], Null], tuple]:
        return _null, ()


NULL: Null = Null()
"""
`sob.NULL` is the singleton instance of `sob.Null`, and is used to represent
an explicit `null` value in JSON, whereas in the context of an instance
of a sub-class of `sob.Object`—`None` indicates the *absence* of a property
value.
"""


def _null() -> Null:
    return NULL
