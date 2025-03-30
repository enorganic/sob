"""
`sob` is an object serialization/deserialization library intended to facilitate
authoring of API models which are readable and introspective, and to expedite
code and data validation and testing.
"""

# isort: off
from sob import (
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

__all__: list[str] = [
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
