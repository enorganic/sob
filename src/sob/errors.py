from __future__ import annotations

import sys
from traceback import format_exception
from typing import TYPE_CHECKING, Any

from sob import abc
from sob._types import DefinitionExistsError
from sob.utilities import indent, represent

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__: tuple[str, ...] = (
    "ValidationError",
    "VersionError",
    "DeserializeError",
    "UnmarshalError",
    "UnmarshalTypeError",
    "UnmarshalValueError",
    "get_exception_text",
    "append_exception_text",
    "DefinitionExistsError",
)


class ValidationError(Exception):
    """
    This error is raised when `sob.validate` encounters extraneous attributes
    associated with a model instance, or discovers missing required attributes.
    """


class VersionError(AttributeError):
    """
    This error is raised when versioning an object fails due to
    having data which is incompatible with the target version.
    """


class DeserializeError(ValueError):
    """
    This error is raised when data is encountered during deserialization which
    cannot be parsed.

    Attributes:
        data: The data that could not be parsed.
        message: Additional information about the error.
    """

    def __init__(self, data: str, message: str = "") -> None:
        """
        Parameters:
            data: The data that could not be parsed.
            message: An optional message to include with the error.
        """
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

    Attributes:
        message:
        parameter:
    """

    def __init__(
        self,
        message: str | None = None,
        data: abc.MarshallableTypes | None = None,
        types: Iterable[abc.Property | type] | abc.Types | None = None,
        item_types: Iterable[abc.Property | type] | abc.Types | None = None,
        value_types: Iterable[abc.Property | type] | abc.Types | None = None,
    ) -> None:
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
        super().__init__("\n".join(error_message_lines))


class UnmarshalTypeError(UnmarshalError, TypeError):
    pass


class UnmarshalValueError(UnmarshalError, ValueError):
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
