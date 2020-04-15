from typing import Any, List, Tuple, Union, Iterable

from .inspect import represent


def assert_argument_is_instance(
    name: str,
    value: Any,
    type_: Union[type, Tuple[type, ...]]
) -> None:
    if not isinstance(value, type_):
        raise TypeError(
            '`%s` must be an instance of %s (not `%s`).' % (
                name,
                (
                    f'`{type_.__name__}`'
                    if isinstance(type_, type) else
                    _repr_or_list(type_, quotes='`')
                ),
                represent(value)
            )
        )


def assert_argument_is_subclass(
    name: str,
    value: Any,
    type_: Union[type, Tuple[type, ...]]
) -> None:
    if not issubclass(value, type_):
        raise TypeError(
            '`%s` must be a sub-class of %s (not `%s`).' % (
                name,
                (
                    f'`{represent(type_)}`'
                    if isinstance(type_, type) else
                    _repr_or_list(type_, quotes='`')
                ),
                represent(value)
            )
        )


def _repr_or_list(
    values: Iterable[Any],
    quotes: str = ''
) -> str:
    open_quote: str = ''
    close_quote: str = ''
    if quotes:
        open_quote = quotes[0]
        close_quote = quotes[-1]
    repr_values: List[str] = [
        f'{open_quote}{represent(value)}{close_quote}'
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
    valid_values: Iterable[Any]
) -> None:
    if value not in valid_values:
        raise TypeError(
            '`%s` must be %s--not %s.' % (
                name,
                _repr_or_list(valid_values, quotes='`'),
                represent(value)
            )
        )
