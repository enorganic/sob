from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from . import compatibility
import re  # noqa
from unicodedata import normalize  # noqa
from keyword import iskeyword  # noqa
from .inspect import BUILTINS_DICT

compatibility.backport()

urljoin = compatibility.urljoin

Union = compatibility.typing.Union
Optional = compatibility.typing.Optional
Iterable = compatibility.typing.Iterable
Tuple = compatibility.typing.Tuple
Any = compatibility.typing.Any
Callable = compatibility.typing.Callable
AnyStr = compatibility.typing.AnyStr
Iterator = compatibility.typing.Iterator
Sequence = compatibility.typing.Sequence
IO = compatibility.typing.IO

if Any is None:
    KeyValueIterator = None
else:
    KeyValueIterator = Iterator[Tuple[AnyStr, Any]]

# endregion


def property_name(string):
    # type: (str) -> str
    """
    Converts a "camelCased" attribute/property name, or a name which conflicts
    with a python keyword, to a PEP-8 compliant property name.

    >>> print(property_name('theBirdsAndTheBees'))
    the_birds_and_the_bees

    >>> print(property_name('FYIThisIsAnAcronym'))
    fyi_this_is_an_acronym

    >>> print(property_name('in'))
    in_

    >>> print(property_name('id'))
    id_
    """
    name = re.sub(
        r'__+',
        '_',
        re.sub(
            r'[^\w]+',
            '',
            re.sub(
                r'([a-zA-Z])([0-9])',
                r'\1_\2',
                re.sub(
                    r'([0-9])([a-zA-Z])',
                    r'\1_\2',
                    re.sub(
                        r'([A-Z])([A-Z])([a-z])',
                        r'\1_\2\3',
                        re.sub(
                            r'([a-z])([A-Z])',
                            r'\1_\2',
                            re.sub(
                                r'([^\x20-\x7F]|\s)+',
                                '_',
                                normalize('NFKD', string)
                            )
                        )
                    )
                )
            )
        )
    ).lower()
    if iskeyword(name) or (name in BUILTINS_DICT):
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


def camel(string, capitalize=False):
    # type: (str, bool) -> str
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


def camel_split(string):
    # test: (str) -> str
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


def properties_values(object_):
    # type: (object) -> KeyValueIterator
    """
    This function iterates over an object's public (non-callable)
    properties, yielding a tuple comprised of each attribute/property name and
    value
    """
    for attribute in dir(object_):
        if attribute[0] != '_':
            value = getattr(object_, attribute)
            if not callable(value):
                yield attribute, value


def indent(string, number_of_spaces=4, start=1, stop=None):
    # type: (str, int, int, Optional[int]) -> str
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


def url_directory_and_file_name(url):
    # type: (str) -> str
    """
    Split a URL into
    """
    return _URL_DIRECTORY_AND_FILE_NAME_RE.match(url).groups()


def url_relative_to(absolute_url, base_url):
    # type: (str, str) -> str
    """
    Returns a relative URL given an absolute URL and a base URL
    """
    # If no portion of the absolute URL is shared with the base URL--the
    # absolute URL will be returned
    relative_url = absolute_url  # type: str
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
