from abc import ABCMeta, abstractmethod
from typing import Iterable, List, Optional, Union

from .properties import Property

__all__: List[str] = [
    'Types',
    'ImmutableTypes'
]


class Types(metaclass=ABCMeta):

    _mutable: bool

    # noinspection PyUnusedLocal,PyMissingConstructor
    @abstractmethod
    def __init__(
        self,
        items: Optional[
            Union[
                Iterable[
                    Union[
                        type,
                        Property
                    ]
                ],
                type,
                Property
            ]
        ] = None
    ) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[Union[type, Property]]:
        pass

    @abstractmethod
    def __next__(self) -> Union[type, Property]:
        pass

    @abstractmethod
    def __setitem__(
        self, index: int, value: Union[type, Property]
    ) -> None:
        pass

    @abstractmethod
    def append(
        self,
        value: Union[type, Property]
    ) -> None:
        pass

    @abstractmethod
    def __delitem__(self, index: int) -> None:
        pass

    @abstractmethod
    def pop(self, index: int = -1) -> Union[
        type,
        Property
    ]:
        pass

    @abstractmethod
    def __copy__(self) -> 'Types':
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict = None) -> 'Types':
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass


class ImmutableTypes(Types, metaclass=ABCMeta):

    pass
