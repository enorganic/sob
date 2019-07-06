from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from ..utilities import compatibility
from abc import ABCMeta, abstractmethod

compatibility.backport()

ABC = compatibility.ABC
Iterable = compatibility.typing.Iterable
Any = compatibility.typing.Any


class Model(ABC):

    __metaclass__ = ABCMeta


class Object(Model):

    pass


class Dictionary(Model):

    @abstractmethod
    def keys(self):
        # type: (...) -> Iterable[str]
        pass

    @abstractmethod
    def values(self):
        # type: (...) -> Iterable[Any]
        pass


class Array(Model):

    @abstractmethod
    def append(self, value):
        # type: (Any) -> None
        pass

    def __iter__(self):
        # type: (...) -> Iterable[Any]
        pass


