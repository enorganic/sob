from __future__ import annotations
import typing
import sob
import datetime
import decimal


class ArrayA(sob.Array):

    def __init__(
        self,
        items: (
            typing.Iterable[
                ObjectA
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


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
        is_a_class: (
            bool
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
        alpha: (
            typing.Any
            | None
        ) = None,
        beta: (
            typing.Any
            | None
        ) = None,
        gamma: (
            typing.Any
            | None
        ) = None,
        delta: (
            typing.Any
            | None
        ) = None,
        iso8601_datetime: (
            datetime.datetime
            | None
        ) = None,
        iso8601_date: (
            datetime.date
            | None
        ) = None
    ) -> None:
        self.is_a_class: (
            bool
            | None
        ) = is_a_class
        self.boolean: (
            bool
            | None
        ) = boolean
        self.string: (
            str
            | None
        ) = string
        self.alpha: (
            typing.Any
            | None
        ) = alpha
        self.beta: (
            typing.Any
            | None
        ) = beta
        self.gamma: (
            typing.Any
            | None
        ) = gamma
        self.delta: (
            typing.Any
            | None
        ) = delta
        self.iso8601_datetime: (
            datetime.datetime
            | None
        ) = iso8601_datetime
        self.iso8601_date: (
            datetime.date
            | None
        ) = iso8601_date
        super().__init__(_data)


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
        is_b_class: (
            bool
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
        integer: (
            int
            | None
        ) = None,
        alpha: (
            typing.Any
            | None
        ) = None,
        beta: (
            typing.Any
            | None
        ) = None,
        gamma: (
            typing.Any
            | None
        ) = None,
        delta: (
            typing.Any
            | None
        ) = None,
        iso8601_datetime: (
            datetime.datetime
            | None
        ) = None,
        iso8601_date: (
            datetime.date
            | None
        ) = None
    ) -> None:
        self.is_b_class: (
            bool
            | None
        ) = is_b_class
        self.boolean: (
            bool
            | None
        ) = boolean
        self.string: (
            str
            | None
        ) = string
        self.integer: (
            int
            | None
        ) = integer
        self.alpha: (
            typing.Any
            | None
        ) = alpha
        self.beta: (
            typing.Any
            | None
        ) = beta
        self.gamma: (
            typing.Any
            | None
        ) = gamma
        self.delta: (
            typing.Any
            | None
        ) = delta
        self.iso8601_datetime: (
            datetime.datetime
            | None
        ) = iso8601_datetime
        self.iso8601_date: (
            datetime.date
            | None
        ) = iso8601_date
        super().__init__(_data)


class ObjectC(sob.Object):

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
        is_c_class: (
            bool
            | None
        ) = None,
        string: (
            str
            | None
        ) = None,
        integer: (
            int
            | None
        ) = None,
        alpha: (
            typing.Any
            | None
        ) = None,
        beta: (
            typing.Any
            | None
        ) = None,
        gamma: (
            typing.Any
            | None
        ) = None,
        delta: (
            typing.Any
            | None
        ) = None,
        iso8601_datetime: (
            datetime.datetime
            | None
        ) = None,
        iso8601_date: (
            datetime.date
            | None
        ) = None
    ) -> None:
        self.is_c_class: (
            bool
            | None
        ) = is_c_class
        self.string: (
            str
            | None
        ) = string
        self.integer: (
            int
            | None
        ) = integer
        self.alpha: (
            typing.Any
            | None
        ) = alpha
        self.beta: (
            typing.Any
            | None
        ) = beta
        self.gamma: (
            typing.Any
            | None
        ) = gamma
        self.delta: (
            typing.Any
            | None
        ) = delta
        self.iso8601_datetime: (
            datetime.datetime
            | None
        ) = iso8601_datetime
        self.iso8601_date: (
            datetime.date
            | None
        ) = iso8601_date
        super().__init__(_data)


class Tesstee(sob.Object):

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
        "array_a",
        "null_value",
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
            Tesstee
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
                Tesstee
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
            ObjectA
            | None
        ) = None,
        b: (
            ObjectB
            | None
        ) = None,
        c: (
            ObjectC
            | None
        ) = None,
        a_b_c: (
            ObjectA
            | ObjectB
            | ObjectC
            | None
        ) = None,
        c_b_a: (
            ObjectC
            | ObjectB
            | ObjectA
            | None
        ) = None,
        string2testy: (
            typing.Mapping[
                str,
                Tesstee
            ]
            | None
        ) = None,
        string2string2testy: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    Tesstee
                ]
            ]
            | None
        ) = None,
        string2a_b_c: (
            typing.Mapping[
                str,
                ObjectA
                | ObjectB
                | ObjectC
            ]
            | None
        ) = None,
        string2c_b_a: (
            typing.Mapping[
                str,
                ObjectC
                | ObjectB
                | ObjectA
            ]
            | None
        ) = None,
        string2string2a_b_c: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    ObjectA
                    | ObjectB
                    | ObjectC
                ]
            ]
            | None
        ) = None,
        string2string2c_b_a: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    ObjectC
                    | ObjectB
                    | ObjectA
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
        ) = None,
        array_a: (
            ArrayA
            | None
        ) = None,
        null_value: (
            sob.Null
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
            Tesstee
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
                Tesstee
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
            ObjectA
            | None
        ) = a
        self.b: (
            ObjectB
            | None
        ) = b
        self.c: (
            ObjectC
            | None
        ) = c
        self.a_b_c: (
            ObjectA
            | ObjectB
            | ObjectC
            | None
        ) = a_b_c
        self.c_b_a: (
            ObjectC
            | ObjectB
            | ObjectA
            | None
        ) = c_b_a
        self.string2testy: (
            typing.Mapping[
                str,
                Tesstee
            ]
            | None
        ) = string2testy
        self.string2string2testy: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    Tesstee
                ]
            ]
            | None
        ) = string2string2testy
        self.string2a_b_c: (
            typing.Mapping[
                str,
                ObjectA
                | ObjectB
                | ObjectC
            ]
            | None
        ) = string2a_b_c
        self.string2c_b_a: (
            typing.Mapping[
                str,
                ObjectC
                | ObjectB
                | ObjectA
            ]
            | None
        ) = string2c_b_a
        self.string2string2a_b_c: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    ObjectA
                    | ObjectB
                    | ObjectC
                ]
            ]
            | None
        ) = string2string2a_b_c
        self.string2string2c_b_a: (
            typing.Mapping[
                str,
                typing.Mapping[
                    str,
                    ObjectC
                    | ObjectB
                    | ObjectA
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
        self.array_a: (
            ArrayA
            | None
        ) = array_a
        self.null_value: (
            sob.Null
            | None
        ) = null_value
        super().__init__(_data)


sob.get_writable_array_meta(
    ArrayA
).item_types = sob.Types([
    ObjectA
])
sob.get_writable_object_meta(
    ObjectA
).properties = sob.Properties([
    ('is_a_class', sob.BooleanProperty()),
    ('boolean', sob.BooleanProperty()),
    ('string', sob.StringProperty()),
    (
        'alpha',
        sob.EnumeratedProperty(
            values={
                1,
                2,
                3
            }
        )
    ),
    (
        'beta',
        sob.EnumeratedProperty(
            values={
                1,
                2,
                3
            }
        )
    ),
    (
        'gamma',
        sob.EnumeratedProperty(
            values={
                1,
                2,
                3
            }
        )
    ),
    (
        'delta',
        sob.EnumeratedProperty(
            values={
                1,
                2,
                3
            }
        )
    ),
    (
        'iso8601_datetime',
        sob.DateTimeProperty(
            name="iso8601DateTime"
        )
    ),
    (
        'iso8601_date',
        sob.DateProperty(
            name="iso8601Date"
        )
    )
])
sob.get_writable_object_meta(
    ObjectB
).properties = sob.Properties([
    ('is_b_class', sob.BooleanProperty()),
    ('boolean', sob.BooleanProperty()),
    ('string', sob.StringProperty()),
    ('integer', sob.IntegerProperty()),
    (
        'alpha',
        sob.EnumeratedProperty(
            values={
                "A",
                "B",
                "C"
            }
        )
    ),
    (
        'beta',
        sob.EnumeratedProperty(
            values={
                "A",
                "B",
                "C"
            }
        )
    ),
    (
        'gamma',
        sob.EnumeratedProperty(
            values={
                "A",
                "B",
                "C"
            }
        )
    ),
    (
        'delta',
        sob.EnumeratedProperty(
            values={
                "A",
                "B",
                "C"
            }
        )
    ),
    (
        'iso8601_datetime',
        sob.DateTimeProperty(
            name="iso8601DateTime"
        )
    ),
    (
        'iso8601_date',
        sob.DateProperty(
            name="iso8601Date"
        )
    )
])
sob.get_writable_object_meta(
    ObjectC
).properties = sob.Properties([
    ('is_c_class', sob.BooleanProperty()),
    ('string', sob.StringProperty()),
    ('integer', sob.IntegerProperty()),
    (
        'alpha',
        sob.EnumeratedProperty(
            values={
                False,
                True
            }
        )
    ),
    (
        'beta',
        sob.EnumeratedProperty(
            values={
                False,
                True
            }
        )
    ),
    (
        'gamma',
        sob.EnumeratedProperty(
            values={
                False,
                True
            }
        )
    ),
    (
        'delta',
        sob.EnumeratedProperty(
            values={
                False,
                True
            }
        )
    ),
    (
        'iso8601_datetime',
        sob.DateTimeProperty(
            name="iso8601DateTime"
        )
    ),
    (
        'iso8601_date',
        sob.DateProperty(
            name="iso8601Date"
        )
    )
])
sob.get_writable_object_meta(
    Tesstee
).properties = sob.Properties([
    ('boolean', sob.BooleanProperty()),
    ('string', sob.StringProperty()),
    ('number', sob.NumberProperty()),
    ('decimal_', sob.NumberProperty()),
    ('integer', sob.IntegerProperty()),
    ('rainbow', sob.BytesProperty()),
    (
        'testy',
        sob.Property(
            types=sob.MutableTypes([
                Tesstee
            ])
        )
    ),
    (
        'boolean_array',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                bool
            ]),
            name="booleanArray"
        )
    ),
    (
        'string_array',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            name="stringArray"
        )
    ),
    (
        'number_array',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                sob.NumberProperty()
            ]),
            name="numberArray"
        )
    ),
    (
        'integer_array',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                sob.IntegerProperty()
            ]),
            name="integerArray"
        )
    ),
    (
        'rainbow_array',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                sob.BytesProperty()
            ]),
            name="rainbowArray"
        )
    ),
    (
        'testy_array',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Tesstee
            ]),
            name="testyArray"
        )
    ),
    (
        'string_number_boolean',
        sob.Property(
            name="stringNumberBoolean",
            types=sob.MutableTypes([
                str,
                sob.NumberProperty(),
                bool
            ])
        )
    ),
    (
        'a',
        sob.Property(
            types=sob.MutableTypes([
                ObjectA
            ])
        )
    ),
    (
        'b',
        sob.Property(
            types=sob.MutableTypes([
                ObjectB
            ])
        )
    ),
    (
        'c',
        sob.Property(
            types=sob.MutableTypes([
                ObjectC
            ])
        )
    ),
    (
        'a_b_c',
        sob.Property(
            name="ABC",
            types=sob.MutableTypes([
                ObjectA,
                ObjectB,
                ObjectC
            ])
        )
    ),
    (
        'c_b_a',
        sob.Property(
            name="CBA",
            types=sob.MutableTypes([
                ObjectC,
                ObjectB,
                ObjectA
            ])
        )
    ),
    (
        'string2testy',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Tesstee
            ])
        )
    ),
    (
        'string2string2testy',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                sob.DictionaryProperty(
                    value_types=sob.MutableTypes([
                        Tesstee
                    ])
                )
            ])
        )
    ),
    (
        'string2a_b_c',
        sob.DictionaryProperty(
            name="string2ABC",
            value_types=sob.MutableTypes([
                ObjectA,
                ObjectB,
                ObjectC
            ])
        )
    ),
    (
        'string2c_b_a',
        sob.DictionaryProperty(
            name="string2CBA",
            value_types=sob.MutableTypes([
                ObjectC,
                ObjectB,
                ObjectA
            ])
        )
    ),
    (
        'string2string2a_b_c',
        sob.DictionaryProperty(
            name="string2string2ABC",
            value_types=sob.MutableTypes([
                sob.DictionaryProperty(
                    value_types=sob.MutableTypes([
                        ObjectA,
                        ObjectB,
                        ObjectC
                    ])
                )
            ])
        )
    ),
    (
        'string2string2c_b_a',
        sob.DictionaryProperty(
            name="string2String2CBA",
            value_types=sob.MutableTypes([
                sob.DictionaryProperty(
                    value_types=sob.MutableTypes([
                        ObjectC,
                        ObjectB,
                        ObjectA
                    ])
                )
            ])
        )
    ),
    (
        'version_switch',
        sob.Property(
            name="versionSwitch",
            types=sob.MutableTypes([
                sob.IntegerProperty(
                    versions=(
                        'testy<2',
                    )
                ),
                sob.StringProperty(
                    versions=(
                        'testy>1&testy<3',
                    )
                ),
                sob.ArrayProperty(
                    item_types=sob.MutableTypes([
                        int
                    ]),
                    versions=(
                        'testy==3.0',
                    )
                )
            ])
        )
    ),
    (
        'version_1',
        sob.IntegerProperty(
            name="version1",
            versions=(
                'testy==1.0',
            )
        )
    ),
    (
        'version_2',
        sob.IntegerProperty(
            name="version2",
            versions=(
                'testy==2.0',
            )
        )
    ),
    (
        'required_integer',
        sob.IntegerProperty(
            name="requiredInteger",
            required=True
        )
    ),
    (
        'required_integer_or_string',
        sob.Property(
            name="requiredIntegerOrString",
            required=True,
            types=sob.Types([
                int,
                str
            ])
        )
    ),
    (
        'array_a',
        sob.Property(
            name="arrayA",
            types=sob.Types([
                ArrayA
            ])
        )
    ),
    (
        'null_value',
        sob.Property(
            name="nullValue",
            types=sob.MutableTypes([
                sob.Null
            ])
        )
    )
])