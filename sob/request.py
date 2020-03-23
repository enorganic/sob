"""
This module extends the functionality of `urllib.request.Request` to support
multipart requests, to support passing instances of sob models to the `data`
parameter/property for `urllib.request.Request`, and to support casting
requests as `str` or `bytes` (typically for debugging purposes and/or to aid in
producing non-language-specific API documentation).
"""
import collections.abc
import random
import re
import string
import urllib.request
from typing import Dict, Iterable, Optional, Sequence, Set, Tuple, Union

from .model import Dictionary, Model, serialize


class Headers:
    """
    A dictionary of headers for a `Request`, `Part`, or `MultipartRequest`
    instance.
    """

    def __init__(
        self,
        items: Dict[str, str],
        request: 'Data'
    ) -> None:
        assert isinstance(request, Data)
        self._dict = {}
        self.request: Data = request
        self.update(items)

    def pop(self, key: str, default: Optional[str] = None) -> str:
        key = key.capitalize()
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.pop(key, default=default)

    def popitem(self) -> Tuple[str, str]:
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.popitem()

    def setdefault(self, key: str, default: Optional[str] = None) -> str:
        key = key.capitalize()
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.setdefault(key, default=default)

    def update(
        self,
        _iterable: Union[Dict[str, str], Sequence[Tuple[str, str]]] = None,
        **kwargs: Dict[str, str]
    ) -> None:
        cd = {}
        if _iterable is None:
            d = kwargs
        else:
            d = dict(_iterable, **kwargs)
        for k, v in d.items():
            cd[k.capitalize()] = v
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        return self._dict.update(cd)

    def __delitem__(self, key: str) -> None:
        key = key.capitalize()
        if hasattr(self.request, '_boundary'):
            self.request._boundary = None
        if hasattr(self.request, '_bytes'):
            self.request._bytes = None
        del self._dict[key]

    def __setitem__(self, key: str, value: str) -> None:
        key = key.capitalize()
        if key != 'Content-length':
            if hasattr(self.request, '_boundary'):
                self.request._boundary = None
            if hasattr(self.request, '_bytes'):
                self.request._bytes = None
            return self._dict.__setitem__(key, value)

    def _get_content_length(self) -> int:
        data = self.request.data
        if data is None:
            content_length = 0
        else:
            content_length = len(data)
        return content_length

    def _get_boundary(self) -> str:
        boundary: str = ''
        try:
            boundary = str(
                getattr(self.request, 'boundary'),
                encoding='utf-8'
            )
        except AttributeError:
            pass
        return boundary

    def _get_content_type(self) -> Optional[str]:
        content_type: Optional[str] = None
        try:
            content_type = self._dict.__getitem__('Content-type')
        except KeyError:
            # Check to see if we can *infer* the content type
            try:
                if getattr(self.request, 'parts'):
                    content_type = 'multipart/form-data'
            except AttributeError:
                pass
        if (
            (content_type is not None) and
            content_type.strip().lower().startswith('multipart')
        ):
            boundary: str = self._get_boundary()
            if boundary:
                content_type += f'; boundary={boundary}'
        return content_type

    def __getitem__(self, key: str) -> None:
        key = key.capitalize()
        value: Optional[str]
        if key == 'Content-length':
            value = str(self._get_content_length())
        elif key == 'Content-type':
            value = self._get_content_type()
        else:
            value = self._dict.__getitem__(key)
        return value

    def keys(self) -> Iterable[str]:
        return (k for k in self)

    def values(self):
        return (self[k] for k in self)

    def __len__(self):
        return len(tuple(self))

    def __iter__(self) -> Iterable[str]:
        keys: Set[str] = set()
        key: str
        for key in self._dict.keys():
            keys.add(key)
            yield key
        if type(self.request) is not Part:
            # *Always* include "Content-length"
            if 'Content-length' not in keys:
                yield 'Content-length'
        # Always include "Content-type" for multi-part requests
        try:
            parts: Parts = getattr(self.request, 'parts')
            if parts and ('Content-type' not in keys):
                yield 'Content-type'
        except AttributeError:
            pass

    def __contains__(self, key: str) -> bool:
        return True if key in self.keys() else False

    def items(self) -> Iterable[Tuple[str, str]]:
        key: str
        for key in self:
            yield key, self[key]

    def copy(self) -> 'Headers':
        return self.__class__(
            self._dict,
            request=self.request
        )

    def __copy__(self) -> 'Headers':
        return self.copy()


