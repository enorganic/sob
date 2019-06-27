"""
This module facilitates backwards compatibility with older python version
(>=2.7)
"""

from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)

import inspect

# Before `collections.abc` existed, the definitions we use from this module
# were in `collections`
try:
    import collections.abc as collections_abc
    import collections
except ImportError:
    import collections
    collections_abc = collections

# Earlier versions of the `collections` library do not include the `Generator`
# class, so when this class is missing--we employ a workaround.
if hasattr(collections_abc, 'Generator'):
    Generator = collections_abc.Generator
else:
    Generator = type(n for n in (1, 2, 3))

BACKWARDS_COMPATIBILITY_IMPORTS = (
    '# region Backwards Compatibility\n'
    'from __future__ import (\n'
    '   nested_scopes, generators, division, absolute_import, with_statement, '
    'print_function, '
    '   unicode_literals\n'
    ')\n'    
    'from future import standard_library\n'
    'standard_library.install_aliases()\n'
    'from future.builtins import *\n'
    '# endregion'
)


def backport():
    # type: (...) -> None
    """
    This function imports future functionality and installs built-ins, if
    necessary
    """
    frame_info = inspect.stack()[1]
    try:
        frame = frame_info.frame
    except AttributeError:
        frame = frame_info[0]
    exec(BACKWARDS_COMPATIBILITY_IMPORTS, frame.f_globals, frame.f_locals)

