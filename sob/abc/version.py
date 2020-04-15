from abc import ABCMeta, abstractmethod
from numbers import Number
from typing import Optional, Sequence, Union


class Version(metaclass=ABCMeta):

    specification: Optional[str]
    equals: Optional[Sequence[Union[str, Number]]]
    not_equals: Optional[Sequence[Union[str, Number]]]
    less_than: Optional[Sequence[Union[str, Number]]]
    less_than_or_equal_to: Optional[Sequence[Union[str, Number]]]
    greater_than: Optional[Sequence[Union[str, Number]]]
    greater_than_or_equal_to: Optional[Sequence[Union[str, Number]]]

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        version_number: Optional[str] = None,
        specification: Optional[str] = None,
        equals: Optional[Sequence[Union[str, Number]]] = None,
        not_equals: Optional[Sequence[Union[str, Number]]] = None,
        less_than: Optional[Sequence[Union[str, Number]]] = None,
        less_than_or_equal_to: Optional[Sequence[Union[str, Number]]] = None,
        greater_than: Optional[Sequence[Union[str, Number]]] = None,
        greater_than_or_equal_to: Optional[Sequence[Union[str, Number]]] = None
    ) -> None:
        pass
