from abc import ABCMeta, abstractmethod
from decimal import Decimal
from typing import Optional, Sequence, Union


class Version(metaclass=ABCMeta):

    specification: Optional[str]
    equals: Optional[Sequence[Union[str, float, int, Decimal]]]
    not_equals: Optional[Sequence[Union[str, float, int, Decimal]]]
    less_than: Optional[Sequence[Union[str, float, int, Decimal]]]
    less_than_or_equal_to: Optional[Sequence[Union[str, float, int, Decimal]]]
    greater_than: Optional[Sequence[Union[str, float, int, Decimal]]]
    greater_than_or_equal_to: Optional[
        Sequence[Union[str, float, int, Decimal]]
    ]

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        version_number: Optional[str] = None,
        specification: Optional[str] = None,
        equals: Optional[Sequence[Union[str, float, int, Decimal]]] = None,
        not_equals: Optional[Sequence[Union[str, float, int, Decimal]]] = None,
        less_than: Optional[Sequence[Union[str, float, int, Decimal]]] = None,
        less_than_or_equal_to: Optional[
            Sequence[Union[str, float, int, Decimal]]
        ] = None,
        greater_than: Optional[
            Sequence[Union[str, float, int, Decimal]]
        ] = None,
        greater_than_or_equal_to: Optional[
            Sequence[Union[str, float, int, Decimal]]
        ] = None
    ) -> None:
        pass
