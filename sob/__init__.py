"""
`sob` is an object serialization/deserialization library intended to facilitate
authoring of API models which are readable and introspective, and to expedite
code and data validation and testing.
"""

from typing import List

from . import (
    abc,
    errors,
    hooks,
    meta,
    model,
    properties,
    request,
    test,
    thesaurus,
    types,
    utilities,
)

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
