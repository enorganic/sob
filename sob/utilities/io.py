import os
from io import UnsupportedOperation, RawIOBase
from typing import IO, Any, Optional, Union
from urllib.parse import urljoin
from urllib.response import addinfourl


def _has_callable_attribute(
    object_instance: object,
    attribute_name: str
) -> bool:
    try:
        attribute_value: Any = getattr(object_instance, attribute_name)
    except AttributeError:
        return False
    return callable(attribute_value)


def read(data: Union[str, IO, RawIOBase]) -> Any:
    readall_is_callable: bool = _has_callable_attribute(data, 'readall')
    read_is_callable: bool = _has_callable_attribute(data, 'read')
    if (
        readall_is_callable or
        read_is_callable
    ):
        if _has_callable_attribute(data, 'seek'):
            try:
                data.seek(0)
            except UnsupportedOperation:
                pass
        if readall_is_callable:
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


def get_url(file_like_object: Union[IO, addinfourl]) -> Optional[str]:
    """
    Get the URL from which an input-output (file-like) object was sourced
    """
    url: Optional[str] = None
    if hasattr(file_like_object, 'url'):
        url = file_like_object.url
    elif hasattr(file_like_object, 'name'):
        url = urljoin('file:', os.path.abspath(file_like_object.name))
    return url
