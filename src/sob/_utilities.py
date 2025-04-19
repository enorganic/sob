from __future__ import annotations

import functools

# from copy import copy
from typing import Any, Callable
from warnings import warn


def deprecated(
    message: str,
    category: type[Warning] = DeprecationWarning,
    stacklevel: int = 2,
) -> Callable[..., Callable[..., Any]]:
    """
    This decorator marks a function as deprecated, and issues a
    deprecation warning when the function is called.
    """

    def decorating_function(
        function_or_class: type | Callable[..., Any],
    ) -> Callable[..., Any]:
        @functools.wraps(function_or_class)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn(
                message,
                category,
                stacklevel=stacklevel,
            )
            return function_or_class(*args, **kwargs)

        return wrapper

    return decorating_function
