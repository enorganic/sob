import enum
import re
import sys

import builtins
from keyword import iskeyword
from typing import List, Match, Optional, Pattern, Tuple
from unicodedata import normalize


_DIGITS: str = "0123456789"
# noinspection SpellCheckingInspection
_LOWERCASE_ALPHABET: str = "abcdefghijklmnopqrstuvwxyz"
# noinspection SpellCheckingInspection
_UPPERCASE_ALPHABET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ALPHANUMERIC_CHARACTERS = (
    f"{_DIGITS}" f"{_UPPERCASE_ALPHABET}" f"{_LOWERCASE_ALPHABET}"
)
_URL_DIRECTORY_AND_FILE_NAME_RE: Pattern = re.compile(r"^(.*/)([^/]*)")
MAX_LINE_LENGTH: int = 79


def property_name(string: str) -> str:
    """
    Converts a "camelCased" attribute/property name, a name which conflicts
    with a python keyword, or an otherwise non-compatible string to a PEP-8
    compliant property name.

    >>> print(property_name('theBirdsAndTheBees'))
    the_birds_and_the_bees

    >>> print(property_name('FYIThisIsAnAcronym'))
    fyi_this_is_an_acronym

    >>> print(property_name('in'))
    in_

    >>> print(property_name('id'))
    id_

    >>> print(property_name('one2one'))  # No change needed
    one2one

    >>> print(property_name('One2One'))
    one_2_one

    >>> print(property_name('@One2One'))
    one_2_one
    """
    name: str = string
    # Replace accented and otherwise modified latin characters with their
    # basic latin equivalent
    name = normalize("NFKD", name)
    # Replace any remaining non-latin characters with underscores
    name = re.sub(r"([^\x20-\x7F]|\s)+", "_", name)
    # Insert underscores between lowercase and uppercase characters
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    # Insert underscores between uppercase characters and following uppercase
    # characters which are followed by lowercase characters (indicating the
    # latter uppercase character was intended as part of a capitalized word
    name = re.sub(r"([A-Z])([A-Z])([a-z])", r"\1_\2\3", name)
    # Replace any series of one or more non-alphanumeric characters remaining
    # with a single underscore
    name = re.sub(r"[^\w_]+", "_", name).lower()
    # Only insert underscores between letters and numbers if camelCasing is
    # found in the original string
    if string != string.lower() and string != string.upper():
        name = re.sub(r"([0-9])([a-zA-Z])", r"\1_\2", name)
        name = re.sub(r"([a-zA-Z])([0-9])", r"\1_\2", name)
    # Replace any two or more adjacent underscores with a single underscore
    name = re.sub(r"__+", "_", name)
    # Append an underscore to the keyword until it does not conflict with any
    # python keywords or built-ins
    while iskeyword(name) or (name in builtins.__dict__) or name == "self":
        name += "_"
    return name.lstrip("_")


def class_name(string: str) -> str:
    """
    This function accepts a string and returns a variation of that string
    which is a PEP-8 compatible python class name.

    >>> print(class_name('the birds and the bees'))
    TheBirdsAndTheBees

    >>> print(class_name('the-birds-and-the-bees'))
    TheBirdsAndTheBees

    >>> print(class_name('**the - birds - and - the - bees**'))
    TheBirdsAndTheBees

    >>> print(class_name('FYI is an acronym'))
    FYIIsAnAcronym

    >>> print(class_name('in-you-go'))
    InYouGo

    >>> print(class_name('False'))
    False_

    >>> print(class_name('True'))
    True_

    >>> print(class_name('ABC Acronym'))
    ABCAcronym

    >>> print(class_name('AB CD Efg'))
    ABCdEfg
    """
    name = camel(string, capitalize=True)
    while iskeyword(name) or (name in builtins.__dict__):
        name += "_"
    return name


