# Compatibility
from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from sob.utilities.compatibility import backport, urljoin
backport()
# Standard library imports
import re  # noqa
import os  # noqa
from iso8601 import iso8601
from decimal import Decimal
from base64 import b64encode
from collections import OrderedDict
from copy import deepcopy
# `sob` package imports
from sob import model, properties, meta, test, utilities
from sob.request import MultipartRequest, Part

try:
    import typing
except ImportError as e:
    typing = None


class A(model.Object):

    def __init__(
        self,
        _=None,  # type: Optional[str]
        is_a_class=None,  # type: Optional[bool]
        boolean=None,  # type: Optional[bool]
        string=None,  # type: Optional[str]
        alpha=None,  # type: Optional[int]
        beta=None,  # type: Optional[int]
        gamma=None,  # type: Optional[int]
        delta=None,  # type: Optional[int]
        iso8601_datetime=None,  # type: Optional[datetime]
        iso8601_date=None,  # type: Optional[date]
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
        super().__init__(_)


meta.writable(A).properties = [
    ('is_a_class', properties.Boolean()),
    ('boolean', properties.Boolean()),
    ('string', properties.String()),
    ('alpha', properties.Enumerated(values=(1, 2, 3))),
    ('beta', properties.Enumerated(values=(1, 2, 3))),
    ('gamma', properties.Enumerated(values=(1, 2, 3))),
    ('delta', properties.Enumerated(values=(1, 2, 3))),
    ('iso8601_datetime', properties.DateTime(name='iso8601DateTime')),
    ('iso8601_date', properties.Date(name='iso8601Date'))
]


class B(model.Object):

    def __init__(
        self,
        _=None,  # type: Optional[str]
        is_b_class=None,  # type: Optional[bool]
        boolean=None,  # type: Optional[bool]
        string=None,  # type: Optional[str]
        integer=None,  # type: Optional[int]
        alpha=None,  # type: Optional[str]
        beta=None,  # type: Optional[str]
        gamma=None,  # type: Optional[str]
        delta=None,  # type: Optional[str]
        iso8601_datetime=None,  # type: Optional[datetime]
        iso8601_date=None,  # type: Optional[date]
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


meta.writable(B).properties = [
    ('is_b_class', properties.Boolean()),
    ('boolean', properties.Boolean()),
    ('string', properties.String()),
    ('integer', properties.Integer()),
    ('alpha', properties.Enumerated(values=('A', 'B', 'C'))),
    ('beta', properties.Enumerated(values=('A', 'B', 'C'))),
    ('gamma', properties.Enumerated(values=('A', 'B', 'C'))),
    ('delta', properties.Enumerated(values=('A', 'B', 'C'))),
    ('iso8601_datetime', properties.DateTime(name='iso8601DateTime')),
    ('iso8601_date', properties.Date(name='iso8601Date'))
]


class C(model.Object):
    def __init__(
        self,
        _=None,  # type: Optional[str]
        is_c_class=None,  # type: Optional[bool]
        string=None,  # type: Optional[str]
        integer=None,  # type: Optional[int]
        alpha=None,  # type: Optional[bool]
        beta=None,  # type: Optional[bool]
        gamma=None,  # type: Optional[bool]
        delta=None,  # type: Optional[bool]
        iso8601_datetime=None,  # type: Optional[datetime]
        iso8601_date=None,  # type: Optional[date]
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


meta.writable(C).properties = [
    ('is_c_class', properties.Boolean()),
    ('string', properties.String()),
    ('integer', properties.Integer()),
    ('alpha', properties.Enumerated(values=(True, False))),
    ('beta', properties.Enumerated(values=(True, False))),
    ('gamma', properties.Enumerated(values=(True, False))),
    ('delta', properties.Enumerated(values=(True, False))),
    ('iso8601_datetime', properties.DateTime(name='iso8601DateTime')),
    ('iso8601_date', properties.Date(name='iso8601Date'))
]


class Tesstee(model.Object):

    def __init__(
        self,
        _=None,  # type: Optional[str, dict, typing.IO]
        boolean=None,  # type: Optional[bool]
        string=None,  # type: Optional[str]
        number=None,  # type: Optional[typing.Number]
        decimal=None,  # type: Optional[typing.Number]
        integer=None,  # type: Optional[int]
        rainbow=None,  # type: Optional[bytes]
        a=None,  # type: Optional[A]
        b=None,  # type: Optional[B]
        c=None,  # type: Optional[C]
        testy=None,  # type: Optional[Tesstee]
        boolean_array=None,  # type: Optional[Sequence[bool]]
        string_array=None,  # type: Optional[Sequence[str]]
        number_array=None,  # type: Optional[Sequence[typing.Number]]
        integer_array=None,  # type: Optional[Sequence[int]]
        rainbow_array=None,  # type: Optional[Sequence[bytes]]
        testy_array=None,  # type: Optional[Sequence[Tesstee]]
        string_number_boolean=None,  # type: Optional[Union[str, typing.Number, bool]]
        a_b_c=None,  # type: Optional[Union[A, B, C]]
        c_b_a=None,  # type: Optional[Union[C, B, A]]
        string2testy=None,  # type: Optional[typing.Dict[str, Tesstee]]
        string2string2testy=None,  # type: Optional[typing.Dict[str, typing.Dict[str, Tesstee]]]
        string2a_b_c=None,  # type: Optional[typing.Dict[str, Union[A, B, C]]]
        string2c_b_a=None,  # type: Optional[typing.Dict[str, Union[C, B, A]]]
        string2string2a_b_c=None,  # type: Optional[typing.Dict[str, typing.Dict[str, Union[A, B, C]]]]
        string2string2c_b_a=None,  # type: Optional[typing.Dict[str, typing.Dict[str, Union[C, B, A]]]]
        version_switch=None,  # type: Optional[Union[int|str|typing.Sequence[int]]]
        version_1=None,  # type: Optional[Union[int]]
        version_2=None,  # type: Optional[Union[int]]
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
        super().__init__(_)


meta.writable(Tesstee).properties = {
    'boolean': properties.Boolean(),
    'string': properties.String(),
    'number': properties.Number(),
    'decimal': properties.Number(),
    'integer': properties.Integer(),
    'rainbow': properties.Bytes(),
    'testy': properties.Property(types=(Tesstee,)),
    'boolean_array': properties.Array(
        item_types=(bool,),
        name='booleanArray'
    ),
    'string_array': properties.Array(
        item_types=(str,),
        name='stringArray'
    ),
    'number_array': properties.Array(
        item_types=(properties.Number(),),
        name='numberArray'
    ),
    'integer_array': properties.Array(
        item_types=(properties.Integer(),),
        name='integerArray'
    ),
    'rainbow_array': properties.Array(
        item_types=(properties.Bytes(),),
        name='rainbowArray'
    ),
    'testy_array': properties.Array(
        item_types=(Tesstee,),
        name='testyArray'
    ),
    'string_number_boolean': properties.Property(
        types=(str, properties.Number(), bool),
        name='stringNumberBoolean'
    ),
    'a': properties.Property(
        types=(A,),
    ),
    'b': properties.Property(
        types=(B,),
    ),
    'c': properties.Property(
        types=(C,),
    ),
    'a_b_c': properties.Property(
        types=(A, B, C),
        name='ABC'
    ),
    'c_b_a': properties.Property(
        types=(C, B, A),
        name='CBA'
    ),
    'string2testy': properties.Dictionary(
        value_types=(Tesstee,)
    ),
    'string2string2testy': properties.Dictionary(
        value_types=(
            properties.Dictionary(
                value_types=(Tesstee,)
            ),
        )
    ),
    'string2a_b_c': properties.Dictionary(
        value_types=(A, B, C),
        name='string2ABC'
    ),
    'string2c_b_a': properties.Dictionary(
        value_types=(C, B, A),
        name='string2CBA'
    ),
    'string2string2a_b_c': properties.Dictionary(
        value_types=(
            properties.Dictionary(
                value_types=(A, B, C),
            ),
        ),
        name='string2string2ABC'
    ),
    'string2string2c_b_a': properties.Dictionary(
        value_types=(
            properties.Dictionary(
                value_types=(C, B, A),
            ),
        ),
        name='string2String2CBA'
    ),
    'version_switch': properties.Property(
        types=(
            properties.Integer(
                versions=('testy<2',)
            ),
            properties.String(
                versions=('testy>1&testy<3',)
            ),
            properties.Array(
                item_types=(int,),
                versions=('testy==3.0',)
            ),
        ),
        name='versionSwitch'
    ),
    'version_1': properties.Integer(
        versions=('testy==1.0',),
        name='version1'
    ),
    'version_2':properties.Integer(
        versions=('testy==2.0',),
        name='version2'
    ),
}

with open(os.path.join(os.path.dirname(__file__), 'data', 'rainbow.png'), mode='rb') as f:
    _rainbow = f.read()

a = A(
    is_a_class=True,
    boolean=True,
    string='a string',
    alpha=1,
    beta=2,
    gamma=3,
    delta=1,
    iso8601_datetime=iso8601.parse_date('2016-03-28T23:33:41.3116627-0500'),
    iso8601_date=iso8601.parse_date('2016-03-28')
)

b = B(
    is_b_class=True,
    boolean=False,
    string='b string',
    integer=666,
    alpha='A',
    beta='B',
    gamma='B',
    delta='C',
    iso8601_datetime=iso8601.parse_date('2016-03-28T23:33:41.3116627-0500'),
    iso8601_date=iso8601.parse_date('2016-03-28')
)

c = C(
    is_c_class=True,
    string='c string',
    integer=3124,
    alpha=True,
    beta=False,
    gamma=True,
    delta=False,
    iso8601_datetime=iso8601.parse_date('2001-10-26T21:32:52+02:00'),
    iso8601_date=iso8601.parse_date('2001-10-26')
)

testy = Tesstee(
    boolean=True,
    string='stringy',
    number=1.0,
    decimal=Decimal('9.99'),
    integer=1,
    rainbow=_rainbow,
    a=a,
    b=b,
    c=c,
    testy=None,
    boolean_array=(True, False, True, False),
    string_array=tuple('ABCDEFG'),
    number_array=(1**n/3 for n in range(10)),
    integer_array=(1**n for n in range(10)),
    rainbow_array=(_rainbow for n in range(10)),
    testy_array=None,
    string_number_boolean=True,
    a_b_c=deepcopy(b),
    c_b_a=deepcopy(c),
    string2testy={},
    string2string2testy=OrderedDict([
        ('A', {}),
        ('B', OrderedDict()),
        ('C', {}),
    ]),
    string2a_b_c={},
    string2c_b_a={},
    string2string2a_b_c={
        'one': {},
        'two': {},
        'three': {}
    },
    string2string2c_b_a={
        'one': {},
        'two': {},
        'three': {}
    },
)
testy_deep_copy = deepcopy(testy)

testy.testy = deepcopy(testy)

testy.testy_array = [deepcopy(testy_deep_copy) for i in range(10)]

testy.string2testy['A'] = deepcopy(testy_deep_copy)
testy.string2testy['B'] = deepcopy(testy_deep_copy)
testy.string2testy['C'] = deepcopy(testy_deep_copy)

testy.string2string2testy['A']['A'] = deepcopy(testy_deep_copy)
testy.string2string2testy['A']['B'] = deepcopy(testy_deep_copy)
testy.string2string2testy['A']['C'] = deepcopy(testy_deep_copy)
testy.string2string2testy['B']['A'] = deepcopy(testy_deep_copy)
testy.string2string2testy['B']['B'] = deepcopy(testy_deep_copy)
testy.string2string2testy['B']['C'] = deepcopy(testy_deep_copy)
testy.string2string2testy['C']['A'] = deepcopy(testy_deep_copy)
testy.string2string2testy['C']['B'] = deepcopy(testy_deep_copy)
testy.string2string2testy['C']['C'] = deepcopy(testy_deep_copy)

testy.string2a_b_c['B'] = deepcopy(testy_deep_copy.b)
testy.string2a_b_c['A'] = deepcopy(testy_deep_copy.a)
testy.string2a_b_c['C'] = deepcopy(testy_deep_copy.c)
testy.string2c_b_a['A'] = deepcopy(testy_deep_copy.a)
testy.string2c_b_a['B'] = deepcopy(testy_deep_copy.b)
testy.string2c_b_a['C'] = deepcopy(testy_deep_copy.c)

testy.string2string2a_b_c['one']['A'] = deepcopy(testy_deep_copy.a)
testy.string2string2a_b_c['one']['B'] = deepcopy(testy_deep_copy.b)
testy.string2string2a_b_c['one']['C'] = deepcopy(testy_deep_copy.c)
testy.string2string2a_b_c['two']['A'] = deepcopy(testy_deep_copy.a)
testy.string2string2a_b_c['two']['B'] = deepcopy(testy_deep_copy.b)
testy.string2string2a_b_c['two']['C'] = deepcopy(testy_deep_copy.c)
testy.string2string2a_b_c['three']['A'] = deepcopy(testy_deep_copy.a)
testy.string2string2a_b_c['three']['B'] = deepcopy(testy_deep_copy.b)
testy.string2string2a_b_c['three']['C'] = deepcopy(testy_deep_copy.c)
testy.string2string2c_b_a['one']['A'] = deepcopy(testy_deep_copy.a)
testy.string2string2c_b_a['one']['B'] = deepcopy(testy_deep_copy.b)
testy.string2string2c_b_a['one']['C'] = deepcopy(testy_deep_copy.c)
testy.string2string2c_b_a['two']['A'] = deepcopy(testy_deep_copy.a)
testy.string2string2c_b_a['two']['B'] = deepcopy(testy_deep_copy.b)
testy.string2string2c_b_a['two']['C'] = deepcopy(testy_deep_copy.c)
testy.string2string2c_b_a['three']['A'] = deepcopy(testy_deep_copy.a)
testy.string2string2c_b_a['three']['B'] = deepcopy(testy_deep_copy.b)
testy.string2string2c_b_a['three']['C'] = deepcopy(testy_deep_copy.c)


def test_object():
    # Test deletions
    testy_deep_copy = deepcopy(testy)
    assert testy_deep_copy.string2string2c_b_a is not None
    del testy_deep_copy.string2string2c_b_a
    assert testy_deep_copy.string2string2c_b_a is None


def test_json_serialization():

    model.validate(testy)
    test.json(testy)

    path = urljoin(urljoin(str(__file__), 'data/'), 'testy.json')

    if not os.path.exists(path):

        with open(
            path,
            mode='w',
            encoding='utf-8'
        ) as file:

            file.write(model.serialize(testy, 'json'))

    with open(
        path,
        mode='r',
        encoding='utf-8'
    ) as file:

        serialized_testy = model.serialize(testy, 'json').strip()
        file_testy = file.read().strip()

        if serialized_testy != file_testy:
            print(serialized_testy)

        assert serialized_testy == file_testy

    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'rainbow.png'
        ),
        mode='rb'
    ) as file:

        rainbow_bytes = file.read()

        assert testy.rainbow == rainbow_bytes
        assert model.marshal(testy)['rainbow'] == str(b64encode(rainbow_bytes), 'ascii')

    test.json(testy)


def test_json_deserialization():

    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'testy.json'
        ),
        mode='r',
        encoding='utf-8'
    ) as f:

        assert Tesstee(f) == testy
        error = None
        try:
            Tesstee('[]')
        except TypeError as e:
            error = e
        assert isinstance(error, TypeError)


