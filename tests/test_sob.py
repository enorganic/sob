from __future__ import annotations

import functools
import os
from base64 import b64encode
from collections import OrderedDict
from collections.abc import Iterable, Reversible
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, cast

import pytest
from iso8601.iso8601 import parse_date

from sob import abc, meta, model, properties, utilities
from tests import utilities as tests_utilities


class A(model.Object):
    """
    TODO
    """

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
    ):
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


meta.object_writable(A).properties = [  # type: ignore
    ("is_a_class", properties.Boolean()),
    ("boolean", properties.Boolean()),
    ("string", properties.String()),
    ("alpha", properties.Enumerated(values=(1, 2, 3))),
    ("beta", properties.Enumerated(values=(1, 2, 3))),
    ("gamma", properties.Enumerated(values=(1, 2, 3))),
    ("delta", properties.Enumerated(values=(1, 2, 3))),
    ("iso8601_datetime", properties.DateTime(name="iso8601DateTime")),
    ("iso8601_date", properties.Date(name="iso8601Date")),
]


class B(model.Object):
    """
    TODO
    """

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


meta.object_writable(B).properties = [  # type: ignore
    ("is_b_class", properties.Boolean()),
    ("boolean", properties.Boolean()),
    ("string", properties.String()),
    ("integer", properties.Integer()),
    ("alpha", properties.Enumerated(values=("A", "B", "C"))),
    ("beta", properties.Enumerated(values=("A", "B", "C"))),
    ("gamma", properties.Enumerated(values=("A", "B", "C"))),
    ("delta", properties.Enumerated(values=("A", "B", "C"))),
    ("iso8601_datetime", properties.DateTime(name="iso8601DateTime")),
    ("iso8601_date", properties.Date(name="iso8601Date")),
]


class C(model.Object):
    """
    TODO
    """

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


meta.object_writable(C).properties = [  # type: ignore
    ("is_c_class", properties.Boolean()),
    ("string", properties.String()),
    ("integer", properties.Integer()),
    ("alpha", properties.Enumerated(values=(True, False))),
    ("beta", properties.Enumerated(values=(True, False))),
    ("gamma", properties.Enumerated(values=(True, False))),
    ("delta", properties.Enumerated(values=(True, False))),
    ("iso8601_datetime", properties.DateTime(name="iso8601DateTime")),
    ("iso8601_date", properties.Date(name="iso8601Date")),
]


class Tesstee(model.Object):
    """
    TODO
    """

    def __init__(
        self,
        _data: str | bytes | dict | abc.Readable | abc.Object | None = None,
        boolean: bool | None = None,
        string: str | None = None,
        number: float | Decimal | None = None,
        decimal: float | Decimal | None = None,
        integer: int | None = None,
        rainbow: bytes | None = None,
        a: A | None = None,
        b: B | None = None,
        c: C | None = None,
        testy: Tesstee | None = None,
        boolean_array: Iterable[bool] | None = None,
        string_array: Iterable[str] | None = None,
        number_array: Iterable[float | int | Decimal] | None = None,
        integer_array: Iterable[int] | None = None,
        rainbow_array: Iterable[bytes] | None = None,
        testy_array: Iterable[Tesstee] | None = None,
        string_number_boolean: str | float | Decimal | bool | None = None,
        a_b_c: A | B | C | None = None,
        c_b_a: C | B | A | None = None,
        string2testy: dict[str, Tesstee] | None = None,
        string2string2testy: dict[str, dict[str, Tesstee]] | None = None,
        string2a_b_c: dict[str, A | B | C] | None = None,
        string2c_b_a: dict[str, C | B | A] | None = None,
        string2string2a_b_c: dict[str, dict[str, A | B | C]] | None = None,
        string2string2c_b_a: dict[str, dict[str, C | B | A]] | None = None,
        version_switch: int | str | Iterable[int] | None = None,
        version_1: int | None = None,
        version_2: int | None = None,
    ):
        self.boolean = boolean
        self.string = string
        self.number = number
        self.decimal = decimal
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
        super().__init__(_data)


