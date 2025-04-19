from __future__ import annotations

import builtins
import collections
import enum
import re
import sys
from inspect import (
    FrameInfo,
    getargvalues,
    getsource,
    stack,
)
from keyword import iskeyword
from re import Match, Pattern
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable
from unicodedata import normalize

from sob._types import UNDEFINED, Undefined
from sob._utilities import deprecated

if TYPE_CHECKING:
    from collections.abc import Iterable

_DIGITS: str = "0123456789"
_LOWERCASE_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz"
_UPPERCASE_ALPHABET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ALPHANUMERIC_CHARACTERS = (
    f"{_DIGITS}" f"{_UPPERCASE_ALPHABET}" f"{_LOWERCASE_ALPHABET}"
)
_URL_DIRECTORY_AND_FILE_NAME_RE: Pattern = re.compile(r"^(.*/)([^/]*)")
MAX_LINE_LENGTH: int = 79


def get_property_name(string: str) -> str:
    """
    Converts a "camelCased" attribute/property name, a name which conflicts
    with a python keyword, or an otherwise non-compatible string to a PEP-8
    compliant property name.

    Examples:

        >>> print(get_property_name("theBirdsAndTheBees"))
        the_birds_and_the_bees

        >>> print(get_property_name("theBirdsAndTheBEEs"))
        the_birds_and_the_bees

        >>> print(get_property_name("theBirdsAndTheBEEsEs"))
        the_birds_and_the_be_es_es

        >>> print(get_property_name("FYIThisIsAnAcronym"))
        fyi_this_is_an_acronym

        >>> print(get_property_name("in"))
        in_

        >>> print(get_property_name("id"))
        id_

        >>> print(get_property_name("one2one"))  # No change needed
        one2one

        >>> print(get_property_name("One2One"))
        one_2_one

        >>> print(get_property_name("@One2One"))
        one_2_one

        >>> print(get_property_name("One2One-ALL"))
        one_2_one_all

        >>> print(get_property_name("one2one-ALL"))
        one2one_all
    """
    name: str = string
    # Replace accented and otherwise modified latin characters with their
    # basic latin equivalent
    name = normalize("NFKD", name)
    # Replace any remaining non-latin characters with underscores
    name = re.sub(r"([^\x20-\x7F]|\s)+", "_", name)
    # Only insert underscores between letters and numbers if camelCasing is
    # found in the original string
    if re.search(r"[A-Z][a-z]", name) or re.search(r"[a-z][A-Z]", name):
        name = re.sub(r"([0-9])([a-zA-Z])", r"\1_\2", name)
        name = re.sub(r"([a-zA-Z])([0-9])", r"\1_\2", name)
    # Insert underscores between lowercase and uppercase characters
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    # Insert underscores between uppercase characters and following uppercase
    # characters which are followed by lowercase characters (indicating the
    # latter uppercase character was intended as part of a capitalized word),
    # except where the trailing lowercase character is a solo lowercase "s"
    # (pluralizing the acronym).
    name = re.sub(r"([A-Z])([A-Z])([a-rt-z]|s(?!\b))", r"\1_\2\3", name)
    # Replace any series of one or more non-alphanumeric characters remaining
    # with a single underscore
    name = re.sub(r"[^\w_]+", "_", name).lower()
    # Replace any two or more adjacent underscores with a single underscore
    name = re.sub(r"__+", "_", name)
    # Append an underscore to the keyword until it does not conflict with any
    # python keywords, built-ins, or potential module imports
    while (
        iskeyword(name)
        or (name in builtins.__dict__)
        or name in {"self", "decimal", "datetime", "typing"}
    ):
        name += "_"
    return name.lstrip("_")


property_name = deprecated(
    "`sob.utilities.property_name` is deprecated, and will be removed in sob "
    "3. Please use `sob.utilities.get_property_name` instead."
)(get_property_name)


