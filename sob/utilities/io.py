from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
import os  # noqa
from io import UnsupportedOperation
from . import compatibility

compatibility.backport()

urljoin = compatibility.urljoin

IO = compatibility.typing.IO
Any = compatibility.typing.Any
Optional = compatibility.typing.Optional
Union = compatibility.typing.Union


def read(data):
    # type: (Union[str, IO]) -> Any
    if (
        (hasattr(data, 'readall') and callable(data.readall)) or
        (hasattr(data, 'read') and callable(data.read))
    ):
        if hasattr(data, 'seek') and callable(data.seek):
            try:
                data.seek(0)
            except UnsupportedOperation:
                pass
        if hasattr(data, 'readall') and callable(data.readall):
            try:
                data = data.readall()
            except UnsupportedOperation:
                data = data.read()
        else:
            data = data.read()
        return data
    else:
        raise TypeError(
            '%s is not a file-like object' % repr(data)
        )


def get_url(file_like_object):
    # type: (IO) -> Optional[str]
    """
    Get the URL from which an input-output (file-like) object was sourced
    """
    url = None
    if hasattr(file_like_object, 'url'):
        url = file_like_object.url
    elif hasattr(file_like_object, 'name'):
        url = urljoin('file:', os.path.abspath(file_like_object.name))
    return url


# For backwards compatibility...
get_io_url = get_url
