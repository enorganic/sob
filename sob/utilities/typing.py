from datetime import date, datetime
from decimal import Decimal
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
    int, float, Decimal,
    date, datetime,
    Null
]