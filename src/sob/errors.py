from __future__ import annotations

import sys
from traceback import format_exception
from typing import TYPE_CHECKING, Any

from sob import abc
from sob.utilities import indent, represent

if TYPE_CHECKING:
    from collections.abc import Iterable


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
        message: str | None = None,
        data: abc.MarshallableTypes | None = None,
        types: Iterable[abc.Property | type] | abc.Types | None = None,
        item_types: Iterable[abc.Property | type] | abc.Types | None = None,
        value_types: Iterable[abc.Property | type] | abc.Types | None = None,
    ) -> None:
        self._message: str | None = None
        self._parameter: str | None = None
        self._index: str | int | None = None
        self._key: str | None = None
        error_message_lines: list[str] = []
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
    def parameter(self) -> str | None:
        return self._parameter

    @parameter.setter  # type: ignore
    def parameter(self, parameter_name: str) -> None:
        if parameter_name != self.parameter:
            self._parameter = parameter_name
            self.assemble_message()

    @property  # type: ignore
    def message(self) -> str | None:
        return self._message

    @message.setter
    def message(self, message_text: str) -> None:
        if message_text != self.message:
            self._message = message_text
            self.assemble_message()

    @property  # type: ignore
    def index(self) -> str | int | None:
        return self._index

    @index.setter
    def index(self, index_or_key: str | int | None) -> None:
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
                "Errors encountered in attempting to un-marshal "
                f"{self.parameter}:"
            )
        if self.index is not None:
            messages.append(
                "Errors encountered in attempting to un-marshal the value at "
                f"index {self.index}:"
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
    attribute_name: str
    for attribute_name in ("strerror", "msg", "errmsg"):
        attribute_value: str = getattr(error, attribute_name, "")
        if attribute_value:
            setattr(error, attribute_name, f"{attribute_value}{message}")
    found: bool = False
    index: int
    arg: Any
    reversed_args: list[Any] = list(reversed(error.args)) or [""]
    for index, value in enumerate(reversed_args):
        if isinstance(value, str):
            found = True
            reversed_args[index] = f"{value}{message}"
            break
    if found:
        error.args = tuple(reversed(reversed_args))
    else:
        error.args = (message,)
