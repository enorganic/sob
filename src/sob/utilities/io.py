from __future__ import annotations

import os
from io import UnsupportedOperation
from typing import TYPE_CHECKING, Callable
from urllib.parse import urljoin

# isort: off
from sob.utilities.inspect import get_method
import contextlib

if TYPE_CHECKING:
    from sob.abc import Readable

# isort: on


def read(file: Readable) -> str | bytes:
    """
    Read a file-like object and return the text or binary data it contains.

    Parameters:

    - file (abc.io.Readable): A readable, file-like object.

    This function returns an instance of `str` or `bytes`.
    """
    read_method_name: str
    seek_method: Callable | None = get_method(file, "seek", None)
    if seek_method:
        with contextlib.suppress(UnsupportedOperation):
            seek_method(0)
    for read_method_name in ("readall", "read"):
        read_method: Callable | None = get_method(file, read_method_name, None)
        if read_method:
            try:
                return read_method()
            except UnsupportedOperation:
                pass
    message: str = f"{file!r} is not a file-like object"
    raise TypeError(message)


def get_url(file: Readable) -> str | None:
    """
    Get the URL from which an input-output (file-like) object was sourced.

    Parameters:

    - file (abc.io.Readable)

    This function returns an instance of `str` if the originating URL or
    file-path can be inferred, otherwise it returns `None`.
    """
    url: str | None = getattr(file, "url", None)
    if url is None:
        url = getattr(file, "name", None)
        if url is not None:
            url = urljoin("file:", os.path.abspath(url))
    return url
