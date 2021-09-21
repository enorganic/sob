import sys
from traceback import format_exception
from typing import Any, Iterable, List, Optional, Tuple, Union

from . import abc
from .utilities.inspect import represent
from .utilities.string import indent


__all__: List[str] = [
    "ValidationError",
    "VersionError",
    "DeserializeError",
    "UnmarshalError",
    "UnmarshalTypeError",
    "UnmarshalValueError",
    "UnmarshalKeyError",
    "ObjectDiscrepancyError",
    "get_exception_text",
    "append_exception_text",
    "IsSubClassAssertionError",
    "IsInstanceAssertionError",
    "IsInAssertionError",
    "NotIsInstanceAssertionError",
    "EqualsAssertionError",
]


class ValidationError(Exception):

    pass


class VersionError(AttributeError):

    pass


class DeserializeError(ValueError):
    """
    This error is raised when data is encountered during deserialization which
    cannot be parsed.
    """

    def __init__(self, data: str, message: str = "") -> None:
        self.data: str = data
        self.message: str = message
        super().__init__(*((data,) + ((message,) if message else ())))

    def __repr__(self) -> str:
        return "\n".join(
            ((self.message,) if self.message else ())
            + (f"Could not parse:\n{self.data}",)
        )

    def __str__(self) -> str:
        return repr(self)


