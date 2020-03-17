from abc import ABCMeta, abstractmethod, ABC
from typing import Iterable, Any, List

__any__: List[str] = [
    'Model',
    'Dictionary',
    'Array'
]


class Model(ABC):

    __metaclass__ = ABCMeta


class Object(Model):

    pass


class Dictionary(Model):

    @abstractmethod
    def keys(self) -> Iterable[str]:
        pass

    @abstractmethod
    def values(self) -> Iterable[Any]:
        pass


class Array(Model):

    @abstractmethod
    def append(self, value):
        # type: (Any) -> None
        pass

    def __iter__(self) -> Iterable[Any]:
        pass


