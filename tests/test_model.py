from __future__ import annotations

import doctest
import os
from base64 import b64encode
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast

import pytest
from iso8601.iso8601 import parse_date

import sob
from tests import utilities as tests_utilities

if TYPE_CHECKING:
    from collections.abc import Iterable

REGRESSION_DATA: Path = Path(__file__).parent / "regression-data"
STATIC_DATA: Path = Path(__file__).parent / "static-data"
TESTY_JSON: Path = REGRESSION_DATA / "testy.json"
RAINBOW_PNG: Path = STATIC_DATA / "rainbow.png"
TESSTEE_MODEL_PY: Path = REGRESSION_DATA / "tesstee_model.py"

# region Test Model


class ObjectA(sob.Object):
    __slots__: tuple[str, ...] = (
        "is_a_class",
        "boolean",
        "string",
        "alpha",
        "beta",
        "gamma",
        "delta",
        "iso8601_datetime",
        "iso8601_date",
    )

    def __init__(
        self,
        _data: str | None = None,
        is_a_class: bool | None = None,
        boolean: bool | None = None,
        string: str | None = None,
        alpha: int | None = None,
        beta: int | None = None,
        gamma: int | None = None,
        delta: int | None = None,
        iso8601_datetime: datetime | None = None,
        iso8601_date: date | None = None,
    ) -> None:
        self.is_a_class = is_a_class
        self.boolean = boolean
        self.string = string
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.iso8601_datetime = iso8601_datetime
        self.iso8601_date = iso8601_date
        super().__init__(_data)


sob.get_writable_object_meta(ObjectA).properties = [  # type: ignore
    ("is_a_class", sob.BooleanProperty()),
    ("boolean", sob.BooleanProperty()),
    ("string", sob.StringProperty()),
    ("alpha", sob.EnumeratedProperty(values=(1, 2, 3))),
    ("beta", sob.EnumeratedProperty(values=(1, 2, 3))),
    ("gamma", sob.EnumeratedProperty(values=(1, 2, 3))),
    ("delta", sob.EnumeratedProperty(values=(1, 2, 3))),
    ("iso8601_datetime", sob.DateTimeProperty(name="iso8601DateTime")),
    ("iso8601_date", sob.DateProperty(name="iso8601Date")),
]


class ArrayA(sob.Array):
    def __init__(
        self,
        items: (
            Iterable[ObjectA] | sob.abc.Readable | str | bytes | None
        ) = None,
    ) -> None:
        super().__init__(items)


sob.get_writable_array_meta(ArrayA).item_types = sob.Types([ObjectA])


class ObjectB(sob.Object):
    __slots__: tuple[str, ...] = (
        "is_b_class",
        "boolean",
        "string",
        "integer",
        "alpha",
        "beta",
        "gamma",
        "delta",
        "iso8601_datetime",
        "iso8601_date",
    )

    def __init__(
        self,
        _: str | None = None,
        is_b_class: bool | None = None,
        boolean: bool | None = None,
        string: str | None = None,
        integer: int | None = None,
        alpha: str | None = None,
        beta: str | None = None,
        gamma: str | None = None,
        delta: str | None = None,
        iso8601_datetime: datetime | None = None,
        iso8601_date: date | None = None,
    ):
        self.is_b_class = is_b_class
        self.boolean = boolean
        self.string = string
        self.integer = integer
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.iso8601_datetime = iso8601_datetime
        self.iso8601_date = iso8601_date
        super().__init__(_)


sob.get_writable_object_meta(ObjectB).properties = [  # type: ignore
    ("is_b_class", sob.BooleanProperty()),
    ("boolean", sob.BooleanProperty()),
    ("string", sob.StringProperty()),
    ("integer", sob.IntegerProperty()),
    ("alpha", sob.EnumeratedProperty(values=("A", "B", "C"))),
    ("beta", sob.EnumeratedProperty(values=("A", "B", "C"))),
    ("gamma", sob.EnumeratedProperty(values=("A", "B", "C"))),
    ("delta", sob.EnumeratedProperty(values=("A", "B", "C"))),
    ("iso8601_datetime", sob.DateTimeProperty(name="iso8601DateTime")),
    ("iso8601_date", sob.DateProperty(name="iso8601Date")),
]


