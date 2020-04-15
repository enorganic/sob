from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import List, Dict, Optional, Union

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


class Object(Model, OrderedDict, metaclass=ABCMeta):

    _meta: meta.Object

    @abstractmethod
    def _marshal(self) -> Dict[str, JSONTypes]:
        pass


class Dictionary(Model, OrderedDict, metaclass=ABCMeta):

    _meta: meta.Dictionary

    @abstractmethod
    def _marshal(self) -> Dict[str, JSONTypes]:
        pass


class Array(Model, list, metaclass=ABCMeta):

    _meta: meta.Array

    @abstractmethod
    def _marshal(self) -> List[JSONTypes]:
        pass