meta.object_writable(Tesstee).properties = {  # type: ignore
    "boolean": properties.Boolean(),
    "string": properties.String(),
    "number": properties.Number(),
    "decimal": properties.Number(),
    "integer": properties.Integer(),
    "rainbow": properties.Bytes(),
    "testy": properties.Property(types=(Tesstee,)),
    "boolean_array": properties.Array(item_types=(bool,), name="booleanArray"),
    "string_array": properties.Array(item_types=(str,), name="stringArray"),
    "number_array": properties.Array(
        item_types=(properties.Number(),), name="numberArray"
    ),
    "integer_array": properties.Array(
        item_types=(properties.Integer(),), name="integerArray"
    ),
    "rainbow_array": properties.Array(
        item_types=(properties.Bytes(),), name="rainbowArray"
    ),
    "testy_array": properties.Array(item_types=(Tesstee,), name="testyArray"),
    "string_number_boolean": properties.Property(
        types=(str, properties.Number(), bool), name="stringNumberBoolean"
    ),
    "a": properties.Property(
        types=(A,),
    ),
    "b": properties.Property(
        types=(B,),
    ),
    "c": properties.Property(
        types=(C,),
    ),
    "a_b_c": properties.Property(types=(A, B, C), name="ABC"),
    "c_b_a": properties.Property(types=(C, B, A), name="CBA"),
    "string2testy": properties.Dictionary(value_types=(Tesstee,)),
    "string2string2testy": properties.Dictionary(
        value_types=(properties.Dictionary(value_types=(Tesstee,)),)
    ),
    "string2a_b_c": properties.Dictionary(
        value_types=(A, B, C), name="string2ABC"
    ),
    "string2c_b_a": properties.Dictionary(
        value_types=(C, B, A), name="string2CBA"
    ),
    "string2string2a_b_c": properties.Dictionary(
        value_types=(
            properties.Dictionary(
                value_types=(A, B, C),
            ),
        ),
        name="string2string2ABC",
    ),
    "string2string2c_b_a": properties.Dictionary(
        value_types=(
            properties.Dictionary(
                value_types=(C, B, A),
            ),
        ),
        name="string2String2CBA",
    ),
    "version_switch": properties.Property(
        types=(
            properties.Integer(versions=("testy<2",)),
            properties.String(versions=("testy>1&testy<3",)),
            properties.Array(item_types=(int,), versions=("testy==3.0",)),
        ),
        name="versionSwitch",
    ),
    "version_1": properties.Integer(versions=("testy==1.0",), name="version1"),
    "version_2": properties.Integer(versions=("testy==2.0",), name="version2"),
}

with open(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "rainbow.png"
    ),
    mode="rb",
) as f:
    _rainbow = f.read()

