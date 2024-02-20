"""
`sob` is an object serialization/deserialization library intended to facilitate
authoring of API models which are readable and introspective, and to expedite
code and data validation and testing.
"""

from typing import List

# isort: off
from . import (
    utilities,
    errors,
    abc,
    model,
    meta,
    types,
    hooks,
    properties,
    test,
    request,
    thesaurus,
)

# isort: on

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
