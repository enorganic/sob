from abc import ABCMeta, abstractmethod
from typing import Callable, Optional, Sequence, Union

from .types import Types


class Property(metaclass=ABCMeta):

    # noinspection PyShadowingNames
    @abstractmethod
    def __init__(
        self,
        types: Sequence[Union[type, 'Property']] = None,
        name: Optional[str] = None,
        required: Union[bool, Callable] = False,
        versions: Optional[Sequence[Union[str, object]]] = None
    ) -> None:
        self.types = types
        self.name = name
        self.required = required
        self.versions = versions

    @property
    @abstractmethod
    def types(self) -> Optional[Types]:
        pass

    @types.setter
    @abstractmethod
    def types(
        self,
        types_or_properties: Optional[
            Sequence[Union[type, 'Property', dict, list]]
        ]
    ) -> None:
        pass

    @property
    @abstractmethod
    def versions(self) -> Optional[Sequence[object]]:
        pass

    @versions.setter
    @abstractmethod
    def versions(
        self,
        versions: Optional[Sequence[Union[str, object]]]
    ) -> None:
        pass


class String(Property, metaclass=ABCMeta):

    pass


class Date(Property, metaclass=ABCMeta):

    pass


class DateTime(Property, metaclass=ABCMeta):

    pass


class Bytes(Property, metaclass=ABCMeta):

    pass


class Enumerated(Property, metaclass=ABCMeta):

    pass


class Number(Property, metaclass=ABCMeta):

    pass


class Integer(Property, metaclass=ABCMeta):

    pass


class Boolean(Property, metaclass=ABCMeta):

    pass


class Array(Property, metaclass=ABCMeta):

    @property
    @abstractmethod
    def item_types(self) -> Types:
        pass

    @item_types.setter
    @abstractmethod
    def item_types(self, item_types: Types) -> None:
        pass


class Dictionary(Property, metaclass=ABCMeta):

    @property
    @abstractmethod
    def value_types(self) -> Types:
        pass

    @value_types.setter
    @abstractmethod
    def value_types(self, value_types_: Types) -> None:
        pass