def test_validation():
    pass


def test_version():

    testy1 = deepcopy(testy)
    testy2 = deepcopy(testy)
    testy3 = deepcopy(testy)

    meta.version(
        testy1,
        'testy',
        1
    )
    
    testy1.version_1 = 99
    error = None
    try:
        testy1.version_2 = 99
    except KeyError as e:
        error = e
    assert isinstance(error, KeyError)
    meta.version(
        testy2,
        'testy',
        2
    )
    testy2.version_2 = 99
    error = None
    try:
        testy2.version_1 = 99
    except KeyError as e:
        error = e
    assert isinstance(error, KeyError)
    meta.version(
        testy3,
        'testy',
        3
    )
    testy1.version_switch = 99
    error = None
    try:
        testy1.version_switch = '99'
    except TypeError as e:
        error = e
    assert isinstance(error, TypeError)
    error = None
    try:
        testy1.version_switch = (9, 9)
    except TypeError as e:
        error = e
    assert isinstance(error, TypeError)
    testy2.version_switch = '99'
    error = None
    try:
        testy2.version_switch = 99
    except TypeError as e:
        error = e
    assert isinstance(error, TypeError)
    error = None
    try:
        testy2.version_switch = (9, 9)
    except TypeError as e:
        error = e
    assert isinstance(error, TypeError)
    testy3.version_switch = (9, 9)
    error = None
    try:
        testy3.version_switch = 99
    except TypeError as e:
        error = e
    assert isinstance(error, TypeError)
    error = None
    try:
        testy3.version_switch = '99'
    except TypeError as e:
        error = e
    assert isinstance(error, TypeError)


