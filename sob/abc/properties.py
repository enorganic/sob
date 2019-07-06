from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from ..utilities import compatibility
# from .. import meta
from .model import Model
from abc import ABCMeta, abstractmethod

compatibility.backport()

ABC = compatibility.ABC
Any = compatibility.typing.Any
Optional = compatibility.typing.Optional
Union = compatibility.typing.Union
Sequence = compatibility.typing.Sequence
Callable = compatibility.typing.Callable

# if Any is None:
#     _ItemsParameter = _TypesParameter = None
# else:
#     _ItemsParameter = Optional[
#         Union[
#             Sequence[
#                 Union[type, "Property"],
#                 "Types"
#             ],
#             type,
#             "Property"
#         ]
#     ]
#     _TypesParameter = Sequence[Union[type, "Property"]]
#     _VersionsParameter = Optional[Sequence[Union[str, meta.Version]]]


class Types(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        items=None  # type: _ItemsParameter
    ):
        pass


class Property(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        types=None,  # type: _TypesParameter
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, Callable]
        versions=None,  # type: _VersionsParameter
    ):
        self.types = types
        self.name = name
        self.required = required
        self.versions = versions  # type: meta.Version

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
        # type: (...) -> Optional[Sequence[meta.Version]]
        pass

    @versions.setter
    @abstractmethod
    def versions(
        self,
        versions  # type: _VersionsParameter
    ):
        # type: (...) -> None
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
