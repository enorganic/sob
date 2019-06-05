from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from ..utilities.compatibility import backport

backport()

from abc import ABCMeta, abstractmethod  # noqa

# We need ABCs to inherit from `ABC` in python 3x, but in python 2x ABC is absent and we need classes to inherit from
# `object` in order to be new-style classes
try:
    from abc import ABC
except ImportError:
    ABC = object


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