class Data:
    """
    One of a multipart request's parts.
    """

    def __init__(
        self,
        data: Optional[Union[bytes, str, Sequence, Set, dict, Model]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Parameters:

            - data (
                  bytes|str|collections.Sequence|collections.Set|dict|
                  sob.abc.Model
              ): The payload.
            - headers ({str: str}): A dictionary of headers (for this part of
              the request body, not the main request). This should (almost)
              always include values for "Content-Disposition" and
              "Content-Type".
        """
        self._bytes: Optional[bytes] = None
        self._headers = None
        self._data = None
        self.headers: Dict[str, str] = headers
        self.data: Optional[bytes] = data

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._bytes = None
        if headers is None:
            headers = Headers({}, self)
        elif isinstance(headers, Headers):
            headers.request = self
        else:
            headers = Headers(headers, self)
        self._headers = headers

    @property
    def data(self):
        return self._data

    @data.setter
    def data(
        self,
        data: Optional[
            Union[
                bytes, str,
                Sequence, Set, dict,
                Model
            ]
        ]
    ) -> None:
        self._bytes = None
        if data is not None:
            serialize_type = None
            if 'Content-type' in self.headers:
                ct = self.headers['Content-type']
                if re.search(r'/json\b', ct) is not None:
                    serialize_type = 'json'
                if re.search(r'/yaml\b', ct) is not None:
                    serialize_type = 'yaml'
            if isinstance(data, (Model, dict)) or (
                isinstance(
                    data,
                    (
                        collections.abc.Sequence,
                        collections.abc.Set
                    )
                ) and not isinstance(
                    data,
                    (str, bytes)
                )
            ):
                data = serialize(
                    data,
                    serialize_type or 'json'
                )
            elif isinstance(data, dict):
                data = serialize(
                    Dictionary(data),
                    serialize_type or 'json'
                )
            if isinstance(data, str):
                data = bytes(data, encoding='utf-8')
        self._data = data

    def __bytes__(self):
        if self._bytes is None:
            lines = []
            for k, v in self.headers.items():
                lines.append(bytes(
                    '%s: %s' % (k, v),
                    encoding='utf-8'
                ))
            lines.append(b'')
            data = self.data
            if data:
                lines.append(self.data)
            self._bytes = b'\r\n'.join(lines) + b'\r\n'
        return self._bytes

    def __str__(self):
        b = self.__bytes__()
        if not isinstance(b, str):
            b = repr(b)[2:-1].replace('\\r\\n', '\r\n').replace('\\n', '\n')
        return b


class Part(Data):

    def __init__(
        self,
        data: Optional[Union[bytes, str, Sequence, Set, dict, Model]] = None,
        headers: Optional[Dict[str, str]] = None,
        parts: Optional[Sequence['Part']] = None
    ):
        """
        Parameters:

        - data (
              bytes|str|collections.Sequence|collections.Set|dict|
              sob.abc.Model
          ): The payload.
        - headers ({str: str}): A dictionary of headers (for this part of
          the request body, not the main request). This should (almost)
          always include values for "Content-Disposition" and
          "Content-Type".
        """
        self._boundary: Optional[bytes] = None
        self._parts: Optional[Parts] = None
        self.parts = parts
        Data.__init__(self, data=data, headers=headers)

    @property
    def boundary(self):
        """
        Calculates a boundary which is not contained in any of the request
        parts.
        """
        if self._boundary is None:
            data = b'\r\n'.join(
                [self._data or b''] +
                [bytes(p) for p in self.parts]
            )
            boundary = b''.join(
                bytes(
                    random.choice(string.digits + string.ascii_letters),
                    encoding='utf-8'
                )
                for _index in range(16)
            )
            while boundary in data:
                boundary += bytes(
                    random.choice(string.digits + string.ascii_letters),
                    encoding='utf-8'
                )
            self._boundary = boundary
        return self._boundary

    @property
    def data(self) -> None:
        if self.parts:
            data = (b'\r\n--' + self.boundary + b'\r\n').join(
                [self._data or b''] +
                [bytes(p).rstrip() for p in self.parts]
            ) + (b'\r\n--' + self.boundary + b'--')
        else:
            data = self._data
        return data

    @data.setter
    def data(self, data):
        Data.data.__set__(self, data)

    @property
    def parts(self) -> 'Parts':
        return self._parts

    @parts.setter
    def parts(self, parts: Optional[Sequence['Part']]) -> None:
        if parts is None:
            parts = Parts([], request=self)
        elif isinstance(parts, Parts):
            parts.request = self
        else:
            parts = Parts(parts, request=self)
        self._boundary = None
        self._parts = parts


class Parts(list):

    def __init__(
        self,
        items: Sequence[Part],
        request: 'Part'
    ) -> None:
        self.request = request
        super().__init__(items)

    def append(self, item: Part) -> None:
        self.request._boundary = None
        self.request._bytes = None
        super().append(item)

    def clear(self) -> None:
        self.request._boundary = None
        self.request._bytes = None
        super().clear()

    def extend(self, items: Iterable[Part]) -> None:
        self.request._boundary = None
        self.request._bytes = None
        super().extend(items)

    def reverse(self) -> None:
        self.request._boundary = None
        self.request._bytes = None
        super().reverse()

    def __delitem__(self, key: int) -> None:
        self.request._boundary = None
        self.request._bytes = None
        super().__delitem__(key)

    def __setitem__(self, key: int, value: Part) -> None:
        self.request._boundary = None
        self.request._bytes = None
        super().__setitem__(key, value)


class Request(Data, urllib.request.Request):
    """
    A sub-class of `urllib.request.Request` which accommodates additional data
    types, and serializes `data` in accordance with what is indicated by the
    request's "Content-Type" header.
    """

    def __init__(
        self,
        url,
        data: Optional[Union[bytes, str, Sequence, Set, dict, Model]] = None,
        headers: Optional[Dict[str, str]] = None,
        origin_req_host: Optional[str] = None,
        unverifiable: bool = False,
        method: Optional[str] = None
    ) -> None:
        self._bytes: Optional[bytes] = None
        self._headers = None
        self._data = None
        self.headers = headers
        urllib.request.Request.__init__(
            self,
            url,
            data=data,
            headers=headers,
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method
        )


class MultipartRequest(Part, Request):
    """
    A sub-class of `Request` which adds a property (and initialization
    parameter) to hold the `parts` of a multipart request.

    https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
    """

    def __init__(
        self,
        url,
        data: Optional[Union[bytes, str, Sequence, Set, dict, Model]] = None,
        headers: Optional[Dict[str, str]] = None,
        origin_req_host: Optional[str] = None,
        unverifiable: bool = False,
        method: Optional[str] = None,
        parts: Optional[Sequence[Part]] = None
    ) -> None:
        Part.__init__(
            self,
            data=data,
            headers=headers,
            parts=parts
        )
        Request.__init__(
            self,
            url,
            data=data,
            headers=headers,
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method
        )
