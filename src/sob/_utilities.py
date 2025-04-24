from __future__ import annotations

import functools

# from copy import copy
from typing import Any, Callable
from urllib.parse import urljoin
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


def get_readable_url(readable: Any) -> str | None:
    """
    Get the URL from an HTTP response or file-like object.
    """
    if hasattr(readable, "geturl") and callable(readable.geturl):
        return readable.geturl()
    if hasattr(readable, "url"):
        if isinstance(readable.url, str):
            return readable.url
        raise TypeError(readable.url)
    if hasattr(readable, "name"):
        if not isinstance(readable.name, str):
            raise TypeError(readable.name)
        name: str = readable.name
        if not name.startswith("/"):
            name = f"/{name}"
        return urljoin(
            "file:",
            name.replace("\\", "/"),
        )
    return None
