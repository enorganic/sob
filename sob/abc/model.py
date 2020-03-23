from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Iterable, List, Tuple, Dict

__all__: List[str] = [
    'Model',
    'Object',
    'Dictionary',
    'Array'
]


class Model(ABC):

    __metaclass__ = ABCMeta

    @abstractmethod
    def _marshal(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _validate(self, raise_errors: bool = True) -> None:
        pass


class Object(Model, ABC):

    @abstractmethod
    def __setattr__(self, property_name: str, value: Any) -> None:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def __delattr__(self, key: str) -> None:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass


class Dictionary(Model, ABC):

    @abstractmethod
    def keys(self) -> Iterable[str]:
        pass

    @abstractmethod
    def values(self) -> Iterable[Any]:
        pass

    def items(self) -> Iterable[Tuple[str, Any]]:
        pass


class Array(Model, ABC):

    @abstractmethod
    def append(self, value: Any) -> None:
        pass

    def __iter__(self) -> Iterable[Any]:
        pass

    def __len__(self) -> int:
        pass

    def __getitem__(self, index: int) -> Any:
        pass