def test_sequence_properties_assignment() -> None:
    """
    Verify that when a list/tuple is assigned to a model's properties
    metadata, that the resulting property is an instance of `sob.Properties`
    """
    object_meta: sob.abc.Meta | None = sob.read_object_meta(ObjectB)
    if (object_meta is None) or not isinstance(object_meta, sob.ObjectMeta):
        raise TypeError(object_meta)
    properties: sob.abc.Properties | None = object_meta.properties
    assert properties is not None
    assert isinstance(properties, sob.Properties)


class ObjectC(sob.Object):
    """
    TODO
    """

    __slots__: tuple[str, ...] = (
        "is_c_class",
        "string",
        "integer",
        "alpha",
        "beta",
        "gamma",
        "delta",
        "iso8601_datetime",
        "iso8601_date",
    )

    def __init__(
        self,
        _: str | None = None,
        is_c_class: bool | None = None,
        string: str | None = None,
        integer: int | None = None,
        alpha: bool | None = None,
        beta: bool | None = None,
        gamma: bool | None = None,
        delta: bool | None = None,
        iso8601_datetime: datetime | None = None,
        iso8601_date: date | None = None,
    ):
        self.is_c_class = is_c_class
        self.string = string
        self.integer = integer
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.iso8601_datetime = iso8601_datetime
        self.iso8601_date = iso8601_date
        super().__init__(_)


sob.get_writable_object_meta(ObjectC).properties = [  # type: ignore
    ("is_c_class", sob.BooleanProperty()),
    ("string", sob.StringProperty()),
    ("integer", sob.IntegerProperty()),
    ("alpha", sob.EnumeratedProperty(values=(True, False))),
    ("beta", sob.EnumeratedProperty(values=(True, False))),
    ("gamma", sob.EnumeratedProperty(values=(True, False))),
    ("delta", sob.EnumeratedProperty(values=(True, False))),
    ("iso8601_datetime", sob.DateTimeProperty(name="iso8601DateTime")),
    ("iso8601_date", sob.DateProperty(name="iso8601Date")),
]


class Tesstee(sob.Object):
    __slots__: tuple[str, ...] = (
        "boolean",
        "string",
        "number",
        "decimal_",
        "integer",
        "rainbow",
        "a",
        "b",
        "c",
        "testy",
        "boolean_array",
        "string_array",
        "number_array",
        "integer_array",
        "rainbow_array",
        "testy_array",
        "string_number_boolean",
        "a_b_c",
        "c_b_a",
        "string2testy",
        "string2string2testy",
        "string2a_b_c",
        "string2c_b_a",
        "string2string2a_b_c",
        "string2string2c_b_a",
        "version_switch",
        "version_1",
        "version_2",
        "array_a",
        "null_value",
    )

    def __init__(
        self,
        _data: (
            str | bytes | dict | sob.abc.Readable | sob.abc.Object | IO | None
        ) = None,
        boolean: bool | None = None,
        string: str | None = None,
        number: float | Decimal | None = None,
        decimal_: float | Decimal | None = None,
        integer: int | None = None,
        rainbow: bytes | None = None,
        a: ObjectA | None = None,
        b: ObjectB | None = None,
        c: ObjectC | None = None,
        testy: Tesstee | None = None,
        boolean_array: Iterable[bool] | None = None,
        string_array: Iterable[str] | None = None,
        number_array: Iterable[float | int | Decimal] | None = None,
        integer_array: Iterable[int] | None = None,
        rainbow_array: Iterable[bytes] | None = None,
        testy_array: Iterable[Tesstee] | None = None,
        string_number_boolean: str | float | Decimal | bool | None = None,
        a_b_c: ObjectA | ObjectB | ObjectC | None = None,
        c_b_a: ObjectC | ObjectB | ObjectA | None = None,
        string2testy: dict[str, Tesstee] | None = None,
        string2string2testy: dict[str, dict[str, Tesstee]] | None = None,
        string2a_b_c: dict[str, ObjectA | ObjectB | ObjectC] | None = None,
        string2c_b_a: dict[str, ObjectC | ObjectB | ObjectA] | None = None,
        string2string2a_b_c: (
            dict[str, dict[str, ObjectA | ObjectB | ObjectC]] | None
        ) = None,
        string2string2c_b_a: (
            dict[str, dict[str, ObjectC | ObjectB | ObjectA]] | None
        ) = None,
        version_switch: int | str | Iterable[int] | None = None,
        version_1: int | None = None,
        version_2: int | None = None,
        required_integer: int | None = None,
        required_integer_or_string: int | str | None = None,
        array_a: ArrayA | None = None,
        null_value: sob.Null | None = None,
    ):
        self.boolean = boolean
        self.string = string
        self.number = number
        self.decimal_ = decimal_
        self.integer = integer
        self.rainbow = rainbow
        self.a = a
        self.b = b
        self.c = c
        self.testy = testy
        self.boolean_array = boolean_array
        self.string_array = string_array
        self.number_array = number_array
        self.integer_array = integer_array
        self.rainbow_array = rainbow_array
        self.testy_array = testy_array
        self.string_number_boolean = string_number_boolean
        self.a_b_c = a_b_c
        self.c_b_a = c_b_a
        self.string2testy = string2testy
        self.string2string2testy = string2string2testy
        self.string2a_b_c = string2a_b_c
        self.string2c_b_a = string2c_b_a
        self.string2string2a_b_c = string2string2a_b_c
        self.string2string2c_b_a = string2string2c_b_a
        self.version_switch = version_switch
        self.version_1 = version_1
        self.version_2 = version_2
        self.required_integer = required_integer
        self.required_integer_or_string = required_integer_or_string
        self.array_a = array_a
        self.null_value = null_value
        super().__init__(_data)


