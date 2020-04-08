from abc import ABC, abstractmethod
from typing import Optional, Union, Sequence, Iterable


class Types(ABC):

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        items: Optional[
            Union[
                Sequence[
                    Union[type, object]
                ],
                type,
                object
            ]
        ] = None
    ) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[Union[type, object]]:
        pass

    @abstractmethod
    def __setitem__(self, index: int, value: Union[type, object]) -> None:
        pass

    @abstractmethod
    def append(
        self,
        value: Union[type, object]
    ) -> None:
        pass

    @abstractmethod
    def __delitem__(self, index: int) -> None:
        pass

    @abstractmethod
    def pop(self, index: int = -1) -> Union[type, object]:
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


class ImmutableTypes(Types, ABC):

    pass
