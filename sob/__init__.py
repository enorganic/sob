"""
`sob` is an object serialization/deserialization library intended to facilitate
authoring of API models which are readable and introspective, and to expedite
code and data validation and testing.
"""
from typing import List

from . import (
   utilities, errors, abc, model, properties, meta, hooks, test, request
)

__all__: List[str] = [
   'utilities', 'abc', 'model', 'errors', 'properties', 'meta', 'hooks',
   'test', 'request'
]