testee_meta: sob.abc.ObjectMeta = sob.get_writable_object_meta(Tesstee)
testee_meta.properties = {  # type: ignore
    "boolean": sob.BooleanProperty(),
    "string": sob.StringProperty(),
    "number": sob.NumberProperty(),
    "decimal_": sob.NumberProperty(),
    "integer": sob.IntegerProperty(),
    "rainbow": sob.BytesProperty(),
    "testy": sob.Property(types=(Tesstee,)),
    "boolean_array": sob.ArrayProperty(
        item_types=(bool,), name="booleanArray"
    ),
    "string_array": sob.ArrayProperty(item_types=(str,), name="stringArray"),
    "number_array": sob.ArrayProperty(
        item_types=(sob.NumberProperty(),), name="numberArray"
    ),
    "integer_array": sob.ArrayProperty(
        item_types=(sob.IntegerProperty(),), name="integerArray"
    ),
    "rainbow_array": sob.ArrayProperty(
        item_types=(sob.BytesProperty(),), name="rainbowArray"
    ),
    "testy_array": sob.ArrayProperty(item_types=(Tesstee,), name="testyArray"),
    "string_number_boolean": sob.Property(
        types=(str, sob.NumberProperty(), bool), name="stringNumberBoolean"
    ),
    "a": sob.Property(
        types=(ObjectA,),
    ),
    "b": sob.Property(
        types=(ObjectB,),
    ),
    "c": sob.Property(
        types=(ObjectC,),
    ),
    "a_b_c": sob.Property(types=(ObjectA, ObjectB, ObjectC), name="ABC"),
    "c_b_a": sob.Property(types=(ObjectC, ObjectB, ObjectA), name="CBA"),
    "string2testy": sob.DictionaryProperty(value_types=(Tesstee,)),
    "string2string2testy": sob.DictionaryProperty(
        value_types=(sob.DictionaryProperty(value_types=(Tesstee,)),)
    ),
    "string2a_b_c": sob.DictionaryProperty(
        value_types=(ObjectA, ObjectB, ObjectC), name="string2ABC"
    ),
    "string2c_b_a": sob.DictionaryProperty(
        value_types=(ObjectC, ObjectB, ObjectA), name="string2CBA"
    ),
    "string2string2a_b_c": sob.DictionaryProperty(
        value_types=(
            sob.DictionaryProperty(
                value_types=(ObjectA, ObjectB, ObjectC),
            ),
        ),
        name="string2string2ABC",
    ),
    "string2string2c_b_a": sob.DictionaryProperty(
        value_types=(
            sob.DictionaryProperty(
                value_types=(ObjectC, ObjectB, ObjectA),
            ),
        ),
        name="string2String2CBA",
    ),
    "version_switch": sob.Property(
        types=(
            sob.IntegerProperty(versions=("testy<2",)),
            sob.StringProperty(versions=("testy>1&testy<3",)),
            sob.ArrayProperty(item_types=(int,), versions=("testy==3.0",)),
        ),
        name="versionSwitch",
    ),
    "version_1": sob.IntegerProperty(
        versions=("testy==1.0",), name="version1"
    ),
    "version_2": sob.IntegerProperty(
        versions=("testy==2.0",), name="version2"
    ),
    "required_integer": sob.IntegerProperty(
        name="requiredInteger", required=True
    ),
    "required_integer_or_string": sob.Property(
        types=sob.Types([int, str]),
        name="requiredIntegerOrString",
        required=True,
    ),
    "array_a": sob.Property(
        types=sob.Types([ArrayA]),
        name="arrayA",
    ),
    "null_value": sob.Property(
        types=(sob.Null,),
        name="nullValue",
    ),
}

