# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals
from ..utilities.compatibility import backport

backport()

from future.utils import native_str  # noqa

from abc import ABCMeta, abstractmethod

# We need to inherit from `ABC` in python 3x, but in python 2x ABC is absent
try:
    from abc import ABC
except ImportError:
    ABC = object


class Types(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        items=None  # type: Optional[Union[Sequence[Union[type, Property], Types], type, Property]]
    ):
        pass


class Property(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        types=None,  # type: Sequence[Union[type, Property]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Sequence[Union[str, sob.meta.Version]]]
    ):
        self.types = types
        self.name = name
        self.required = required
        self.versions = versions  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]

    @property
    @abstractmethod
    def types(self):
        # type: (...) -> Optional[Sequence[Union[type, Property, Model]]]
        pass

    @types.setter
    @abstractmethod
    def types(self, types_or_properties):
        # type: (Optional[Sequence[Union[type, Property, Model]]]) -> None
        pass

    @property
    @abstractmethod
    def versions(self):
        # type: () -> Optional[Sequence[meta.Version]]
        pass

    @versions.setter
    @abstractmethod
    def versions(
        self,
        versions  # type: Optional[Sequence[Union[str, collections_abc.Iterable, meta.Version]]]
    ):
        # type: (...) -> Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        pass


class String(Property):

    pass


class Date(Property):

    pass


class DateTime(Property):

    pass


class Bytes(Property):

    pass


class Enumerated(Property):

    pass


class Number(Property):

    pass


class Integer(Property):

    pass


class Integer(Property):

    pass


class Boolean(Property):

    pass


class Array(Property):

    @property
    @abstractmethod
    def item_types(self):
        # type: (...) -> Types
        pass

    @item_types.setter
    @abstractmethod
    def item_types(self, item_types):
        # type: (Types) -> None
        pass


class Dictionary(Property):

    @property
    @abstractmethod
    def value_types(self):
        # type: (...) -> Types
        pass

    @value_types.setter
    @abstractmethod
    def value_types(self, value_types_):
        # type: (Types) -> None
        pass