def get_class_name(string: str) -> str:
    """
    This function accepts a string and returns a variation of that string
    which is a PEP-8 compatible python class name.

    Examples:

        >>> print(get_class_name("the birds and the bees"))
        TheBirdsAndTheBees

        >>> print(get_class_name("the-birds-and-the-bees"))
        TheBirdsAndTheBees

        >>> print(get_class_name("**the - birds - and - the - bees**"))
        TheBirdsAndTheBees

        >>> print(get_class_name("FYI is an acronym"))
        FYIIsAnAcronym

        >>> print(get_class_name("in-you-go"))
        InYouGo

        >>> print(get_class_name("False"))
        False_

        >>> print(get_class_name("True"))
        True_

        >>> print(get_class_name("ABC Acronym"))
        ABCAcronym

        >>> print(get_class_name("AB CD Efg"))
        ABCdEfg
    """
    name = camel(string, capitalize=True)
    while iskeyword(name) or (name in builtins.__dict__):
        name += "_"
    return name


class_name = deprecated(
    "`sob.utilities.class_name` is deprecated, and will be removed in sob 3. "
    "Please use `sob.utilities.get_class_name` instead."
)(get_class_name)


def camel(string: str, *, capitalize: bool = False) -> str:
    """
    This function returns a camelCased representation of the input string.
    When/if an input string corresponds to a python keyword,

    Parameters:
        string: The string to be camelCased.
        capitalize: If this is `true`, the first letter will be capitalized.

    Examples:

        >>> print(camel("the birds and the bees"))
        theBirdsAndTheBees

        >>> print(camel("the birds and the bees", capitalize=True))
        TheBirdsAndTheBees

        >>> print(camel("the-birds-and-the-bees"))
        theBirdsAndTheBees

        >>> print(camel("**the - birds - and - the - bees**"))
        theBirdsAndTheBees

        >>> print(camel("FYI is an acronym"))
        FYIIsAnAcronym

        >>> print(camel("in-you-go"))
        inYouGo

        >>> print(camel("False"))
        false

        >>> print(camel("True"))
        true

        >>> print(camel("in"))
        in

        >>> print(camel("AB CD Efg", capitalize=True))
        ABCdEfg

        >>> print(camel("ABC DEF GHI", capitalize=True))
        AbcDefGhi

        >>> print(camel("ABC_DEF_GHI", capitalize=True))
        AbcDefGhi

        >>> print(camel("ABC DEF GHI"))
        abcDefGhi

        >>> print(camel("ABC_DEF_GHI"))
        abcDefGhi

        >>> print(camel("AB_CDEfg"))
        ABCdEfg
    """
    index: int
    character: str
    string = normalize("NFKD", string)
    characters: list[str] = []
    all_uppercase: bool = string.upper() == string
    capitalize_next: bool = capitalize
    uncapitalize_next: bool = (not capitalize) and (
        len(string) < 2  # noqa: PLR2004
        or all_uppercase
        or not (
            string[0] in _UPPERCASE_ALPHABET
            and string[1] in _UPPERCASE_ALPHABET
        )
    )
    for index, character in enumerate(string):
        if character in _ALPHANUMERIC_CHARACTERS:
            if capitalize_next:
                if all_uppercase:
                    uncapitalize_next = True
                elif capitalize or characters:
                    # This prevents two acronyms which are adjacent from
                    # retaining capitalization (since word separations would
                    # not be possible to identify if caps were kept for both)
                    if characters and (characters[-1] in _UPPERCASE_ALPHABET):
                        uncapitalize_next = True
                    character = character.upper()  # noqa: PLW2901
            elif uncapitalize_next and character:
                if character in _LOWERCASE_ALPHABET:
                    uncapitalize_next = False
                else:
                    character = character.lower()  # noqa: PLW2901
                    # Halt lowercasing if the next character starts a
                    # camelCased word
                    next_index: int = index + 1
                    tail: str = string[next_index:]
                    if (
                        len(tail) > 1
                        and tail[0] in _UPPERCASE_ALPHABET
                        and tail[1] in _LOWERCASE_ALPHABET
                    ):
                        uncapitalize_next = False
            characters.append(character)
            capitalize_next = False
        else:
            capitalize_next = True
            uncapitalize_next = False
    return "".join(characters)


class _CharacterType(enum.Enum):
    DIGIT = enum.auto()
    LOWERCASE = enum.auto()
    UPPERCASE = enum.auto()
    OTHER = enum.auto()


