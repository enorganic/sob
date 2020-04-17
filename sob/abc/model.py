import collections
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from io import IOBase
from typing import Any, Iterable, List, Dict, Optional, Union

from . import meta
from ..utilities.typing import JSONTypes

__all__: List[str] = [
    'Model',
    'Object',
    'Dictionary',
    'Array'
]


class Model(metaclass=ABCMeta):

    _meta: meta.Meta
    _pointer: Optional[str]
    _url: Optional[str]
    _format: Optional[str]

    @abstractmethod
    def _marshal(self) -> Union[
        Dict[str, JSONTypes],
        List[JSONTypes]
    ]:
        pass

    @abstractmethod
    def _validate(self, raise_errors: bool = True) -> None:
        pass


class Object(Model, collections.abc.MutableMapping, metaclass=ABCMeta):

    _meta: meta.Object

    @abstractmethod
    def _marshal(self) -> Dict[str, JSONTypes]:
        pass

    @abstractmethod
    def __copy__(self) -> 'Object':
        pass

    @abstractmethod
    def __deepcopy__(self, memo: Optional[dict]) -> 'Object':
        pass

    @abstractmethod
    def __delattr__(self, key: str) -> None:
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> None:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __init__(
        self,
        _data: Optional[Union[str, bytes, dict, IOBase]] = None
    ) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[str]:
        pass

    @abstractmethod
    def __ne__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __setattr__(self, property_name: str, value: Any) -> None:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class Dictionary(Model, collections.abc.MutableMapping, metaclass=ABCMeta):

    _meta: meta.Dictionary

    @abstractmethod
    def _marshal(self) -> Dict[str, JSONTypes]:
        pass


class Array(Model, collections.abc.MutableSequence, metaclass=ABCMeta):

    _meta: meta.Array

    @abstractmethod
    def _marshal(self) -> List[JSONTypes]:
        pass
