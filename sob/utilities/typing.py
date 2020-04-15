from collections.abc import Sequence, Set
from datetime import date, datetime
from decimal import Decimal
from numbers import Number
from types import GeneratorType
from typing import Union
from .types import NoneType, Null

JSONTypes = Union[str, dict, list, int, float, bool, NoneType]
MarshallableTypes = Union[
    str, bytes, bool,
    dict,
    Set, Sequence, GeneratorType,
    Number, Decimal,
    date, datetime,
    Null
]