def camel(string: str, capitalize: bool = False) -> str:
    """
    This function returns a camelCased representation of the input string.
    When/if an input string corresponds to a python keyword,

    Parameters:

    - string (str): The string to be camelCased.

    - capitalize (bool):

      If this is `true`, the first letter will be capitalized.

    >>> print(camel('the birds and the bees'))
    theBirdsAndTheBees

    >>> print(camel('the birds and the bees', capitalize=True))
    TheBirdsAndTheBees

    >>> print(camel('the-birds-and-the-bees'))
    theBirdsAndTheBees

    >>> print(camel('**the - birds - and - the - bees**'))
    theBirdsAndTheBees

    >>> print(camel('FYI is an acronym'))
    FYIIsAnAcronym

    >>> print(camel('in-you-go'))
    inYouGo

    >>> print(camel('False'))
    false

    >>> print(camel('True'))
    true

    >>> print(camel('in'))
    in

    >>> print(camel('AB CD Efg', capitalize=True))
    ABCdEfg

    >>> print(camel('ABC DEF GHI', capitalize=True))
    AbcDefGhi

    >>> print(camel('ABC_DEF_GHI', capitalize=True))
    AbcDefGhi

    >>> print(camel('ABC DEF GHI'))
    abcDefGhi

    >>> print(camel('ABC_DEF_GHI'))
    abcDefGhi
    """
    index: int
    character: str
    string = normalize("NFKD", string)
    characters: List[str] = []
    all_uppercase: bool = string.upper() == string
    capitalize_next: bool = capitalize
    uncapitalize_next: bool = (not capitalize) and (
        len(string) < 2
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
                    character = character.upper()
                    # This prevents two acronyms which are adjacent from
                    # retaining capitalization (since word separations would
                    # not be possible to identify if caps were kept for both)
                    if characters and (characters[-1] in _UPPERCASE_ALPHABET):
                        uncapitalize_next = True
            elif uncapitalize_next:
                if character in _LOWERCASE_ALPHABET:
                    uncapitalize_next = False
                else:
                    character = character.lower()
            characters.append(character)
            capitalize_next = False
        else:
            capitalize_next = True
            uncapitalize_next = False
    character_string = "".join(characters)
    return character_string


class _CharacterType(enum.Enum):

    DIGIT = enum.auto()
    LOWERCASE = enum.auto()
    UPPERCASE = enum.auto()
    OTHER = enum.auto()


def camel_split(string: str) -> Tuple[str, ...]:
    """
    Split a string of camelCased words into a tuple.

    Examples:

    >>> print(
    ...     '(%s)' % ', '.join(
    ...         "'%s'" % s for s in camel_split('theBirdsAndTheBees')
    ...     )
    ... )
    ('the', 'Birds', 'And', 'The', 'Bees')
    >>> print(
    ...     '(%s)' % ', '.join(
    ...         "'%s'" % s for s in camel_split('theBirdsAndTheBees123')
    ...     )
    ... )
    ('the', 'Birds', 'And', 'The', 'Bees', '123')
    >>> print(
    ...     '(%s)' % ', '.join(
    ...         "'%s'" % s for s in camel_split('theBirdsAndTheBeesABC123')
    ...     )
    ... )
    ('the', 'Birds', 'And', 'The', 'Bees', 'ABC', '123')
    >>> print(
    ...     '(%s)' % ', '.join(
    ...         "'%s'" % s for s in camel_split(
    ...             'the-Birds-&-The-Bs-ABC--123'
    ...         )
    ...     )
    ... )
    ('the', '-', 'Birds', '-&-', 'The', '-', 'Bs', '-', 'ABC', '--', '123')
    >>> print(
    ...     '(%s)' % ', '.join(
    ...         "'%s'" % s for s in camel_split('THEBirdsAndTheBees')
    ...     )
    ... )
    ('THE', 'Birds', 'And', 'The', 'Bees')
    """
    words: List[List[str]] = []
    preceding_character_type: Optional[_CharacterType] = None
    for character in string:
        character_type: _CharacterType = (
            _CharacterType.LOWERCASE
            if character in _LOWERCASE_ALPHABET
            else _CharacterType.DIGIT
            if character in _DIGITS
            else _CharacterType.UPPERCASE
            if character in _UPPERCASE_ALPHABET
            else _CharacterType.OTHER
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
                    words.append([words[-1].pop()] + [character])
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
    stop: Optional[int] = None,
) -> str:
    """
    Indent text by `number_of_spaces` starting at line index `start` and
    stopping at line index `stop`.
    """
    indented_text = string
    if ("\n" in string) or start == 0:
        lines: List[str] = string.split("\n")
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


def url_directory_and_file_name(url: str) -> Tuple[str, str]:
    """
    Split a URL into a directory path and file name
    """
    directory: str
    file_name: str
    matched: Optional[Match] = _URL_DIRECTORY_AND_FILE_NAME_RE.match(url)
    assert matched is not None
    directory, file_name = matched.groups()
    return directory, file_name


def url_relative_to(absolute_url: str, base_url: str) -> str:
    """
    Returns a relative URL given an absolute URL and a base URL
    """
    # If no portion of the absolute URL is shared with the base URL--the
    # absolute URL will be returned
    relative_url: str = absolute_url
    base_url = url_directory_and_file_name(base_url)[0]
    if base_url:
        relative_url = ""
        # URLs are not case-sensitive
        base_url = base_url.lower()
        lowercase_absolute_url = absolute_url.lower()
        while base_url and (
            base_url.lower() != lowercase_absolute_url[: len(base_url)]
        ):
            relative_url = "../" + relative_url
            base_url = url_directory_and_file_name(base_url[:-1])[0]
        base_url_length: int = len(base_url)
        relative_url += absolute_url[base_url_length:]
    return relative_url


def split_long_comment_line(
    line: str, max_line_length: int = MAX_LINE_LENGTH, prefix: str = "#"
) -> str:
    """
    Split a comment (or docstring) line

    >>> print(split_long_comment_line(
    ...     '    Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
    ...     'Nullam faucibu odio a urna elementum, eu tempor nisl efficitur.'
    ... ))
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam faucibu
        odio a urna elementum, eu tempor nisl efficitur.
    """
    if len(line) > max_line_length:
        matched: Optional[Match] = re.match(
            (r"^[ ]*(?:%s[ ]*)?" % prefix if prefix else r"^[ ]*"), line
        )
        assert matched is not None
        indent_: str = matched.group()
        indent_length = len(indent_)
        words = re.split(r'([\w]*[\w,/"\'.;\-?`])', line[indent_length:])
        lines: List[str] = []
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
    Split long docstring lines

    >>> print(split_long_docstring_lines(
    ...     '    Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
    ...     'Nullam faucibu odio a urna elementum, eu tempor nisl efficitu'
    ... ))
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam faucibu
        odio a urna elementum, eu tempor nisl efficitu
    """
    line: str
    indent_: str = "    "
    if "\t" in docstring:
        docstring = docstring.replace("\t", indent_)
    lines: List[str] = docstring.split("\n")
    indentation_length: int = sys.maxsize
    for line in filter(lambda line: line, lines):
        matched = re.match(r"^[ ]+", line)
        if matched:
            indentation_length = min(indentation_length, len(matched.group()))
        else:
            indentation_length = 0
            break
    if indentation_length < sys.maxsize:
        wrapped_lines: List[str] = []
        for line in lines:
            wrapped_lines.append(
                split_long_comment_line(
                    indent_ + line[indentation_length:],
                    max_line_length,
                    prefix="",
                )
            )
        docstring = "\n".join(wrapped_lines)
    # Strip trailing whitespace and empty lines
    return re.sub(r"[ ]+(\n|$)", r"\1", docstring)


def suffix_long_lines(
    text: str, max_line_length: int = MAX_LINE_LENGTH, suffix: str = "  # noqa"
) -> str:
    """
    This function adds a suffix to the end of any line of code longer than
    `max_line_length`.

    Parameters:

    - text (str): Text representing python code
    - max_line_length (int) = 79:
      The length at which a line should have the `suffix` appended. If
      this is a *negative* integer (or zero), the sum of this integer +
      `MAX_LINE_LENGTH` is used
    - suffix (str) = "  # noqa": The default suffix indicates to linters that
      a long line should be permitted
    """
    if max_line_length <= 0:
        max_line_length += MAX_LINE_LENGTH

    def suffix_line_if_long(line: str) -> str:
        if len(line) > max_line_length and not line.endswith(suffix):
            line = f"{line}{suffix}"
        return line

    return "\n".join(map(suffix_line_if_long, text.split("\n")))
