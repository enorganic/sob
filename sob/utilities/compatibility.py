"""
This module facilitates backwards compatibility with older python version
(>=2.7)
"""

from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
import inspect
import importlib
from future.utils import native_str
from itertools import chain

# Before `collections.abc` existed, the definitions we use from this module
# were in `collections`
try:
    import collections.abc as collections_abc
    import collections
except ImportError:
    import collections
    collections_abc = collections

# Before `urllib.parse` existed, these definitions were in `urllib`
try:
    _urlparse_module = importlib.import_module('urllib.parse')
except ImportError:
    _urlparse_module = importlib.import_module('urlparse')

# We need ABCs to inherit from `ABC` in python 3.4+, but in previous versions
# of python ABC is absent and we need classes to inherit from `object` in
# order to be new-style classes
try:
    from abc import ABC
except ImportError:
    ABC = object

urljoin = _urlparse_module.urljoin
urlparse = _urlparse_module.urlparse

# Earlier versions of the `collections` library do not include the `Generator`
# class, so when this class is missing--we employ a workaround.
if hasattr(collections_abc, 'Generator'):
    Generator = collections_abc.Generator
else:
    Generator = type(n for n in (1, 2, 3))


def _get_typing_module():
    # type: (...) -> object
    """
    The `typing` module did not exist prior to python version 3.5, so we create
    a dummy namespace for older versions
    """
    _typing_names = (
        'AbstractSet',
        'Any',
        'AnyStr',
        'AsyncContextManager',
        'AsyncGenerator',
        'AsyncIterable',
        'AsyncIterator',
        'Awaitable',
        'BinaryIO',
        'ByteString',
        'Callable',
        'ChainMap',
        'ClassVar',
        'Collection',
        'Container',
        'ContextManager',
        'Coroutine',
        'Counter',
        'DefaultDict',
        'Deque',
        'Dict',
        'ForwardRef',
        'FrozenSet',
        'Generator',
        'Generic',
        'Hashable',
        'IO',
        'ItemsView',
        'Iterable',
        'Iterator',
        'KeysView',
        'List',
        'Mapping',
        'MappingView',
        'Match',
        'MethodDescriptorType',
        'MethodWrapperType',
        'MutableMapping',
        'MutableSequence',
        'MutableSet',
        'NamedTuple',
        'NamedTupleMeta',
        'NewType',
        'NoReturn',
        'Optional',
        'Pattern',
        'Reversible',
        'Sequence',
        'Set',
        'Sized',
        'SupportsAbs',
        'SupportsBytes',
        'SupportsComplex',
        'SupportsFloat',
        'SupportsInt',
        'SupportsRound',
        'Text',
        'TextIO',
        'Tuple',
        'Type',
        'TypeVar',
        'Union',
        'ValuesView',
        'WrapperDescriptorTyp'
    )
    try:
        typing_ = importlib.import_module('typing')
        for name in _typing_names:
            if not hasattr(typing_, name):
                setattr(typing_, name, None)
    except ImportError as e:
        typing_ = collections.namedtuple(
            'typing',
            _typing_names
        )(
            *([None] * len(_typing_names))
        )
    return typing_


typing = _get_typing_module()

# A constant representing a number of compatibility imports
BACKWARDS_COMPATIBILITY_IMPORTS = (
    'from __future__ import (\n'
    '   nested_scopes, generators, division, absolute_import, with_statement, '
    'print_function,\n'
    '    unicode_literals\n'
    ')\n'    
    'from future import standard_library\n'
    'standard_library.install_aliases()\n'
    'from future.builtins import *\n'
)


def backport():
    # type: (int) -> None
    """
    This function imports future functionality and installs built-ins, if
    necessary
    """
    for frame_info in inspect.stack():
        frame = frame_info[0]
        exec(BACKWARDS_COMPATIBILITY_IMPORTS, frame.f_globals, frame.f_locals)


def include_native_str(types):
    # type: (Iterable[Any]) -> Iterable(Any)
    if (
        native_str is not str
    ) and (
        str in types
    ) and (
        native_str not in types
    ):
        return chain(*(
            ((type_, native_str) if (type_ is str) else (type_,))
            for type_ in types
        ))
    else:
        return types


