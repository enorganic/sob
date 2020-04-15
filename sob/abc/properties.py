from abc import ABCMeta, abstractmethod
from typing import Callable, List, Optional, Iterable, Union

from .version import Version

__all__: List[str] = [
    'types',  # For the backwards-compatibility of `oapi` generated modules
    'Property',
    'Array',
    'Boolean',
    'Bytes',
    'Date',
    'DateTime',
    'Enumerated', 'Integer',
    'Number',
    'Property',
    'String'
]


class Property(metaclass=ABCMeta):

    name: str
    required: bool
    versions: Optional[
        Iterable[Version]
    ]
    types: Optional[
        Union[
            Iterable[Union[type, 'Property']]
        ]
    ]

    # noinspection PyShadowingNames,PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        types: Iterable[Union[type, 'Property']] = None,
        name: Optional[str] = None,
        required: Union[bool, Callable] = False,
        versions: Optional[Iterable[Union[str, Version]]] = None
    ) -> None:
        pass


# noinspection DuplicatedCode
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

    item_types: Optional[Iterable[Union[type, 'Property']]]


class Dictionary(Property, metaclass=ABCMeta):

    value_types: Optional[Iterable[Union[type, 'Property']]]