def camel_split(string: str) -> tuple[str, ...]:
    """
    Split a string of camelCased words into a tuple.

    Examples:

        >>> camel_split("theBirdsAndTheBees")
        ('the', 'Birds', 'And', 'The', 'Bees')

        >>> camel_split("theBirdsAndTheBees123")
        ('the', 'Birds', 'And', 'The', 'Bees', '123')

        >>> camel_split("theBirdsAndTheBeesABC123")
        ('the', 'Birds', 'And', 'The', 'Bees', 'ABC', '123')

        >>> camel_split("the-Birds-&-The-Bs-ABC--123")
        ('the', '-', 'Birds', '-&-', 'The', '-', 'Bs', '-', 'ABC', '--', '123')

        >>> camel_split("THEBirdsAndTheBees")
        ('THE', 'Birds', 'And', 'The', 'Bees')
    """
    words: list[list[str]] = []
    preceding_character_type: _CharacterType | None = None
    for character in string:
        character_type: _CharacterType = (
            _CharacterType.LOWERCASE
            if character in _LOWERCASE_ALPHABET
            else (
                _CharacterType.DIGIT
                if character in _DIGITS
                else (
                    _CharacterType.UPPERCASE
                    if character in _UPPERCASE_ALPHABET
                    else _CharacterType.OTHER
                )
            )
        )
        if character_type == _CharacterType.LOWERCASE:
            if preceding_character_type == _CharacterType.LOWERCASE:
                # If following another lowercase character, a lowercase
                # character always continues that word
                words[-1].append(character)
            elif preceding_character_type == _CharacterType.UPPERCASE:
                if len(words[-1]) > 1:
                    # When following a multi-character uppercase word,
                    # the preceding word's last character should be removed
                    # and a new word created from that preceding character
                    # as well as the current lowercase character (until
                    # followed by a lowercase character, the preceding
                    # uppercase character was inferred to be part of an,
                    # however now we know it was either following an acronym,
                    # or following a single-character word)
                    words.append([words[-1].pop(), character])
                else:
                    # When following an uppercase character, a lowercase
                    # character should be added to the preceding word if that
                    # word has only one character thus far
                    words[-1].append(character)
            else:
                words.append([character])
            preceding_character_type = _CharacterType.LOWERCASE
        else:
            # Any type of character besides one from the *lowercase alphabet*
            # should start a new word if it follows a character of a
            # different type
            if preceding_character_type == character_type:
                words[-1].append(character)
            else:
                words.append([character])
            preceding_character_type = character_type
    return tuple("".join(word) for word in words)


def indent(
    string: str,
    number_of_spaces: int = 4,
    start: int = 1,
    stop: int | None = None,
) -> str:
    """
    Indent text by `number_of_spaces` starting at line index `start` and
    stopping at line index `stop`.
    """
    indented_text = string
    if ("\n" in string) or start == 0:
        lines: list[str] = string.split("\n")
        if stop:
            if stop < 0:
                stop = len(lines) - stop
        else:
            stop = len(lines)
        index: int
        for index in range(start, stop):
            line: str = lines[index]
            line_indent: str = " " * number_of_spaces
            lines[index] = f"{line_indent}{line}".rstrip()
        indented_text = "\n".join(lines)
    return indented_text


def _url_directory_and_file_name(url: str) -> tuple[str, str]:
    """
    Split a URL into a directory path and file name
    """
    directory: str
    file_name: str
    matched: Match | None = _URL_DIRECTORY_AND_FILE_NAME_RE.match(url)
    if matched is None:
        raise ValueError(url)
    directory, file_name = matched.groups()
    return directory, file_name


def get_url_relative_to(absolute_url: str, base_url: str) -> str:
    """
    Returns a relative URL given an absolute URL and a base URL
    """
    # If no portion of the absolute URL is shared with the base URL--the
    # absolute URL will be returned
    relative_url: str = absolute_url
    base_url = _url_directory_and_file_name(base_url)[0]
    if base_url:
        relative_url = ""
        # URLs are not case-sensitive
        base_url = base_url.lower()
        lowercase_absolute_url = absolute_url.lower()
        while base_url and (
            base_url.lower() != lowercase_absolute_url[: len(base_url)]
        ):
            relative_url = "../" + relative_url
            base_url = _url_directory_and_file_name(base_url[:-1])[0]
        base_url_length: int = len(base_url)
        relative_url += absolute_url[base_url_length:]
    return relative_url


