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
    thesaurus,
)

# isort: on

__all__: tuple[str, ...] = (
    "utilities",
    "abc",
    "model",
    "errors",
    "properties",
    "meta",
    "types",
    "hooks",
    "request",
    "thesaurus",
)
