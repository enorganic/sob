import os
from io import UnsupportedOperation
from typing import Callable, Optional, Union
from urllib.parse import urljoin

from .inspect import get_method
from ..abc import Readable


def read(file: Readable) -> Union[str, bytes]:
    """
    Read a file-like object and return the text or binary data it contains.

    Parameters:

    - file (abc.io.Readable): A readable, file-like object.

    This function returns an instance of `str` or `bytes`.
    """
    read_method_name: str
    seek_method: Optional[Callable] = get_method(file, "seek", None)
    if seek_method:
        try:
            seek_method(0)
        except UnsupportedOperation:
            pass
    for read_method_name in ("readall", "read"):
        read_method: Optional[Callable] = get_method(
            file, read_method_name, None
        )
        if read_method:
            try:
                return read_method()
            except UnsupportedOperation:
                pass
    raise TypeError(f"{repr(file)} is not a file-like object")


def get_url(file: Readable) -> Optional[str]:
    """
    Get the URL from which an input-output (file-like) object was sourced.

    Parameters:

    - file (abc.io.Readable)

    This function returns an instance of `str` if the originating URL or
    file-path can be inferred, otherwise it returns `None`.
    """
    url: Optional[str] = getattr(file, "url", None)
    if url is None:
        url = getattr(file, "name", None)
        if url is not None:
            url = urljoin("file:", os.path.abspath(url))
    return url
