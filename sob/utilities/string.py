import re
from keyword import iskeyword
from typing import List, Optional, Tuple
from unicodedata import normalize

from .inspect import BUILTINS_DICT


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
    """
    name: str = string
    # Replace accented and otherwise modified latin characters with their
    # basic latin equivalent
    name = normalize('NFKD', name)
    # Replace any remaining non-latin characters with underscores
    name = re.sub(
        r'([^\x20-\x7F]|\s)+',
        '_',
        name
    )
    # Insert underscores between lowercase and uppercase characters
    name = re.sub(
        r'([a-z])([A-Z])',
        r'\1_\2',
        name
    )
    # Insert underscores between uppercase characters and following uppercase
    # characters which are followed by lowercase characters (indicating the
    # latter uppercase character was intended as part of a capitalized word
    name = re.sub(
        r'([A-Z])([A-Z])([a-z])',
        r'\1_\2\3',
        name
    )
    # Replace any series of one or more non-alphanumeric characters remaining
    # with a single underscore
    name = re.sub(
        r'[^\w_]+',
        '_',
        name
    ).lower()
    # Only insert underscores between letters and numbers if camelCasing is
    # found in the original string
    if string != string.lower() and string != string.upper():
        name = re.sub(
            r'([0-9])([a-zA-Z])',
            r'\1_\2',
            name
        )
        name = re.sub(
            r'([a-zA-Z])([0-9])',
            r'\1_\2',
            name
        )
    # Replace any two or more adjacent underscores with a single underscore
    name = re.sub(
        r'__+',
        '_',
        name
    )
    # Append an underscore to the keyword until it does not conflict with any
    # python keywords or built-ins
    while iskeyword(name) or (name in BUILTINS_DICT):
        name += '_'
    return name


def class_name(string):
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
    """
    name = camel(string, capitalize=True)
    if iskeyword(name) or (name in BUILTINS_DICT):
        name += '_'
    return name


_UNNACCENTED_ALPHANUMERIC_CHARACTERS = (
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
)


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
    fyiIsAnAcronym

    >>> print(camel('in-you-go'))
    inYouGo

    >>> print(camel('False'))
    false

    >>> print(camel('True'))
    true

    >>> print(camel('in'))
    in
    """
    string = normalize('NFKD', string)
    characters = []
    if not capitalize:
        string = string.lower()
    capitalize_next = capitalize
    for substring in string:
        if substring in _UNNACCENTED_ALPHANUMERIC_CHARACTERS:
            if capitalize_next:
                if capitalize or characters:
                    substring = substring.upper()
            characters.append(substring)
            capitalize_next = False
        else:
            capitalize_next = True
    character_string = ''.join(characters)
    return character_string


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
    words = []
    character_type = None
    acronym = False
    for s in string:
        if s in '0123456789':
            if character_type == 0:
                words[-1].append(s)
            else:
                words.append([s])
            character_type = 0
            acronym = False
        elif s in 'abcdefghijklmnopqrstuvwxyz':
            if character_type == 1:
                words[-1].append(s)
            elif character_type == 2:
                if acronym:
                    words.append([words[-1].pop()] + [s])
                else:
                    words[-1].append(s)
            else:
                words.append([s])
            character_type = 1
            acronym = False
        elif s in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if character_type == 2:
                words[-1].append(s)
                acronym = True
            else:
                words.append([s])
                acronym = False
            character_type = 2
        else:
            if character_type == 3:
                words[-1].append(s)
            else:
                words.append([s])
            character_type = 3
    return tuple(
        ''.join(w) for w in words
    )


def indent(
    string: str,
    number_of_spaces: int = 4,
    start: int = 1,
    stop: Optional[int] = None
) -> str:
    """
    Indent text by `number_of_spaces` starting at line index `start` and
    stopping at line index `stop`.
    """
    indented_text = string
    if ('\n' in string) or start == 0:
        lines = string.split('\n')
        if stop:
            if stop < 0:
                stop = len(lines) - stop
        else:
            stop = len(lines)
        for i in range(start, stop):
            lines[i] = (' ' * number_of_spaces) + lines[i]
        indented_text = '\n'.join(lines)
    return indented_text


_URL_DIRECTORY_AND_FILE_NAME_RE = re.compile(r'^(.*/)([^/]*)')


def url_directory_and_file_name(url: str) -> Tuple[str, str]:
    """
    Split a URL into a directory path and file name
    """
    directory: str
    file_name: str
    directory, file_name = _URL_DIRECTORY_AND_FILE_NAME_RE.match(url).groups()
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
        relative_url = ''
        # URLs are not case-sensitive
        base_url = base_url.lower()
        lowercase_absolute_url = absolute_url.lower()
        while base_url and (
            base_url.lower() != lowercase_absolute_url[:len(base_url)]
        ):
            relative_url = '../' + relative_url
            base_url = url_directory_and_file_name(base_url[:-1])[0]
        relative_url += absolute_url[len(base_url):]
    return relative_url


_LINE_LENGTH: int = 79


def split_long_comment_line(
    line: str,
    max_line_length: int = _LINE_LENGTH,
    prefix: str = '#'
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
        indent_: str = re.match(
            (
                r'^[ ]*(?:%s[ ]*)?' % prefix
                if prefix else
                r'^[ ]*'
            ),
            line
        ).group()
        indent_length = len(indent_)
        words = re.split(r'([\w]*[\w,/"\'.;\-?`])', line[indent_length:])
        lines: List[str] = []
        wrapped_line: str = ''
        for word in words:
            if (
                len(wrapped_line) + len(word) + indent_length
            ) <= max_line_length:
                wrapped_line += word
            else:
                lines.append(indent_ + wrapped_line.rstrip())
                wrapped_line = '' if not word.strip() else word
        if wrapped_line:
            lines.append(indent_ + wrapped_line.rstrip())
        wrapped_line = '\n'.join(lines)
    else:
        wrapped_line: str = line
    return wrapped_line


def split_long_docstring_lines(
    docstring: str,
    max_line_length: int = _LINE_LENGTH
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
    indent_: str = '    '
    if '\t' in docstring:
        docstring = docstring.replace('\t', indent_)
    lines = docstring.split('\n')
    indentation_length = float('inf')
    for line in lines:
        match = re.match(r'^[ ]+', line)
        if match:
            indentation_length = min(indentation_length, len(match.group()))
        else:
            indentation_length = 0
            break
    wrapped_lines = []
    for line in lines:
        wrapped_lines.append(
            split_long_comment_line(
                indent_ + line[indentation_length:],
                max_line_length,
                prefix=''
            )
        )
    return '\n'.join(wrapped_lines)
