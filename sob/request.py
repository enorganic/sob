"""
This module extends the functionality of `urllib.request.Request` to support
multipart requests, to support passing instances of sob models to the `data`
parameter/property for `urllib.request.Request`, and to support casting
requests as `str` or `bytes` (typically for debugging purposes and/or to aid in
producing non-language-specific API documentation).
"""
import collections
import collections.abc
import random
import re
import string
from typing import (
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)
from urllib.request import Request as _Request  # type: ignore

from . import abc
from .model import Dictionary, serialize


class Headers(collections.OrderedDict):
    """
    A dictionary of headers for a `Request`, `Part`, or `MultipartRequest`
    instance.
    """

    def __init__(
        self,
        items: Union[Dict[str, str], Iterable[Tuple[str, str]]],
        request: "Data",
    ) -> None:
        assert isinstance(request, Data)
        self.request: Data = request
        super().__init__(items)

    def _reset_part(self) -> None:
        if isinstance(self.request, Part):
            del self.request.boundary
            self.request.clear_bytes()

    def pop(  # type: ignore
        self, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        key = key.capitalize()
        self._reset_part()
        return super().pop(key, default)

    def popitem(self, last: bool = True) -> Tuple[str, str]:
        self._reset_part()
        return super().popitem(last=last)

    def setdefault(self, key: str, default: Optional[str] = None) -> str:
        key = key.capitalize()
        self._reset_part()
        return super().setdefault(key, default)

    def update(  # type: ignore
        self,
        *args: Union[
            Mapping[str, str], abc.Dictionary, Iterable[Tuple[str, str]]
        ],
        **kwargs: str,
    ) -> None:
        capitalized_dict: "abc.OrderedDict[str, str]" = (
            collections.OrderedDict()
        )
        key: str
        value: str
        for key, value in collections.OrderedDict(*args, **kwargs).items():
            capitalized_dict[key.capitalize()] = value
        self._reset_part()
        super().update(capitalized_dict)

    def __getitem__(self, key: str) -> str:
        key = key.capitalize()
        value: Optional[str]
        if key == "Content-length":
            value = str(self._get_content_length())
        elif key == "Content-type":
            value = self._get_content_type()
        else:
            value = super().__getitem__(key)
        assert isinstance(value, str)
        return value

    def __delitem__(self, key: str) -> None:
        self._reset_part()
        super().__delitem__(key.capitalize())

    def __setitem__(self, key: str, value: str) -> None:
        key = key.capitalize()
        if key != "Content-length":
            self._reset_part()
            super().__setitem__(key, value)

    def _get_content_length(self) -> int:
        return len(self.request.data or b"")

    def _get_boundary(self) -> str:
        boundary: str = ""
        if isinstance(self.request, Part):
            boundary = str(self.request.boundary, encoding="utf-8")
        return boundary

    def _get_content_type(self) -> str:
        if isinstance(self.request, Part) and self.request.parts:
            return f"multipart/form-data; boundary={self._get_boundary()}"
        else:
            return super().__getitem__("Content-type")

    def __len__(self) -> int:
        return super().__len__()

    def __iter__(self) -> Iterator[str]:
        keys: Set[str] = set()
        key: str
        for key in super().__iter__():
            keys.add(key)
            yield key
        if type(self.request) is not Part:
            # *Always* include "Content-length"
            if "Content-length" not in keys:
                yield "Content-length"
        if isinstance(self.request, Part) and self.request.parts:
            # Always include "Content-type" for multi-part requests
            if "Content-type" not in keys:
                yield "Content-type"

    def __contains__(self, key: str) -> bool:  # type: ignore
        return super().__contains__(key.capitalize())

    def items(self) -> ItemsView[str, str]:  # type: ignore
        for key in self.__iter__():
            yield key, self[key]

    def keys(self) -> Iterator[str]:  # type: ignore
        key: str
        for key in self.__iter__():
            yield key

    def values(self) -> Iterator[str]:  # type: ignore
        key: str
        for key in self.__iter__():
            yield self[key]

    def copy(self) -> "Headers":
        return self.__class__(super().items(), request=self.request)

    def __copy__(self) -> "Headers":
        return self.copy()


class Data:
    """
    One of a multipart request's parts.
    """

    def __init__(
        self,
        data: Optional[
            Union[bytes, str, Sequence, Set, dict, abc.Model]
        ] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Parameters:

            - data (
                  bytes|str|collections.Sequence|collections.Set|dict|
                  abc.model.Model
              ): The payload.
            - headers ({str: str}): A dictionary of headers (for this part of
              the request body, not the main request). This should (almost)
              always include values for "Content-Disposition" and
              "Content-Type".
        """
        self._bytes: Optional[bytes] = None
        self._headers: Optional[Headers] = None
        self._data: Optional[bytes] = None
        setattr(self, "headers", headers)
        setattr(self, "data", data)

    @property  # type: ignore
    def headers(self) -> Optional[Headers]:
        return self._headers

    @headers.setter
    def headers(self, headers: Union[Dict[str, str], Headers, None]) -> None:
        self._bytes = None
        if headers is None:
            headers = Headers({}, self)
        elif isinstance(headers, Headers):
            headers.request = self
        else:
            headers = Headers(headers, self)
        self._headers = headers

    @property  # type: ignore
    def data(self) -> Optional[bytes]:  # type: ignore
        return self._data

    @data.setter
    def data(
        self,
        data: Optional[Union[bytes, str, Sequence, Set, dict, abc.Model]],
    ) -> None:
        self._bytes = None
        if data is not None:
            serialize_type = None
            if (self.headers is not None) and ("Content-type" in self.headers):
                content_type: str = self.headers["Content-type"]
                if re.search(r"/json\b", content_type) is not None:
                    serialize_type = "json"
                if re.search(r"/yaml\b", content_type) is not None:
                    serialize_type = "yaml"
            if isinstance(data, (abc.Model, dict)) or (
                isinstance(
                    data, (collections.abc.Sequence, collections.abc.Set)
                )
                and not isinstance(data, (str, bytes))
            ):
                data = serialize(data, serialize_type or "json")
            elif isinstance(data, dict):
                data = serialize(Dictionary(data), serialize_type or "json")
            if isinstance(data, str):
                data = bytes(data, encoding="utf-8")
        self._data = data

    @data.deleter
    def data(self) -> None:  # type: ignore
        self.data = None

    def clear_bytes(self) -> None:
        self._bytes = None

    def __bytes__(self) -> bytes:
        if self._bytes is None:
            lines: List[bytes] = []
            if self.headers is not None:
                key: str
                value: str
                for key, value in self.headers.items():
                    lines.append(
                        bytes("%s: %s" % (key, value), encoding="utf-8")
                    )
            lines.append(b"")
            if self.data is not None:
                lines.append(self.data)
            self._bytes = b"\r\n".join(lines) + b"\r\n"
        return self._bytes

    def __str__(self) -> str:
        return (
            repr(bytes(self))[2:-1]
            .replace("\\r\\n", "\r\n")
            .replace("\\n", "\n")
        )


class Part(Data):
    """
    TODO
    """

    def __init__(
        self,
        data: Optional[
            Union[bytes, str, Sequence, Set, dict, abc.Model]
        ] = None,
        headers: Optional[Dict[str, str]] = None,
        parts: Optional[Sequence["Part"]] = None,
    ):
        """
        Parameters:

        - data (
              bytes|str|collections.Sequence|collections.Set|dict|
              abc.model.Model
          ): The payload.
        - headers ({str: str}): A dictionary of headers (for this part of
          the request body, not the main request). This should (almost)
          always include values for "Content-Disposition" and
          "Content-Type".
        """
        self._boundary: Optional[bytes] = None
        self._parts: Optional[Parts] = None
        self.parts = parts  # type: ignore
        Data.__init__(self, data=data, headers=headers)

    @property  # type: ignore
    def boundary(self) -> bytes:
        """
        Calculates a boundary which is not contained in any of the request
        parts.
        """
        if self._boundary is None:
            part: Part
            data: bytes = b"\r\n".join(
                [self._data or b""]
                + [bytes(part) for part in (self.parts or ())]
            )
            boundary: bytes = b"".join(
                bytes(
                    random.choice(string.digits + string.ascii_letters),
                    encoding="utf-8",
                )
                for _index in range(16)
            )
            while boundary in data:
                boundary += bytes(
                    random.choice(string.digits + string.ascii_letters),
                    encoding="utf-8",
                )
            self._boundary = boundary
        return self._boundary

    @boundary.deleter
    def boundary(self) -> None:
        self._boundary = None

    @property  # type: ignore
    def data(self) -> Optional[bytes]:
        data: Optional[bytes]
        if self.parts:
            part: Part
            data = b"%s\r\n--%s--" % (
                (b"\r\n--%s\r\n" % self.boundary).join(
                    [self._data or b""]
                    + [bytes(part).rstrip() for part in self.parts]
                ),
                self.boundary,
            )
        else:
            data = self._data
        return data

    @data.setter
    def data(
        self,
        data: Optional[Union[bytes, str, Sequence, Set, dict, abc.Model]],
    ) -> None:
        getattr(Data.data, "__set__")(self, data)

    @property  # type: ignore
    def parts(self) -> Optional["Parts"]:
        return self._parts

    @parts.setter
    def parts(self, parts: Optional[Sequence["Part"]]) -> None:
        if parts is None:
            parts = Parts([], request=self)
        elif isinstance(parts, Parts):
            parts.request = self
        else:
            parts = Parts(parts, request=self)
        self._boundary = None
        self._parts = parts


class Parts(list):
    def __init__(self, items: Sequence[Part], request: "Part") -> None:
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

    def __delitem__(self, key: int) -> None:  # type: ignore
        self.request._boundary = None
        self.request._bytes = None
        super().__delitem__(key)

    def __setitem__(self, key: int, value: Part) -> None:  # type: ignore
        self.request._boundary = None
        self.request._bytes = None
        super().__setitem__(key, value)  # type: ignore


class Request(Data, _Request):  # type: ignore
    """
    A sub-class of `urllib.request.Request` which accommodates additional data
    types, and serializes `data` in accordance with what is indicated by the
    request's "Content-Type" header.
    """

    def __init__(
        self,
        url: str,
        data: Optional[
            Union[bytes, str, Sequence, Set, dict, abc.Model]
        ] = None,
        headers: Optional[Dict[str, str]] = None,
        origin_req_host: Optional[str] = None,
        unverifiable: bool = False,
        method: Optional[str] = None,
    ) -> None:
        self._bytes: Optional[bytes] = None
        self._headers = None
        self._data = None
        self.headers = headers  # type: ignore
        _Request.__init__(
            self,
            url,
            data=data,  # type: ignore
            headers=self.headers,  # type: ignore
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method,
        )


class MultipartRequest(Part, Request):  # type: ignore
    """
    A sub-class of `Request` which adds a property (and initialization
    parameter) to hold the `parts` of a multipart request.

    https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html
    """

    def __init__(
        self,
        url: str,
        data: Optional[
            Union[bytes, str, Sequence, Set, dict, abc.Model]
        ] = None,
        headers: Optional[Dict[str, str]] = None,
        origin_req_host: Optional[str] = None,
        unverifiable: bool = False,
        method: Optional[str] = None,
        parts: Optional[Sequence[Part]] = None,
    ) -> None:
        Part.__init__(self, data=data, headers=headers, parts=parts)
        Request.__init__(
            self,
            url,
            data=data,
            headers=headers,
            origin_req_host=origin_req_host,
            unverifiable=unverifiable,
            method=method,
        )
