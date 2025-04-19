from __future__ import annotations

from io import UnsupportedOperation
from typing import IO, TYPE_CHECKING, Callable

# isort: off
from sob.utilities import get_method
import contextlib

if TYPE_CHECKING:
    from sob.abc import Readable

# isort: on


def read(file: Readable | IO) -> str | bytes:
    """
    Read a file-like object and return the text or binary data it contains.

    Parameters:

        file: A readable, file-like object.

    This function returns an instance of `str` or `bytes`.
    """
    if TYPE_CHECKING:
        assert isinstance(file, Readable)
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
