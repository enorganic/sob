import abc
from abc import ABC, ABCMeta, abstractmethod
from numbers import Number
from typing import Optional, Sequence, Union, Dict, Tuple, List, Iterable

from .properties import Property
from .properties.types import Types


class Meta(ABC):

    __metaclass__ = ABCMeta


class Object(Meta, ABC):

    @abstractmethod
    def __init__(
        self,
        properties: Optional[
            Union[
                Dict[
                    str,
                    Property
                ],
                Sequence[
                    Tuple[str, Property]
                ]
            ]
        ] = None
    ) -> None:
        self.properties: Optional[Properties] = None


class Dictionary(Meta, ABC):

    @abstractmethod
    def __init__(
        self,
        value_types: Optional[
            Sequence[
                Union[
                    'Property',
                    type
                ]
            ]
        ] = None
    ) -> None:
        self.value_types: Optional[Types] = None


class Array(Meta, ABC):

    @abstractmethod
    def __init__(
        self,
        item_types: Optional[
            Sequence[
                Union[
                    'Property',
                    type
                ]
            ]
        ] = None
    ) -> None:
        self.item_types: Optional[Types] = None


class Properties(Meta, ABC):

    @abstractmethod
    def __init__(
        self,
        items: Optional[
            Union[
                Dict[
                    str,
                    Property
                ],
                List[
                    Tuple[
                        str,
                        Property
                    ]
                ]
            ]
        ] = None
    ) -> None:
        pass

    @abstractmethod
    def keys(self) -> Iterable[str]:
        pass

    @abstractmethod
    def values(self) -> Iterable[Property]:
        pass

    @abstractmethod
    def items(self) -> Iterable[Tuple[str, Property]]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: Property) -> None:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> Property:
        pass


class Version(Meta, ABC):

    @abstractmethod
    def __init__(
        self,
        version_number: Optional[str] = None,
        specification: Optional[Sequence[str]] = None,
        equals: Optional[Sequence[Union[str, Number]]] = None,
        not_equals: Optional[Sequence[Union[str, Number]]] = None,
        less_than: Optional[Sequence[Union[str, Number]]] = None,
        less_than_or_equal_to: Optional[Sequence[Union[str, Number]]] = None,
        greater_than: Optional[Sequence[Union[str, Number]]] = None,
        greater_than_or_equal_to: Optional[Sequence[Union[str, Number]]] = None
    ) -> None:
        self.specification: Optional[Sequence[str]] = specification
        self.equals: Optional[Sequence[Union[str, Number]]] = equals
        self.not_equals: Optional[Sequence[Union[str, Number]]] = not_equals
        self.less_than: Optional[Sequence[Union[str, Number]]] = less_than
        self.less_than_or_equal_to: Optional[
            Sequence[Union[str, Number]]
        ] = less_than_or_equal_to
        self.greater_than: Optional[
            Sequence[Union[str, Number]]
        ] = greater_than
        self.greater_than_or_equal_to: Optional[
            Sequence[Union[str, Number]]
        ] = greater_than_or_equal_to
