from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from .utilities import compatibility
import sys
from traceback import format_exception
# from .abc.model import Model
# from .abc.properties import Property
from .properties.types import TYPES
from .utilities import qualified_name

compatibility.backport()

Optional = compatibility.typing.Optional
Any = compatibility.typing.Any
Sequence = compatibility.typing.Sequence
Union = compatibility.typing.Union


class ValidationError(Exception):

    pass


class VersionError(AttributeError):

    pass


class UnmarshalError(Exception):

    def __init__(
        self,
        message=None,  # type: Optional[str]
        data=None,  # type: Optional[Any]
        types=None,  # type: Optional[Sequence[Model, Property, type]]
        item_types=None,  # type: Optional[Sequence[Model, Property, type]]
        value_types=None  # type: Optional[Sequence[Model, Property, type]]
    ):
        # type: (...) -> None
        """
        Generate a comprehensible error message for data which could not be
        un-marshalled according to spec, and raise the appropriate exception
        """
        self._message = None  # type: Optional[str]
        self._parameter = None  # type: Optional[str]
        self._index = None  # type: Optional[int]
        self._key = None  # type: Optional[str]
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
    def parameter(self):
        # type: (...) -> Optional[str]
        return self._parameter

    @parameter.setter
    def parameter(self, parameter_name):
        # type: (str) -> None
        if parameter_name != self.parameter:
            self._parameter = parameter_name
            self.assemble_message()

    @property
    def message(self):
        # type: (...) -> Optional[str]
        return self._message

    @message.setter
    def message(self, message_text):
        # type: (str) -> None
        if message_text != self.message:
            self._message = message_text
            self.assemble_message()

    @property
    def index(self):
        # type: (...) -> Optional[int]
        return self._index

    @index.setter
    def index(self, index_or_key):
        # type: (Union[str, int]) -> None
        if index_or_key != self.index:
            self._index = index_or_key
            self.assemble_message()

    def assemble_message(self):

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

    def __init__(self, message):
        # type (str) -> None
        self.message = message

    def __str__(self):
        return self.message


def get_exception_text():
    # type: (...) -> str
    """
    When called within an exception, this function returns a text
    representation of the error matching what is found in
    `traceback.print_exception`, but is returned as a string value rather than
    printing.
    """
    return ''.join(format_exception(*sys.exc_info()))
