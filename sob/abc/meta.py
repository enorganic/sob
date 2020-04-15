from abc import ABCMeta, abstractmethod
from typing import (Dict, Iterable, List, Optional, Sequence, Tuple, Union)

from .properties import Property
from .types import Types


class Meta(metaclass=ABCMeta):

    pass


class Object(Meta, metaclass=ABCMeta):

    # noinspection PyUnusedLocal
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


class Dictionary(Meta, metaclass=ABCMeta):

    # noinspection PyUnusedLocal
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


class Array(Meta, metaclass=ABCMeta):

    # noinspection PyUnusedLocal
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


class Properties(Meta, metaclass=ABCMeta):

    # noinspection PyUnusedLocal
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


