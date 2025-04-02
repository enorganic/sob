from __future__ import annotations

import functools
from typing import Any, Callable
from warnings import warn

from sob.utilities import get_qualified_name


def deprecated(message: str = "") -> Callable[..., Callable[..., Any]]:
    """
    This decorator marks a function as deprecated, and issues a
    deprecation warning when the function is called.
    """

    def decorating_function(
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            name: str = get_qualified_name(function)
            warn(
                (
                    (
                        f"{name} is deprecated: {message}"
                        if message
                        else f"{name} is deprecated"
                    )
                    if name
                    else message
                ),
                DeprecationWarning,
                stacklevel=2,
            )
            return function(*args, **kwargs)

        return wrapper

    return decorating_function