def _split_long_comment_line(
    line: str, max_line_length: int = MAX_LINE_LENGTH, prefix: str = "#"
) -> str:
    """
    Split a comment (or docstring) line

    Example:

        >>> print(
        ...     _split_long_comment_line(
        ...         "    Lorem ipsum dolor sit amet, consectetur adipiscing "
        ...         "elit. Nullam faucibu odio a urna elementum, eu tempor "
        ...         "nisl efficitur."
        ...     )
        ... )
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam faucibu
            odio a urna elementum, eu tempor nisl efficitur.
    """  # noqa: E501
    if len(line) > max_line_length:
        matched: Match | None = re.match(
            (rf"^[ ]*(?:{prefix}[ ]*)?" if prefix else r"^[ ]*"), line
        )
        if matched is None:
            raise ValueError(line)
        indent_: str = matched.group()
        indent_length = len(indent_)
        words = re.split(r'([\w]*[\w,/"\'.;\-?`])', line[indent_length:])
        lines: list[str] = []
        wrapped_line: str = ""
        for word in words:
            if (
                len(wrapped_line) + len(word) + indent_length
            ) <= max_line_length:
                wrapped_line += word
            else:
                lines.append(indent_ + wrapped_line.rstrip())
                wrapped_line = "" if not word.strip() else word
        if wrapped_line:
            lines.append(f"{indent_}{wrapped_line}".rstrip())
        wrapped_line = "\n".join(lines)
    else:
        wrapped_line = line
    return wrapped_line


def split_long_docstring_lines(
    docstring: str, max_line_length: int = MAX_LINE_LENGTH
) -> str:
    """
    Split long docstring lines.

    Example:

        >>> print(
        ...     split_long_docstring_lines(
        ...         "    Lorem ipsum dolor sit amet, consectetur adipiscing "
        ...         "elit. Nullam faucibu odio a urna elementum, eu tempor "
        ...         "nisl efficitur."
        ...     )
        ... )
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam faucibu
            odio a urna elementum, eu tempor nisl efficitur.
    """  # noqa: E501
    line: str
    indent_: str = "    "
    if "\t" in docstring:
        docstring = docstring.replace("\t", indent_)
    lines: list[str] = docstring.split("\n")
    indentation_length: int = sys.maxsize
    for line in filter(None, lines):
        matched = re.match(r"^[ ]+", line)
        if matched:
            indentation_length = min(indentation_length, len(matched.group()))
        else:
            indentation_length = 0
            break
    indent_ = " " * (indentation_length or 4)
    if indentation_length < sys.maxsize:
        docstring = "\n".join(
            _split_long_comment_line(
                indent_ + line[indentation_length:],
                max_line_length,
                prefix="",
            )
            for line in lines
        )
    # Strip trailing whitespace and empty lines
    return re.sub(r"[ ]+(\n|$)", r"\1", docstring)


def suffix_long_lines(
    text: str,
    max_line_length: int = MAX_LINE_LENGTH,
    suffix: str = "  # noqa: E501",
) -> str:
    """
    This function adds a suffix to the end of any line of code longer than
    `max_line_length`.

    Parameters:
        text: Text representing python code
        max_line_length:
            The length at which a line should have the `suffix` appended. If
            this is a *negative* integer (or zero), the sum of this integer +
            `MAX_LINE_LENGTH` is used
        suffix: The default suffix indicates to linters that
            a long line should be permitted

    Example:

        >>> print(
        ...     suffix_long_lines(
        ...         "A short line...\\n"
        ...         "Lorem ipsum dolor sit amet, consectetur adipiscing "
        ...         "elit. Nullam faucibu odio a urna elementum, eu tempor "
        ...         "nisl efficitur.\\n"
        ...         "...another short line"
        ...     )
        ... )
        A short line...
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam faucibu odio a urna elementum, eu tempor nisl efficitur.  # noqa: E501
        ...another short line

    """  # noqa: E501
    if max_line_length <= 0:
        max_line_length += MAX_LINE_LENGTH

    def suffix_line_if_long(line: str) -> str:
        if len(line) > max_line_length and not line.endswith(suffix):
            line = f"{line}{suffix}"
        return line

    return "\n".join(map(suffix_line_if_long, text.split("\n")))


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def iter_properties_values(
    object_: object, *, include_private: bool = False
) -> Iterable[tuple[str, Any]]:
    """
    This function iterates over an object's public (non-callable)
    properties, yielding a tuple comprised of each attribute/property name and
    value.

    Parameters:
        object_:
        include_private: If this is `True`, private properties (those
            starting with an underscore) will be included in the iteration.
    """
    names: Iterable[str] = dir(object_)
    if not include_private:
        names = filter(_is_public, names)

    def get_name_value(name: str) -> tuple[str, str] | None:
        value: Any = getattr(object_, name, lambda: None)
        if callable(value):
            return None
        return name, value

    return filter(None, map(get_name_value, names))


