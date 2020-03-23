import sys
from traceback import format_exception
from typing import Any, Optional, Sequence, Union

from .abc.model import Model
from .abc.properties import Property
from .properties.types import TYPES
from .utilities.inspect import qualified_name


class ValidationError(Exception):

    pass


class VersionError(AttributeError):

    pass


class UnmarshalError(Exception):
    """
    This is an error message raised when data cannot be un-marshalled due to
    not matching metadata specs.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        data: Optional[Any] = None,
        types: Optional[
            Sequence[
                Union[
                    Model,
                    Property,
                    type
                ]
            ]
        ] = None,
        item_types: Optional[
            Sequence[
                 Union[
                     Model,
                     Property,
                     type
                 ]
            ]
        ] = None,
        value_types: Optional[
            Sequence[
                Union[
                    Model,
                    Property,
                    type
                ]
            ]
        ] = None
    ) -> None:
        self._message: Optional[str] = None
        self._parameter: Optional[str] = None
        self._index: Optional[int] = None
        self._key: Optional[str] = None
        error_message_lines = ['']
        # Identify which parameter is being used for type validation
        types_label = None
        if types:
            types_label = 'types'
        elif item_types:
            types_label = 'item_types'
            types = item_types
        elif value_types:
            types_label = 'value_types'
            types = value_types
        # Assemble the error message
        # Assemble a text representation of the `data`
        data_lines = []
        lines = repr(data).strip().split('\n')
        if len(lines) == 1:
            data_lines.append(lines[0])
        else:
            data_lines.append('')
            for line in lines:
                data_lines.append(
                    '     ' + line
                )
        # Assemble a text representation of the `types`, `item_types`, or
        # `value_types`.
        if types is None:

            error_message_lines.append(
                'The data provided is not an instance of an un-marshallable '
                'type:'
            )

        else:

            error_message_lines.append(
                'The data provided does not match any of the expected types '
                'and/or property definitions:'
            )

        error_message_lines.append(
            ' - data: %s' % '\n'.join(data_lines)
        )

        if types is None:
            types = TYPES
            types_label = 'un-marshallable types'

        types_lines = ['(']

        for type_ in types:

            if isinstance(type_, type):
                lines = (qualified_name(type_),)
            else:
                lines = repr(type_).split('\n')

            for line in lines:
                types_lines.append(
                    '     ' + line
                )

            types_lines[-1] += ','

        types_lines.append('   )')

        error_message_lines.append(
            ' - %s: %s' % (types_label, '\n'.join(types_lines))
        )

        if message:
            error_message_lines += ['', message]

        self.message = '\n'.join(error_message_lines)

    @property
    def parameter(self) -> Optional[str]:
        return self._parameter

    @parameter.setter
    def parameter(self, parameter_name: str) -> None:
        if parameter_name != self.parameter:
            self._parameter = parameter_name
            self.assemble_message()

    @property
    def message(self) -> Optional[str]:
        return self._message

    @message.setter
    def message(self, message_text: str) -> None:
        if message_text != self.message:
            self._message = message_text
            self.assemble_message()

    @property
    def index(self) -> Optional[int]:
        return self._index

    @index.setter
    def index(self, index_or_key: Union[str, int]) -> None:
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
                'Errors encountered in attempting to un-marshal %s:' %
                self.parameter
            )
        if self.index is not None:
            messages.append(
                'Errors encountered in attempting to un-marshal the value at '
                'index %s:' % repr(self.index)
            )
        if self.message:
            messages.append(self.message)
        super().__init__('\n'.join(messages))


class UnmarshalTypeError(UnmarshalError, TypeError):

    pass


class UnmarshalValueError(UnmarshalError, ValueError):

    pass


class UnmarshalKeyError(KeyError):

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self):
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
    return ''.join(format_exception(*sys.exc_info()))
