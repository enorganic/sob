from typing import Any, Container, List, Union, Sequence

from .inspect import qualified_name


def assert_argument_is_instance(
    name: str,
    value: Any,
    type_: Union[type, Sequence[type]]
) -> None:
    if not isinstance(value, type_):
        raise TypeError(
            '`%s` must be an instance of %s (not `%s`).' % (
                name,
                (
                    f'`{_repr(type_)}`'
                    if isinstance(type_, type) else
                    _repr_or_list(type_, quotes='`')
                ),
                _repr(value)
            )
        )


def assert_argument_is_subclass(
    name: str,
    value: Any,
    type_: Union[type, Sequence[type]]
) -> None:
    if not issubclass(value, type_):
        raise TypeError(
            '`%s` must be a sub-class of %s (not `%s`).' % (
                name,
                (
                    f'`{_repr(type_)}`'
                    if issubclass(type_, type) else
                    _repr_or_list(type_, quotes='`')
                ),
                _repr(value)
            )
        )


def _repr(value: Any) -> str:
    if isinstance(value, type):
        return qualified_name(value)
    else:
        return repr(value)


def _repr_or_list(
    values: Container[Any],
    quotes: str = ''
) -> str:
    open_quote: str = ''
    close_quote: str = ''
    if quotes:
        open_quote = quotes[0]
        close_quote = quotes[-1]
    repr_values: List[str] = [
        f'{open_quote}{_repr(value)}{close_quote}'
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
                _repr_or_list(valid_values, quotes='`'),
                repr(value)
            )
        )