class UnmarshalError(Exception):
    """
    This is an error message raised when data cannot be un-marshalled due to
    not matching metadata specs.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        data: Optional[abc.MarshallableTypes] = None,
        types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
        ] = None,
        item_types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
        ] = None,
        value_types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
        ] = None,
    ) -> None:
        self._message: Optional[str] = None
        self._parameter: Optional[str] = None
        self._index: Union[str, int, None] = None
        self._key: Optional[str] = None
        error_message_lines: List[str] = []
        # Identify which parameter is being used for type validation
        types_label: str = (
            "item_types"
            if item_types
            else "value_types"
            if value_types
            else "types"
        )
        types = item_types or value_types or types
        if types is None:
            error_message_lines.append(
                "The data provided is not an instance of an un-marshallable "
                "type:\n"
            )
        else:
            error_message_lines.append(
                "The data provided does not match any of the expected types "
                "and/or property definitions:\n"
            )
        error_message_lines.append(f"- data: {indent(represent(data))}")
        if types is None:
            types = abc.MARSHALLABLE_TYPES
            types_label = "un-marshallable types"
        type_representation: str = indent(
            represent(tuple(types)), number_of_spaces=2
        )
        error_message_lines.append(f"- {types_label}: {type_representation}")
        if message:
            error_message_lines += ["", message]
        self.message = "\n".join(error_message_lines)

    @property  # type: ignore
    def parameter(self) -> Optional[str]:
        return self._parameter

    @parameter.setter  # type: ignore
    def parameter(self, parameter_name: str) -> None:
        if parameter_name != self.parameter:
            self._parameter = parameter_name
            self.assemble_message()

    @property  # type: ignore
    def message(self) -> Optional[str]:
        return self._message

    @message.setter
    def message(self, message_text: str) -> None:
        if message_text != self.message:
            self._message = message_text
            self.assemble_message()

    @property  # type: ignore
    def index(self) -> Union[str, int, None]:
        return self._index

    @index.setter
    def index(self, index_or_key: Union[str, int, None]) -> None:
        if index_or_key != self.index:
            self._index = index_or_key
            self.assemble_message()

    def assemble_message(self) -> None:
        """
        Assemble the text of the error message.
        """
        messages = []
        if self.parameter:
            messages.append(
                "Errors encountered in attempting to un-marshal %s:"
                % self.parameter
            )
        if self.index is not None:
            messages.append(
                "Errors encountered in attempting to un-marshal the value at "
                "index %s:" % repr(self.index)
            )
        if self.message:
            messages.append(self.message)
        super().__init__("\n".join(messages))


class UnmarshalTypeError(UnmarshalError, TypeError):

    pass


class UnmarshalValueError(UnmarshalError, ValueError):

    pass


class UnmarshalKeyError(KeyError):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class ObjectDiscrepancyError(AssertionError):

    pass


def get_exception_text() -> str:
    """
    When called within an exception, this function returns a text
    representation of the error matching what is found in
    `traceback.print_exception`, but is returned as a string value rather than
    printing.
    """
    return "".join(format_exception(*sys.exc_info()))


def append_exception_text(error: Exception, message: str) -> None:
    """
    Cause `message` to be appended to an error's exception text.
    """
    last_attribute_name: str
    repr_last_attribute_value: str
    for last_attribute_name in ("strerror", "msg"):
        last_attribute_value = getattr(error, last_attribute_name, "")
        if last_attribute_value:
            setattr(
                error, last_attribute_name, f"{last_attribute_value}{message}"
            )
            break
    if not last_attribute_value:
        index: int
        arg: Any
        reversed_args: List[Any] = list(reversed(error.args)) or [""]
        for index, value in enumerate(reversed_args):
            if isinstance(value, str):
                reversed_args[index] = f"{value}{message}"
                break
        error.args = tuple(reversed(reversed_args))


def _repr_or_list(values: Iterable[Any], quotes: str = "") -> str:
    open_quote: str = ""
    close_quote: str = ""
    if quotes:
        open_quote = quotes[0]
        close_quote = quotes[-1]
    repr_values: List[str] = [
        f"{open_quote}{represent(value)}{close_quote}" for value in values
    ]
    if len(repr_values) > 1:
        return " or ".join([", ".join(repr_values[:-1]), repr_values[-1]])
    else:
        return ", ".join(repr_values)


class IsSubClassAssertionError(AssertionError, TypeError):
    """
    TODO
    """

    def __init__(
        self, name: str, value: Any, type_: Union[type, Tuple[type, ...]]
    ) -> None:
        super().__init__(
            "`%s` must be a sub-class of %s (not `%s`)."
            % (
                name,
                (
                    f"`{represent(type_)}`"
                    if isinstance(type_, type)
                    else _repr_or_list(type_, quotes="`")
                ),
                represent(value),
            )
        )


class IsInAssertionError(AssertionError, ValueError):
    """
    TODO
    """

    def __init__(
        self, name: str, value: Any, valid_values: Iterable[Any]
    ) -> None:
        super().__init__(
            f"`{name}` must be "
            f"{_repr_or_list(valid_values, quotes='`')}--not "
            f"{represent(value)}."
        )


class IsInstanceAssertionError(AssertionError, TypeError):
    """
    TODO
    """

    def __init__(
        self, name: str, value: Any, type_: Union[type, Tuple[type, ...]]
    ) -> None:
        super().__init__(
            "`%s` must be an instance of %s (not `%s`)."
            % (
                name,
                (
                    f"`{type_.__name__}`"
                    if isinstance(type_, type)
                    else _repr_or_list(type_, quotes="`")
                ),
                represent(value),
            )
        )


class NotIsInstanceAssertionError(AssertionError, TypeError):
    """
    TODO
    """

    def __init__(
        self, name: str, value: Any, type_: Union[type, Tuple[type, ...]]
    ) -> None:
        super().__init__(
            "`%s` must not be an instance of %s: %s"
            % (
                name,
                (
                    f"`{type_.__name__}`"
                    if isinstance(type_, type)
                    else _repr_or_list(type_, quotes="`")
                ),
                represent(value),
            )
        )


class EqualsAssertionError(AssertionError, ValueError):
    """
    TODO
    """

    def __init__(self, name: str, value: Any, other: Any) -> None:
        super().__init__(
            "Incorrect value for `{}`:\n\n"
            "    {}\n"
            "    !=\n"
            "    {}".format(
                name, repr(value).replace("\n", r"\n"), repr(other)
            )
        )
