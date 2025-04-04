from __future__ import annotations
import typing
import decimal
import sob
import tests.test_model


class Tesstee(sob.model.Object):

    __slots__: tuple[str, ...] = (
        "boolean",
        "string",
        "number",
        "decimal_",
        "integer",
        "rainbow",
        "testy",
        "boolean_array",
        "string_array",
        "number_array",
        "integer_array",
        "rainbow_array",
        "testy_array",
        "string_number_boolean",
        "a",
        "b",
        "c",
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
        "required_integer",
        "required_integer_or_string",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        boolean: (
            bool
            | None
        ) = None,
        string: (
            str
            | None
        ) = None,
        number: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        decimal_: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        integer: (
            int
            | None
        ) = None,
        rainbow: (
            bytes
            | None
        ) = None,
        testy: (
            "tests.test_model.Tesstee"
            | None
        ) = None,
        boolean_array: (
            typing.Sequence[
                bool
            ]
            | None
        ) = None,
        string_array: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        number_array: (
            typing.Sequence[
                float
            | int
            | decimal.Decimal
            ]
            | None
        ) = None,
        integer_array: (
            typing.Sequence[
                int
            ]
            | None
        ) = None,
        rainbow_array: (
            typing.Sequence[
                bytes
            ]
            | None
        ) = None,
        testy_array: (
            typing.Sequence[
                "tests.test_model.Tesstee"
            ]
            | None
        ) = None,
        string_number_boolean: (
            str
            | float
            | int
            | decimal.Decimal
            | bool
            | None
        ) = None,
        a: (
            "tests.test_model.A"
            | None
        ) = None,
        b: (
            "tests.test_model.B"
            | None
        ) = None,
        c: (
            "tests.test_model.C"
            | None
        ) = None,
        a_b_c: (
            "tests.test_model.A"
            | "tests.test_model.B"
            | "tests.test_model.C"
            | None
        ) = None,
        c_b_a: (
            "tests.test_model.C"
            | "tests.test_model.B"
            | "tests.test_model.A"
            | None
        ) = None,
        string2testy: (
            typing.Mapping[
                str,
                "tests.test_model.Tesstee"
            ]
            | None
        ) = None,
        string2string2testy: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    "tests.test_model.Tesstee"
                ]
            ]
            | None
        ) = None,
        string2a_b_c: (
            typing.Mapping[
                str,
                "tests.test_model.A"
                | "tests.test_model.B"
                | "tests.test_model.C"
            ]
            | None
        ) = None,
        string2c_b_a: (
            typing.Mapping[
                str,
                "tests.test_model.C"
                | "tests.test_model.B"
                | "tests.test_model.A"
            ]
            | None
        ) = None,
        string2string2a_b_c: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    "tests.test_model.A"
                    | "tests.test_model.B"
                    | "tests.test_model.C"
                ]
            ]
            | None
        ) = None,
        string2string2c_b_a: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    "tests.test_model.C"
                    | "tests.test_model.B"
                    | "tests.test_model.A"
                ]
            ]
            | None
        ) = None,
        version_switch: (
            int
            | str
            | typing.Sequence[
                int
            ]
            | None
        ) = None,
        version_1: (
            int
            | None
        ) = None,
        version_2: (
            int
            | None
        ) = None,
        required_integer: (
            int
            | None
        ) = None,
        required_integer_or_string: (
            int
            | str
            | None
        ) = None
    ) -> None:
        self.boolean: (
            bool
            | None
        ) = boolean
        self.string: (
            str
            | None
        ) = string
        self.number: (
            float
            | int
            | decimal.Decimal
            | None
        ) = number
        self.decimal_: (
            float
            | int
            | decimal.Decimal
            | None
        ) = decimal_
        self.integer: (
            int
            | None
        ) = integer
        self.rainbow: (
            bytes
            | None
        ) = rainbow
        self.testy: (
            "tests.test_model.Tesstee"
            | None
        ) = testy
        self.boolean_array: (
            typing.Sequence[
                bool
            ]
            | None
        ) = boolean_array
        self.string_array: (
            typing.Sequence[
                str
            ]
            | None
        ) = string_array
        self.number_array: (
            typing.Sequence[
                float
            | int
            | decimal.Decimal
            ]
            | None
        ) = number_array
        self.integer_array: (
            typing.Sequence[
                int
            ]
            | None
        ) = integer_array
        self.rainbow_array: (
            typing.Sequence[
                bytes
            ]
            | None
        ) = rainbow_array
        self.testy_array: (
            typing.Sequence[
                "tests.test_model.Tesstee"
            ]
            | None
        ) = testy_array
        self.string_number_boolean: (
            str
            | float
            | int
            | decimal.Decimal
            | bool
            | None
        ) = string_number_boolean
        self.a: (
            "tests.test_model.A"
            | None
        ) = a
        self.b: (
            "tests.test_model.B"
            | None
        ) = b
        self.c: (
            "tests.test_model.C"
            | None
        ) = c
        self.a_b_c: (
            "tests.test_model.A"
            | "tests.test_model.B"
            | "tests.test_model.C"
            | None
        ) = a_b_c
        self.c_b_a: (
            "tests.test_model.C"
            | "tests.test_model.B"
            | "tests.test_model.A"
            | None
        ) = c_b_a
        self.string2testy: (
            typing.Mapping[
                str,
                "tests.test_model.Tesstee"
            ]
            | None
        ) = string2testy
        self.string2string2testy: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    "tests.test_model.Tesstee"
                ]
            ]
            | None
        ) = string2string2testy
        self.string2a_b_c: (
            typing.Mapping[
                str,
                "tests.test_model.A"
                | "tests.test_model.B"
                | "tests.test_model.C"
            ]
            | None
        ) = string2a_b_c
        self.string2c_b_a: (
            typing.Mapping[
                str,
                "tests.test_model.C"
                | "tests.test_model.B"
                | "tests.test_model.A"
            ]
            | None
        ) = string2c_b_a
        self.string2string2a_b_c: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    "tests.test_model.A"
                    | "tests.test_model.B"
                    | "tests.test_model.C"
                ]
            ]
            | None
        ) = string2string2a_b_c
        self.string2string2c_b_a: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    "tests.test_model.C"
                    | "tests.test_model.B"
                    | "tests.test_model.A"
                ]
            ]
            | None
        ) = string2string2c_b_a
        self.version_switch: (
            int
            | str
            | typing.Sequence[
                int
            ]
            | None
        ) = version_switch
        self.version_1: (
            int
            | None
        ) = version_1
        self.version_2: (
            int
            | None
        ) = version_2
        self.required_integer: (
            int
            | None
        ) = required_integer
        self.required_integer_or_string: (
            int
            | str
            | None
        ) = required_integer_or_string
        super().__init__(_data)

