"""
`sob` is an object serialization/deserialization library intended to facilitate
authoring of API models which are readable and introspective, and to expedite
code and data validation and testing.
"""
from typing import List

from . import utilities
from . import errors
from . import abc
from . import model
from . import meta
from . import types
from . import hooks
from . import properties
from . import test
from . import request
from . import thesaurus

__all__: List[str] = [
    "utilities",
    "abc",
    "model",
    "errors",
    "properties",
    "meta",
    "types",
    "hooks",
    "test",
    "request",
    "thesaurus",
]