with open(
    RAINBOW_PNG,
    mode="rb",
) as f:
    _rainbow = f.read()

a = ObjectA(
    is_a_class=True,
    boolean=True,
    string="a string",
    alpha=1,
    beta=2,
    gamma=3,
    delta=1,
    iso8601_datetime=parse_date("2016-03-28T23:33:41.3116627-0500"),
    iso8601_date=date.fromisoformat("2016-03-28"),
)

b = ObjectB(
    is_b_class=True,
    boolean=False,
    string="b string",
    integer=666,
    alpha="A",
    beta="B",
    gamma="B",
    delta="C",
    iso8601_datetime=parse_date("2016-03-28T23:33:41.3116627-0500"),
    iso8601_date=date.fromisoformat("2016-03-28"),
)

c = ObjectC(
    is_c_class=True,
    string="c string",
    integer=3124,
    alpha=True,
    beta=False,
    gamma=True,
    delta=False,
    iso8601_datetime=parse_date("2001-10-26T21:32:52+02:00"),
    iso8601_date=date.fromisoformat("2001-10-26"),
)

testy: Tesstee = Tesstee(
    boolean=True,
    string="stringy",
    number=1.0,
    decimal_=Decimal("9.99"),
    integer=1,
    rainbow=_rainbow,
    a=a,
    b=b,
    c=c,
    testy=None,
    boolean_array=(True, False, True, False),
    string_array=tuple("ABCDEFG"),
    number_array=(2**n / 3 for n in range(10)),
    integer_array=(2**n for n in range(10)),
    rainbow_array=(_rainbow for n in range(10)),
    testy_array=None,
    string_number_boolean=True,
    a_b_c=deepcopy(b),
    c_b_a=deepcopy(c),
    string2testy={},
    string2string2testy={"A": {}, "B": {}, "C": {}},
    string2a_b_c={},
    string2c_b_a={},
    string2string2a_b_c={
        "one": {"a": ObjectA(is_a_class=True)},
        "two": {"b": ObjectB(is_b_class=True)},
        "three": {"c": ObjectC(is_c_class=True)},
    },
    string2string2c_b_a={
        "one": {"c": ObjectC(is_c_class=True)},
        "two": {"b": ObjectB(is_b_class=True)},
        "three": {"a": ObjectA(is_a_class=True)},
    },
    required_integer=1,
    required_integer_or_string="Two",
    array_a=ArrayA([a]),
    null_value=sob.NULL,
)
testy_deep_copy = deepcopy(testy)
testy.testy = deepcopy(testy)
index: int
testy.testy_array = [deepcopy(testy_deep_copy) for index in range(10)]

if TYPE_CHECKING:
    assert isinstance(testy.string2testy, dict)
    assert isinstance(testy.string2string2testy, dict)
    assert isinstance(testy.string2a_b_c, dict)
    assert isinstance(testy.string2string2a_b_c, dict)

testy.string2testy["A"] = deepcopy(testy_deep_copy)
testy.string2testy["B"] = deepcopy(testy_deep_copy)
testy.string2testy["C"] = deepcopy(testy_deep_copy)

testy.string2string2testy["A"]["A"] = deepcopy(testy_deep_copy)
testy.string2string2testy["A"]["B"] = deepcopy(testy_deep_copy)
testy.string2string2testy["A"]["C"] = deepcopy(testy_deep_copy)
testy.string2string2testy["B"]["A"] = deepcopy(testy_deep_copy)
testy.string2string2testy["B"]["B"] = deepcopy(testy_deep_copy)
testy.string2string2testy["B"]["C"] = deepcopy(testy_deep_copy)
testy.string2string2testy["C"]["A"] = deepcopy(testy_deep_copy)
testy.string2string2testy["C"]["B"] = deepcopy(testy_deep_copy)
testy.string2string2testy["C"]["C"] = deepcopy(testy_deep_copy)

