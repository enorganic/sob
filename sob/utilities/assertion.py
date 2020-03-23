from typing import Any, Container, List

from .inspect import qualified_name


def assert_argument_is_instance(
    name: str,
    value: Any,
    type_: type
) -> None:
    if not isinstance(value, type_):
        raise TypeError(
            '`%s` must be an instance of `%s`, not %s.' % (
                name,
                qualified_name(type_),
                repr(value)
            )
        )


def _repr_or_list(values: Container[Any]) -> str:
    repr_values: List[str] = [
        repr(value)
        for value in values
    ]
    if len(repr_values) > 1:
        return ' or '.join([
            ', '.join(repr_values[:-1]),
            repr_values[-1]
        ])
    else:
        return ', '.join(repr_values)


def assert_argument_in(
    name: str,
    value: Any,
    valid_values: Container[Any]
) -> None:
    if value not in valid_values:
        raise TypeError(
            '`%s` must be %s--not %s.' % (
                name,
                _repr_or_list(valid_values),
                repr(value)
            )
        )
