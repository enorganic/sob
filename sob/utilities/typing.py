from datetime import date, datetime
from decimal import Decimal
from numbers import Number
from typing import (
    Union, MutableMapping, Sequence, MutableSequence, MutableSet, Generator,
    AnyStr
)
from .types import NoneType, Null

JSONTypes = Union[
    str, int, float, bool,
    MutableMapping,
    MutableSequence,
    NoneType
]
MarshallableTypes = Union[
    bool,
    AnyStr,
    MutableMapping,
    MutableSet,
    Sequence,
    Generator,
    Number, Decimal,
    date, datetime,
    Null
]