testy.string2a_b_c["B"] = deepcopy(testy_deep_copy.b)  # type: ignore
testy.string2a_b_c["A"] = deepcopy(testy_deep_copy.a)  # type: ignore
testy.string2a_b_c["C"] = deepcopy(testy_deep_copy.c)  # type: ignore
testy.string2c_b_a["A"] = deepcopy(testy_deep_copy.a)  # type: ignore
testy.string2c_b_a["B"] = deepcopy(testy_deep_copy.b)  # type: ignore
testy.string2c_b_a["C"] = deepcopy(testy_deep_copy.c)  # type: ignore

testy.string2string2a_b_c["one"]["A"] = deepcopy(  # type: ignore
    testy_deep_copy.a
)
testy.string2string2a_b_c["one"]["B"] = deepcopy(  # type: ignore
    testy_deep_copy.b
)
testy.string2string2a_b_c["one"]["C"] = deepcopy(  # type: ignore
    testy_deep_copy.c
)
testy.string2string2a_b_c["two"]["A"] = deepcopy(  # type: ignore
    testy_deep_copy.a
)
testy.string2string2a_b_c["two"]["B"] = deepcopy(  # type: ignore
    testy_deep_copy.b
)
testy.string2string2a_b_c["two"]["C"] = deepcopy(  # type: ignore
    testy_deep_copy.c
)
testy.string2string2a_b_c["three"]["A"] = deepcopy(  # type: ignore
    testy_deep_copy.a
)
testy.string2string2a_b_c["three"]["B"] = deepcopy(  # type: ignore
    testy_deep_copy.b
)
testy.string2string2a_b_c["three"]["C"] = deepcopy(  # type: ignore
    testy_deep_copy.c
)
testy.string2string2c_b_a["one"]["A"] = deepcopy(  # type: ignore
    testy_deep_copy.a
)
testy.string2string2c_b_a["one"]["B"] = deepcopy(  # type: ignore
    testy_deep_copy.b
)
testy.string2string2c_b_a["one"]["C"] = deepcopy(  # type: ignore
    testy_deep_copy.c
)
testy.string2string2c_b_a["two"]["A"] = deepcopy(  # type: ignore
    testy_deep_copy.a
)
testy.string2string2c_b_a["two"]["B"] = deepcopy(  # type: ignore
    testy_deep_copy.b
)
testy.string2string2c_b_a["two"]["C"] = deepcopy(  # type: ignore
    testy_deep_copy.c
)
testy.string2string2c_b_a["three"]["A"] = deepcopy(  # type: ignore
    testy_deep_copy.a
)
testy.string2string2c_b_a["three"]["B"] = deepcopy(  # type: ignore
    testy_deep_copy.b
)
testy.string2string2c_b_a["three"]["C"] = deepcopy(  # type: ignore
    testy_deep_copy.c
)

# endregion


def test_doctest() -> None:
    """
    Run docstring tests
    """
    doctest.testmod(sob.model)


def test_copy() -> None:
    """
    Verify that the `deepcopy` method produces identical objects with
    different memory addresses.
    """
    testy_deep_copy: Tesstee = deepcopy(testy)
    assert id(testy_deep_copy) != id(testy)
    assert testy.string2string2c_b_a is not None
    assert testy_deep_copy.string2string2c_b_a is not None
    assert id(testy_deep_copy.string2string2c_b_a["one"]["c"]) != id(
        testy.string2string2c_b_a["one"]["c"]
    )
    assert (
        testy_deep_copy.string2string2c_b_a["one"]["c"]
        == (testy.string2string2c_b_a["one"]["c"])
    )
    del testy_deep_copy.string2string2c_b_a["one"]["c"]
    assert testy.string2string2c_b_a["one"]["c"] is not None


def test_bytes_serialization() -> None:
    with open(
        RAINBOW_PNG,
        mode="rb",
    ) as file:
        rainbow_bytes = file.read()
        assert testy.rainbow == rainbow_bytes
        assert cast(dict, sob.marshal(testy))["rainbow"] == str(
            b64encode(rainbow_bytes), "ascii"
        )


def test_replicate_serialization() -> None:
    """
    This test verifies that a model can be serialized and deserialized
    producing comparable results. This test will only work with models which
    have no extraneous properties (all properties have metadata).
    """
    tests_utilities.validate_serialization_is_replicable(testy)