QUALIFIED_NAME_ARGUMENT_TYPES: tuple[Any, ...] = (
    type,
    collections.abc.Callable,
    ModuleType,
)


def get_qualified_name(type_or_module: type | Callable | ModuleType) -> str:
    """
    This function return the fully qualified name for a type or module.

    Examples:

        >>> print(get_qualified_name(get_qualified_name))
        sob.utilities.get_qualified_name

        >>> from sob import model
        >>> print(get_qualified_name(model.marshal))
        sob.model.marshal
    """
    if not isinstance(type_or_module, QUALIFIED_NAME_ARGUMENT_TYPES):
        raise TypeError(type_or_module)
    type_name: str
    if isinstance(type_or_module, ModuleType):
        type_name = type_or_module.__name__
    else:
        type_name = getattr(
            type_or_module,
            "__qualname__",
            getattr(type_or_module, "__name__", ""),
        )
        if "<" in type_name:
            name_part: str
            type_name = ".".join(
                filter(
                    lambda name_part: not name_part.startswith("<"),
                    type_name.split("."),
                )
            )
        if (not type_name) and hasattr(type_or_module, "__origin__"):
            # If this is a generic alias, we can use `repr`
            # to get the qualified type name
            type_name = repr(type_or_module)
        if not type_name:
            msg = (
                "A qualified type name could not be inferred for "
                f"`{type_or_module!r}` "
                f"(an instance of {type(type_or_module).__name__})"
            )
            raise TypeError(msg)
        if type_or_module.__module__ not in (
            "builtins",
            "__builtin__",
            "__main__",
            "__init__",
        ):
            type_name = type_or_module.__module__ + "." + type_name
    return type_name


def _iter_frame_info_names(frame_info: FrameInfo) -> Iterable[str]:
    name_count: int = 0
    if frame_info.function != "<module>":
        yield frame_info.function
        name_count += 1
    arguments, _, _, frame_locals = getargvalues(frame_info.frame)
    if arguments:
        argument: str = arguments[0]
        argument_value: Any = frame_locals[argument]
        argument_value_type: type = type(argument_value)
        if (
            hasattr(argument_value_type, "__name__")
            and hasattr(argument_value_type, "__module__")
            and (
                (argument_value_type.__name__ not in builtins.__dict__)
                or (
                    builtins.__dict__[argument_value_type.__name__]
                    is not argument_value_type
                )
            )
        ):
            yield get_qualified_name(argument_value_type)
            name_count += 1
    if (
        name_count < 2  # noqa: PLR2004
        and ("__name__" in frame_info.frame.f_globals)
    ):
        yield frame_info.frame.f_globals["__name__"]


def get_calling_module_name(depth: int = 1) -> str:
    """
    This function returns the name of the module from which the function
    which invokes this function was called.

    Parameters:
        depth: This defaults to `1`, indicating we want to return the name
            of the module wherein `get_calling_module_name` is being called.
            If set to `2`, it would instead indicate the module.

    Examples:

        >>> print(get_calling_module_name())
        sob.utilities

        >>> print(get_calling_module_name(2))
        doctest
    """
    name: str
    try:
        name = sys._getframe(  # noqa: SLF001
            depth
        ).f_globals.get("__name__", "__main__")
    except (AttributeError, ValueError):
        name = "__main__"
    return name