a = A(
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

b = B(
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

c = C(
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

testy = Tesstee(
    boolean=True,
    string="stringy",
    number=1.0,
    decimal=Decimal("9.99"),
    integer=1,
    rainbow=_rainbow,
    a=a,
    b=b,
    c=c,
    testy=None,
    boolean_array=(True, False, True, False),
    string_array=tuple("ABCDEFG"),
    number_array=(1**n / 3 for n in range(10)),
    integer_array=(1**n for n in range(10)),
    rainbow_array=(_rainbow for n in range(10)),
    testy_array=None,
    string_number_boolean=True,
    a_b_c=deepcopy(b),
    c_b_a=deepcopy(c),
    string2testy={},
    string2string2testy=OrderedDict(
        [("A", {}), ("B", OrderedDict()), ("C", {})]
    ),
    string2a_b_c={},
    string2c_b_a={},
    string2string2a_b_c={"one": {}, "two": {}, "three": {}},
    string2string2c_b_a={"one": {}, "two": {}, "three": {}},
)
testy_deep_copy = deepcopy(testy)

testy.testy = deepcopy(testy)

testy.testy_array = [deepcopy(testy_deep_copy) for i in range(10)]

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


def test_object() -> None:
    # Test deletions
    testy_deep_copy = deepcopy(testy)
    assert testy_deep_copy.string2string2c_b_a is not None
    del testy_deep_copy.string2string2c_b_a
    assert testy_deep_copy.string2string2c_b_a is None


@functools.lru_cache
def _get_testy_path() -> str:
    data_dir: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data/"
    )
    path: str
    # The following accounts for `dict` being ordered in python 3.8+
    if isinstance({}, Reversible):
        path = os.path.join(data_dir, "reversible_dict_testy.json")
    else:
        path = os.path.join(data_dir, "testy.json")
    return path


def test_json_serialization() -> None:
    model.validate(testy)
    tests_utilities.model(testy)
    path: str = _get_testy_path()
    if not os.path.exists(path):
        with open(path, mode="w", encoding="utf-8") as file:
            file.write(model.serialize(testy))
    with open(path, encoding="utf-8") as file:
        serialized_testy = model.serialize(testy).strip()
        file_testy = file.read().strip()
        assert serialized_testy == file_testy
    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data", "rainbow.png"
        ),
        mode="rb",
    ) as file:
        rainbow_bytes = file.read()
        assert testy.rainbow == rainbow_bytes
        assert cast(dict, model.marshal(testy))["rainbow"] == str(
            b64encode(rainbow_bytes), "ascii"
        )
    tests_utilities.model(testy)


def test_json_deserialization() -> None:
    """
    TODO
    """
    with open(
        _get_testy_path(),
        encoding="utf-8",
    ) as f:
        assert Tesstee(cast(abc.Readable, f)) == testy
        error = None
        try:
            Tesstee("[]")
        except TypeError as e:
            error = e
        assert isinstance(error, TypeError)


def test_validation() -> None:
    """
    TODO
    """


def test_utilities() -> None:
    assert utilities.get_calling_function_qualified_name() == (
        "test_sob.test_utilities"
    )

    class TestCallingFunctionQualifiedNameA:
        __module__ = "tests.utilities"

        def __init__(self) -> None:
            assert utilities.get_calling_function_qualified_name() == (
                "tests.utilities.test_utilities."
                "TestCallingFunctionQualifiedNameA.__init__"
            )

    TestCallingFunctionQualifiedNameA()

    class TestCallingFunctionQualifiedNameB:
        def __init__(self) -> None:
            assert utilities.get_calling_function_qualified_name() == (
                "tests.test_sob.test_utilities.TestCallingFunctionQualifie"
                "dNameB.__init__"
            )

    TestCallingFunctionQualifiedNameB()

    class TestCallingFunctionQualifiedNameC:
        class TestCallingFunctionQualifiedNameD:
            def __init__(self) -> None:
                assert utilities.get_calling_function_qualified_name() == (
                    "tests.test_sob.test_utilities.TestCallingFunctionQualifie"
                    "dNameC.TestCallingFunctionQualifiedNameD.__init__"
                )

    TestCallingFunctionQualifiedNameC.TestCallingFunctionQualifiedNameD()
    if hasattr(
        TestCallingFunctionQualifiedNameC.TestCallingFunctionQualifiedNameD,
        "__qualname__",
    ):
        assert utilities.get_qualified_name(
            TestCallingFunctionQualifiedNameC(
                # -
            ).TestCallingFunctionQualifiedNameD
        ) == (
            "tests.test_sob.test_utilities.TestCallingFunctionQualifiedNameC."
            "TestCallingFunctionQualifiedNameD"
        )
    else:
        assert utilities.get_qualified_name(
            TestCallingFunctionQualifiedNameC().TestCallingFunctionQualifiedNameD
        ) == (
            ("" if __name__ == "__main__" else "test_sob.")
            + "TestCallingFunctionQualifiedNameD"
        )
    assert utilities.get_qualified_name(model.Object) == "sob.model.Object"


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
