from collections import OrderedDict
from inspect import Parameter, signature
from typing import Any, Callable

from sob._types import UNDEFINED


def get_parameters_defaults(function: Callable[..., Any]) -> dict[str, Any]:
    """
    Returns an ordered dictionary mapping a function's argument names to
    default values, or `UNDEFINED` in the case of
    positional arguments.

    >>> class X:
    ...     def __init__(self, a, b, c, d=1, e=2, f=3):
    ...         pass
    >>> for parameter_name, default in get_parameters_defaults(
    ...     X.__init__  # -
    ... ).items():
    ...     print((parameter_name, default))
    ('self', UNDEFINED)
    ('a', UNDEFINED)
    ('b', UNDEFINED)
    ('c', UNDEFINED)
    ('d', 1)
    ('e', 2)
    ('f', 3)
    """
    defaults: dict[str, Any] = OrderedDict()
    parameter_name: str
    parameter: Parameter
    for parameter_name, parameter in signature(function).parameters.items():
        if parameter.default is Parameter.empty:
            defaults[parameter_name] = UNDEFINED
        else:
            defaults[parameter_name] = parameter.default
    return defaults
