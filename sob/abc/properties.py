from abc import ABC, ABCMeta, abstractmethod
from typing import Callable, Optional, Sequence, Union

from .model import Model
from .meta import Version


class Types(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        items: Optional[
            Union[
                Sequence[
                    Union[type, "Property", "Types"]
                ],
                type,
                "Property"
            ]
        ] = None
    ) -> None:
        pass


class Property(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(
        self,
        types: Sequence[Union[type, 'Property']] = None,
        name: Optional[str] = None,
        required: Union[bool, Callable] = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        self.types = types
        self.name = name
        self.required = required
        self.versions = versions

    @property
    @abstractmethod
    def types(self) -> Optional[Sequence[Union[type, 'Property', Model]]]:
        pass

    @types.setter
    @abstractmethod
    def types(
        self,
        types_or_properties: Optional[Sequence[Union[type, 'Property', Model]]]
    ) -> None:
        pass

    @property
    @abstractmethod
    def versions(self) -> Optional[Sequence[Version]]:
        pass

    @versions.setter
    @abstractmethod
    def versions(
        self,
        versions: Optional[Sequence[Union[str, Version]]]
    ) -> None:
        pass


class String(Property, ABC):

    pass


class Date(Property, ABC):

    pass


class DateTime(Property, ABC):

    pass


class Bytes(Property, ABC):

    pass


class Enumerated(Property, ABC):

    pass


class Number(Property, ABC):

    pass


class Integer(Property, ABC):

    pass


class Boolean(Property, ABC):

    pass


class Array(Property, ABC):

    @property
    @abstractmethod
    def item_types(self) -> Types:
        pass

    @item_types.setter
    @abstractmethod
    def item_types(self, item_types: Types) -> None:
        pass


class Dictionary(Property, ABC):

    @property
    @abstractmethod
    def value_types(self) -> Types:
        pass

    @value_types.setter
    @abstractmethod
    def value_types(self, value_types_: Types) -> None:
        pass
