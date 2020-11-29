from typing import Any, Tuple, Union, Iterable

from ..errors import (
    EqualsAssertionError,
    IsInAssertionError,
    IsInstanceAssertionError,
    IsSubClassAssertionError,
    NotIsInstanceAssertionError,
)


def assert_is_instance(
    name: str, value: Any, type_: Union[type, Tuple[type, ...]]
) -> None:
    if not isinstance(value, type_):
        raise IsInstanceAssertionError(name, value, type_)


def assert_not_is_instance(
    name: str, value: Any, type_: Union[type, Tuple[type, ...]]
) -> None:
    if isinstance(value, type_):
        raise NotIsInstanceAssertionError(name, value, type_)


def assert_is_subclass(
    name: str, value: Any, type_: Union[type, Tuple[type, ...]]
) -> None:
    if not issubclass(value, type_):
        raise IsSubClassAssertionError(name, value, type_)


def assert_in(name: str, value: Any, valid_values: Iterable[Any]) -> None:
    if value not in valid_values:
        raise IsInAssertionError(name, value, valid_values)


def assert_equals(name: str, value: Any, other: Any) -> None:
    if value != other:
        raise EqualsAssertionError(name, value, other)