def get_calling_function_qualified_name(depth: int = 1) -> str | None:
    """
    Return the fully qualified name of the function from within which this is
    being called

    Examples:

        >>> def my_function() -> str:
        ...     return get_calling_function_qualified_name()
        >>> print(my_function())
        sob.utilities.my_function

        >>> class MyClass:
        ...     def __call__(self) -> None:
        ...         return self.my_method()
        ...
        ...     def my_method(self) -> str:
        ...         return get_calling_function_qualified_name()
        >>> print(MyClass()())
        sob.utilities.MyClass.my_method
    """
    if not isinstance(depth, int):
        raise TypeError(depth)
    try:
        stack_ = stack()
    except IndexError:
        return None
    if len(stack_) < (depth + 1):
        return None
    return ".".join(reversed(tuple(_iter_frame_info_names(stack_[depth]))))


def get_source(object_: type | Callable | ModuleType) -> str:
    """
    Get the source code which defined an object.
    """
    object_source: str = getattr(object_, "_source", "")
    if not object_source:
        object_source = getsource(object_)
    return object_source


def _repr_items(items: Iterable) -> str:
    """
    Returns a string representation of the items in a `list`, `tuple`,
    `set`, or `dict.items()`.
    """
    return ",\n".join(indent(represent(item), start=0) for item in items)


def _repr_dict_items(items: Iterable[tuple[Any, Any]]) -> str:
    """
    Returns a string representation of dictionary items.
    """
    key: Any
    value: Any
    lines: list[str] = []
    for key, value in items:
        lines.append(
            f"{indent(represent(key), start=0)}: {indent(represent(value))}"
        )
    return ",\n".join(lines)


def _repr_list(list_instance: list) -> str:
    """
    Returns a string representation of `list` argument values
    """
    if list_instance:
        return f"[\n{_repr_items(list_instance)}\n]"
    return "[]"


def _repr_tuple(tuple_instance: tuple) -> str:
    """
    Returns a string representation of `tuple` argument values
    """
    if tuple_instance:
        comma: str = "," if len(tuple_instance) == 1 else ""
        return f"(\n{_repr_items(tuple_instance)}{comma}\n)"
    return "()"


def _repr_set(set_instance: set) -> str:
    """
    Returns a string representation of `set` argument values
    """
    if set_instance:
        items: str = _repr_items(
            sorted(set_instance, key=lambda item: represent(item))
        )
        return f"{{\n{items}\n}}"
    return "set()"


def _repr_dict(dict_instance: dict) -> str:
    """
    Returns a string representation of `dict` argument values
    """
    items: tuple[tuple[Any, Any], ...] = tuple(dict_instance.items())
    if items:
        return f"{{\n{_repr_dict_items(items)}\n}}"
    return "{}"


def represent(value: Any) -> str:
    """
    Returns a string representation of a value, formatted to minimize
    character width, and utilizing fully qualified class/function names
    (including module) where applicable.

    Parameters:
        value:
    """
    value_representation: str
    if isinstance(value, type):
        value_representation = get_qualified_name(value)
    else:
        value_type: type = type(value)
        if value_type is list:
            value_representation = _repr_list(value)
        elif value_type is tuple:
            value_representation = _repr_tuple(value)
        elif value_type is set:
            value_representation = _repr_set(value)
        elif value_type is dict:
            value_representation = _repr_dict(value)
        else:
            value_representation = repr(value)
            if (
                value_type is str
                and '"' not in value_representation
                and value_representation.startswith("'")
                and value_representation.endswith("'")
            ):
                value_representation = f'"{value_representation[1:-1]}"'
    return value_representation


def get_method(
    object_instance: object,
    method_name: str,
    default: Callable | Undefined | None = UNDEFINED,
) -> Callable[..., Any] | None:
    """
    This function attempts to retrieve an object's method, by name, if the
    method exists. If the object does not have a method with the given name,
    this function returns the `defualt` function (if provided), otherwise
    `None`.

    Parameters:
        object_instance:
        method_name:
        default:
    """
    method: Callable
    try:
        method = getattr(object_instance, method_name)
    except AttributeError:
        if isinstance(default, Undefined):
            raise
        return default
    if callable(method):
        return method
    if isinstance(default, Undefined):
        message: str = (
            f"{get_qualified_name(type(object_instance))}.{method_name} "
            "is not callable."
        )
        raise AttributeError(message)  # noqa: TRY004
    return method