def test_serialization_regression() -> None:
    """
    This test verifies that a model can be serialized producing identical
    output to previous test runs. Whenever changes are made to Whenever changes
    are made to `testy`, delete the file ./tests/static-data/testy.json
    (The file be recreated the next time the test is run).
    """
    serialized_testy: str = sob.serialize(testy, indent=4).strip()
    if not TESTY_JSON.exists():
        with open(TESTY_JSON, mode="w", encoding="utf-8") as file:
            file.write(serialized_testy)
    with open(TESTY_JSON, encoding="utf-8") as file:
        file_testy = file.read().strip()
        if serialized_testy != file_testy:
            message: str = f"{serialized_testy}\n!=\n{file_testy}"
            raise ValueError(message)


def test_deserialization_regression() -> None:
    """
    This test verifies that a model can be deserialized producing identical
    results to a model recreated from serialized data. Whenever changes are
    made to `testy`, delete the file ./tests/static-data/testy.json
    (The file be recreated the next time the test is run).
    """
    if not TESTY_JSON.exists():
        test_serialization_regression()
    with open(
        TESTY_JSON,
        encoding="utf-8",
    ) as testee_io:
        # Construct from a file object
        assert Tesstee(testee_io) == testy
        # Construct from a string
        testee_io.seek(0)
        testee_str: str = testee_io.read()
        assert Tesstee(testee_str) == testy
        # Construct from a deserialized JSON object
        assert Tesstee(sob.deserialize(testee_str)) == testy
        # Construct via copy
        assert Tesstee(testy) == testy
        # Ensure deserialization from the incorrect type of input raises a
        # TypeError
        error_raised: bool = False
        try:
            Tesstee("[]")
        except TypeError:
            error_raised = True
        assert error_raised


def test_valid_object_validation() -> None:
    sob.validate(testy)


def test_missing_attributes_validation() -> None:
    invalid_testy: Tesstee = deepcopy(testy)
    invalid_testy.required_integer = None
    error_caught: bool = False
    try:
        sob.validate(invalid_testy)
    except sob.ValidationError:
        error_caught = True
    assert error_caught


def test_extraneous_attributes_validation() -> None:
    """
    Ensure that un-marshalling extraneous attributes into an object
    does not raise an error on initialization, but *does* raise a validation
    error when passed to `sob.validate`.
    """
    marshalled_testy: dict = cast(dict, sob.marshal(testy))
    marshalled_testy["extraneous_attribute"] = "extraneous value"
    invalid_testy: Tesstee = Tesstee(marshalled_testy)
    error_caught: bool = False
    try:
        sob.validate(invalid_testy)
    except sob.ValidationError:
        error_caught = True
    assert error_caught


def test_get_model_from_meta_regression() -> None:
    """
    This test verifies that a model's source code can be recreated
    consistently from identical metadata. Whenever changes are
    made to `Tesstee`, delete the file ./tests/static-data/tesstee_model.py
    (The file be recreated the next time the test is run).
    """
    if not TESSTEE_MODEL_PY.parent.exists():
        os.makedirs(TESSTEE_MODEL_PY.parent, exist_ok=True)
    tesstee_source: str = sob.get_models_source(
        sob.get_model_from_meta(
            "ArrayA", cast(sob.ArrayMeta, sob.read_array_meta(ArrayA))
        ),
        sob.get_model_from_meta(
            "ObjectA", cast(sob.ObjectMeta, sob.read_object_meta(ObjectA))
        ),
        sob.get_model_from_meta(
            "ObjectB", cast(sob.ObjectMeta, sob.read_object_meta(ObjectB))
        ),
        sob.get_model_from_meta(
            "ObjectC", cast(sob.ObjectMeta, sob.read_object_meta(ObjectC))
        ),
        sob.get_model_from_meta(
            "Tesstee", cast(sob.ObjectMeta, sob.read_object_meta(Tesstee))
        ),
    ).replace("tests.test_model.", "")
    if TESSTEE_MODEL_PY.exists():
        with open(TESSTEE_MODEL_PY) as testee_model_io:
            assert tesstee_source == testee_model_io.read()
    else:
        with open(TESSTEE_MODEL_PY, mode="w") as testee_model_io:
            testee_model_io.write(tesstee_source)


def test_replace_model_nulls() -> None:
    """
    Verify that `replace_model_nulls` replaces all instances of `sob.NULL`
    with a specified value.
    """
    testy_copy: Tesstee = deepcopy(testy)
    sob.replace_model_nulls(testy_copy, None)
    assert testy_copy.null_value is None


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
