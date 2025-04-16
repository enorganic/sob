from __future__ import annotations

import functools
from copy import copy
from typing import Any, Callable
from warnings import warn

__all__: tuple[str, ...] = ("deprecated",)

try:
    from warnings import deprecated  # type: ignore
except ImportError:
    # For versions of Python < 3.13, define a custom deprecated decorator
    def deprecated(
        message: str,
        category: type[Warning] = DeprecationWarning,
        stacklevel: int = 1,
    ) -> Callable[..., Callable[..., Any]]:
        """
        This decorator marks a function as deprecated, and issues a
        deprecation warning when the function is called.
        """

        def decorating_function(
            function_or_class: type | Callable[..., Any],
        ) -> Callable[..., Any]:
            if isinstance(function_or_class, type):
                # If `function_or_class` is a class, we need to wrap its
                # `__init__` method
                original_init: Callable[
                    ..., None  # -
                ] = function_or_class.__init__  # type: ignore

                @functools.wraps(original_init)
                def init_wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
                    warn(
                        message,
                        category,
                        stacklevel=stacklevel,
                    )
                    original_init(self, *args, **kwargs)

                new_class: type = copy(function_or_class)
                new_class.__init__ = init_wrapper  # type: ignore
                return new_class

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