def test_request():
    # type: (...) -> None
    """
    This will test `sob.requests`, 
    """

    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'rainbow.png'
        ),
        mode='rb'
    ) as rainbow_file:

        rainbow_bytes = rainbow_file.read()

        multi_part_json_request = MultipartRequest(
            url='http://localhost',
            headers={
                'Content-Type': 'multipart/form-data'
            },
            data=testy,
            parts=[
                Part(
                    headers={
                        'Content-Disposition':
                        'form-data; name="rainbow"; filename="rainbow.png"'
                    },
                    data=rainbow_bytes
                )
            ]
        )
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'multi_part_json_request'
        )
        if os.path.exists(path):
            with open(path, 'rb') as multi_part_request_file:
                stored_bytes = bytes(multi_part_request_file.read())
                multi_part_request_bytes = bytes(multi_part_json_request)
                stored_boundary = re.search(
                    b'\\bboundary=([a-zA-Z0-9]+)',
                    stored_bytes
                ).groups()[0]
                # We have to swap out the boundary prior to comparison because
                # the boundary is a random string, and
                # will be different every time.
                boundary = bytes(multi_part_json_request.boundary)
                stored_bytes = stored_bytes.replace(stored_boundary, boundary)
                assert stored_bytes == multi_part_request_bytes
        else:
            with open(path, 'wb') as multi_part_request_file:
                assert multi_part_request_file.write(
                    bytes(multi_part_json_request)
                )


