from enum import Enum
from typing import Any
from . import inspect

UNDEFINED = None


class Undefined:
    """
    This class is intended to indicate that a parameter has not been passed
    to a keyword argument in situations where `None` is to be used as a
    meaningful value
    """

    def __init__(self) -> None:
        """
        Only one instance of `Undefined` is permitted, so initialization
        checks to make sure this is the first use
        """
        if UNDEFINED is not None:
            raise RuntimeError(
                '%s may only be instantiated once.' % repr(self)
            )

    def __repr__(self) -> str:
        """
        Represent instances of this class using the qualified name for the
        constant `UNDEFINED`
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

Module: type = type(inspect)