def test_utilities():
    assert utilities.calling_function_qualified_name() == (
        'test_utilities'
        if __name__ == '__main__' else
        'test_sob.test_utilities'
    )

    class TestCallingFunctionQualifiedNameA(object):

        __module__ = 'sob.test'

        def __init__(self):
            if hasattr(type(self), '__qualname__'):
                assert utilities.calling_function_qualified_name() == (
                    'sob.test.test_utilities.'
                    'TestCallingFunctionQualifiedNameA.__init__'
                )
            else:
                assert utilities.calling_function_qualified_name() == (
                    'sob.test.TestCallingFunctionQualifiedNameA.__init__'
                )

    TestCallingFunctionQualifiedNameA()

    class TestCallingFunctionQualifiedNameB(object):

        def __init__(self):
            if hasattr(type(self), '__qualname__'):
                assert utilities.calling_function_qualified_name() == (
                    'test_utilities.TestCallingFunctionQualifiedNameB.__init__'
                    if __name__ == '__main__' else
                    'test_sob.test_utilities.'
                    'TestCallingFunctionQualifiedNameB.__init__'
                )
            else:
                assert utilities.calling_function_qualified_name() == (
                    'TestCallingFunctionQualifiedNameB.__init__'
                    if __name__ == '__main__' else
                    'test_sob.TestCallingFunctionQualifiedNameB.__init__'
                )

    TestCallingFunctionQualifiedNameB()

    class TestCallingFunctionQualifiedNameC(object):

        class TestCallingFunctionQualifiedNameD(object):

            def __init__(self):
                if hasattr(type(self), '__qualname__'):
                    assert utilities.calling_function_qualified_name() == (
                        (
                            ''
                            if __name__ == '__main__' else
                            'test_sob.'
                        ) +
                        'test_utilities.TestCallingFunctionQualifiedNameC.' +
                        'TestCallingFunctionQualifiedNameD.__init__'
                    )
                else:
                    assert utilities.calling_function_qualified_name() == (
                        (
                            ''
                            if __name__ == '__main__' else
                            'test_sob.'
                        ) +
                        'TestCallingFunctionQualifiedNameD.__init__'
                    )

    TestCallingFunctionQualifiedNameC.TestCallingFunctionQualifiedNameD()

    if hasattr(
        getattr(
            TestCallingFunctionQualifiedNameC,
            'TestCallingFunctionQualifiedNameD'
        ),
        '__qualname__'
    ):

        assert utilities.qualified_name(
            getattr(
                TestCallingFunctionQualifiedNameC(),
                'TestCallingFunctionQualifiedNameD'
            )
        ) == (
            (
                ''
                if __name__ == '__main__' else
                'test_sob.'
            ) +
            'test_utilities.TestCallingFunctionQualifiedNameC.'
            'TestCallingFunctionQualifiedNameD'
        )
    else:
        assert utilities.qualified_name(
            getattr(
                TestCallingFunctionQualifiedNameC(),
                'TestCallingFunctionQualifiedNameD'
            )
        ) == (
            (
                ''
                if __name__ == '__main__' else
                'test_sob.'
            ) +
            'TestCallingFunctionQualifiedNameD'
        )
    assert (
        utilities.qualified_name(MultipartRequest) ==
        'sob.request.MultipartRequest'
    )


if __name__ == '__main__':
    test_json_serialization()
    test_json_deserialization()
    test_version()
    test_validation()
    test_request()
    test_utilities()
