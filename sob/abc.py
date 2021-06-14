import collections
import decimal
from abc import ABCMeta, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from inspect import Traceback
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    IO,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    ValuesView,
)

import typing

from .utilities.types import NoneType, Null, UNDEFINED, Undefined


__all__: List[str] = [
    "OrderedDict",
    "Types",
    "MutableTypes",
    "Hooks",
    "ObjectHooks",
    "ArrayHooks",
    "DictionaryHooks",
    "Readable",
    "Meta",
    "ObjectMeta",
    "DictionaryMeta",
    "ArrayMeta",
    "Properties",
    "Model",
    "Dictionary",
    "Object",
    "Array",
    "Property",
    "String",
    "Date",
    "DateTime",
    "Bytes",
    "Enumerated",
    "Number",
    "Integer",
    "Boolean",
    "ArrayProperty",
    "DictionaryProperty",
    "Version",
    "MARSHALLABLE_TYPES",
    "JSON_TYPES",
    "JSONTypes",
    "MarshallableTypes",
]

if typing.TYPE_CHECKING:
    OrderedDict = collections.OrderedDict
else:
    OrderedDict = typing.Dict


def _check_methods(class_: type, methods: Iterable[str]) -> Optional[bool]:
    mro: Tuple[type, ...] = class_.__mro__
    method: str
    base_class: type
    for method in methods:
        for base_class in mro:
            if method in base_class.__dict__:
                if base_class.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


class Types(metaclass=ABCMeta):

    # noinspection PyUnusedLocal,PyMissingConstructor
    @abstractmethod
    def __init__(
        self,
        items: Optional[
            Union[Iterable[Union[type, "Property"]], type, "Property"]
        ] = None,
    ) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[Union[type, "Property"]]:  # type: ignore
        pass

    @abstractmethod
    def __copy__(self) -> "Types":
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict = None) -> "Types":
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __contains__(
        self, item: Union[type, "Property"]  # type: ignore
    ) -> bool:
        pass

    def __getitem__(self, index: int) -> Union[type, "Property"]:
        pass


class MutableTypes(Types, metaclass=ABCMeta):
    """
    TODO
    """

    @abstractmethod
    def __setitem__(  # type: ignore
        self, index: int, value: Union[type, "Property"]
    ) -> None:
        pass

    @abstractmethod
    def append(self, value: Union[type, "Property"]) -> None:
        pass

    @abstractmethod
    def extend(self, values: Iterable[Union[type, "Property"]]) -> None:
        pass

    @abstractmethod
    def __delitem__(self, index: int) -> None:  # type: ignore
        pass

    @abstractmethod
    def pop(self, index: int = -1) -> Union[type, "Property"]:
        pass


class Hooks(metaclass=ABCMeta):
    """
    TODO
    """

    before_marshal: Optional[Callable[["Model"], Any]]
    after_marshal: Optional[Callable[["JSONTypes"], Any]]
    before_unmarshal: Optional[Callable[["MarshallableTypes"], Any]]
    after_unmarshal: Optional[Callable[["Model"], Any]]
    before_serialize: Optional[Callable[["JSONTypes"], Any]]
    after_serialize: Optional[Callable[[str], str]]
    before_validate: Optional[Callable[["Model"], Any]]
    after_validate: Optional[Callable[["Model"], None]]

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(  # noqa
        self,
        before_marshal: Optional[
            Callable[["MarshallableTypes"], "MarshallableTypes"]
        ] = None,
        after_marshal: Optional[Callable[["JSONTypes"], "JSONTypes"]] = None,
        before_unmarshal: Optional[
            Callable[["MarshallableTypes"], "MarshallableTypes"]
        ] = None,
        after_unmarshal: Optional[
            Callable[["MarshallableTypes"], "MarshallableTypes"]
        ] = None,
        before_serialize: Optional[
            Callable[["JSONTypes"], "JSONTypes"]
        ] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[["Model"], "Model"]] = None,
        after_validate: Optional[Callable[["Model"], None]] = None,
    ) -> None:
        pass

    @abstractmethod
    def __copy__(self) -> "Hooks":
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict = None) -> "Hooks":
        pass

    @abstractmethod
    def __bool__(self) -> bool:
        pass


class ObjectHooks(Hooks, metaclass=ABCMeta):
    """
    TODO
    """

    before_setattr: Optional[
        Callable[
            ["Object", str, "MarshallableTypes"],
            Tuple[str, "MarshallableTypes"],
        ]
    ]
    after_setattr: Optional[
        Callable[["Object", str, "MarshallableTypes"], None]
    ]
    before_setitem: Optional[
        Callable[["Object", str, "MarshallableTypes"], Tuple[str, Any]]
    ]
    after_setitem: Optional[
        Callable[["Object", str, "MarshallableTypes"], None]
    ]

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(  # noqa
        self,
        before_marshal: Optional[Callable[["MarshallableTypes"], Any]] = None,
        after_marshal: Optional[Callable[["JSONTypes"], Any]] = None,
        before_unmarshal: Optional[
            Callable[["MarshallableTypes"], Any]
        ] = None,
        after_unmarshal: Optional[Callable[["MarshallableTypes"], Any]] = None,
        before_serialize: Optional[Callable[["JSONTypes"], Any]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[["Model"], "Model"]] = None,
        after_validate: Optional[Callable[["Model"], None]] = None,
        before_setattr: Optional[
            Callable[
                ["Object", str, "MarshallableTypes"],
                Tuple[str, "MarshallableTypes"],
            ]
        ] = None,
        after_setattr: Optional[
            Callable[["Object", str, "MarshallableTypes"], None]
        ] = None,
        before_setitem: Optional[
            Callable[
                ["Object", str, "MarshallableTypes"],
                Tuple[str, "MarshallableTypes"],
            ]
        ] = None,
        after_setitem: Optional[
            Callable[["Object", str, "MarshallableTypes"], None]
        ] = None,
    ) -> None:
        pass


class ArrayHooks(Hooks, metaclass=ABCMeta):
    """
    TODO
    """

    before_setitem: Optional[
        Callable[["Array", int, "MarshallableTypes"], Tuple[int, Any]]
    ]
    after_setitem: Optional[
        Callable[["Array", int, "MarshallableTypes"], None]
    ]
    before_append: Optional[
        Callable[["Array", "MarshallableTypes"], "MarshallableTypes"]
    ]
    after_append: Optional[Callable[["Array", "MarshallableTypes"], None]]

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(  # noqa
        self,
        before_marshal: Optional[Callable[["MarshallableTypes"], Any]] = None,
        after_marshal: Optional[Callable[["JSONTypes"], Any]] = None,
        before_unmarshal: Optional[
            Callable[["MarshallableTypes"], Any]
        ] = None,
        after_unmarshal: Optional[Callable[["MarshallableTypes"], Any]] = None,
        before_serialize: Optional[Callable[["JSONTypes"], Any]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[["Model"], "Model"]] = None,
        after_validate: Optional[Callable[["Model"], None]] = None,
        before_setitem: Optional[
            Callable[["Array", int, "MarshallableTypes"], Tuple[int, Any]]
        ] = None,
        after_setitem: Optional[
            Callable[["Array", int, "MarshallableTypes"], None]
        ] = None,
        before_append: Optional[
            Callable[["Array", "MarshallableTypes"], Optional[Any]]
        ] = None,
        after_append: Optional[
            Callable[["Array", "MarshallableTypes"], None]
        ] = None,
    ) -> None:
        pass


class DictionaryHooks(Hooks, metaclass=ABCMeta):
    """
    TODO
    """

    before_setitem: Optional[
        Callable[["Dictionary", str, "MarshallableTypes"], Tuple[str, Any]]
    ]
    after_setitem: Optional[
        Callable[["Dictionary", str, "MarshallableTypes"], None]
    ]

    # noinspection PyUnusedLocal
    def __init__(  # noqa
        self,
        before_marshal: Optional[
            Callable[["MarshallableTypes"], "MarshallableTypes"]
        ] = None,
        after_marshal: Optional[Callable[["JSONTypes"], "JSONTypes"]] = None,
        before_unmarshal: Optional[
            Callable[["MarshallableTypes"], "MarshallableTypes"]
        ] = None,
        after_unmarshal: Optional[
            Callable[["MarshallableTypes"], "MarshallableTypes"]
        ] = None,
        before_serialize: Optional[Callable[["JSONTypes"], Any]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[["Model"], "Model"]] = None,
        after_validate: Optional[Callable[["Model"], None]] = None,
        before_setitem: Optional[
            Callable[
                ["Dictionary", str, "MarshallableTypes"],
                Tuple[str, Any],
            ]
        ] = None,
        after_setitem: Optional[
            Callable[["Dictionary", str, "MarshallableTypes"], None]
        ] = None,
    ) -> None:
        pass


class Readable(metaclass=ABCMeta):
    """
    A generic ABC for IO-like objects which are readable but not
    necessarily writable.=
    """

    register: Callable[[type], None]

    @abstractmethod
    def read(self, n: int = -1) -> Union[str, bytes]:
        pass

    @abstractmethod
    def readline(self, limit: int = -1) -> Union[str, bytes]:
        pass

    @abstractmethod
    def readlines(self, hint: int = -1) -> List[Union[str, bytes]]:
        pass

    @abstractmethod
    def seek(self, offset: int, whence: int = 0) -> int:
        pass

    @abstractmethod
    def __enter__(self) -> IO:
        pass

    @abstractmethod
    def __exit__(
        self, type_: type, value: Exception, traceback: Traceback
    ) -> None:
        pass

    @classmethod
    def __subclasshook__(cls, subclass: type) -> Optional[bool]:
        if cls is Readable:
            return _check_methods(subclass, ("read",))
        return NotImplemented


class Meta(metaclass=ABCMeta):

    pass


class ObjectMeta(Meta, metaclass=ABCMeta):
    """
    TODO
    """

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        properties: Union[
            Mapping[str, "Property"],
            Iterable[Tuple[str, "Property"]],
            "Properties",
            None,
        ] = None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def properties(self) -> Optional["Properties"]:
        pass

    @properties.setter  # type: ignore
    @abstractmethod
    def properties(
        self,
        properties_: Union[
            Mapping[str, "Property"],
            Iterable[Tuple[str, "Property"]],
            "Properties",
            None,
        ],
    ) -> None:
        pass


class DictionaryMeta(Meta, metaclass=ABCMeta):
    """
    TODO
    """

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        value_types: Union[
            Iterable[Union["Property", type]], Types, None, "Property", type
        ] = None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def value_types(self) -> Optional[Types]:
        pass

    @value_types.setter  # type: ignore
    @abstractmethod
    def value_types(
        self,
        value_types: Union[
            Iterable[Union["Property", type]], Types, None, "Property", type
        ],
    ) -> None:
        pass


class ArrayMeta(Meta, metaclass=ABCMeta):
    """
    TODO
    """

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        item_types: Union[
            Iterable[Union["Property", type]], Types, None, "Property", type
        ] = None,
    ):
        pass

    @property  # type: ignore
    @abstractmethod
    def item_types(self) -> Optional[Types]:
        pass

    @item_types.setter  # type: ignore
    @abstractmethod
    def item_types(
        self,
        item_types: Union[
            Iterable[Union["Property", type]], Types, None, "Property", type
        ],
    ) -> None:
        pass


class Properties(Meta, metaclass=ABCMeta):

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        items: Union[
            Mapping[str, "Property"],
            Iterable[Tuple[str, "Property"]],
            "Properties",
            None,
        ] = None,
    ) -> None:
        pass

    @abstractmethod
    def keys(self) -> KeysView[str]:
        pass

    @abstractmethod
    def values(self) -> ValuesView["Property"]:
        pass

    @abstractmethod
    def items(self) -> ItemsView[str, "Property"]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: "Property") -> None:
        pass

    @abstractmethod
    def __copy__(self) -> "Properties":
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict = None) -> "Properties":
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> "Property":
        pass

    @abstractmethod
    def __delitem__(self, key: str) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[str]:
        pass

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        pass

    @abstractmethod
    def pop(self, key: str, default: Undefined = UNDEFINED) -> "Property":
        pass

    @abstractmethod
    def popitem(self) -> Tuple[str, "Property"]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def update(
        self,
        *args: Union[
            Mapping[str, "Property"],
            Iterable[Tuple[str, "Property"]],
            "Properties",
        ],
        **kwargs: "Property",
    ) -> None:
        pass

    @abstractmethod
    def setdefault(
        self, key: str, default: Optional["Property"] = None
    ) -> Optional["Property"]:
        pass

    @abstractmethod
    def get(
        self, key: str, default: Optional["Property"] = None
    ) -> Optional["Property"]:
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass


class Model(metaclass=ABCMeta):

    _format: Optional[str]
    _meta: Optional[Meta]
    _hooks: Optional[Hooks]
    _pointer: Optional[str]
    _url: Optional[str]

    @abstractmethod
    def _init_url(
        self,
        data: Union[
            Collection["MarshallableTypes"],
            Dict[str, "MarshallableTypes"],
            "Model",
            Readable,
            None,
        ],
    ) -> None:
        pass

    @abstractmethod
    def _init_format(
        self,
        data: Union[
            str,
            bytes,
            Readable,
            Mapping[str, "MarshallableTypes"],
            Iterable["MarshallableTypes"],
            "Model",
            None,
        ] = None,
    ) -> Union[
        Iterable["MarshallableTypes"],
        Mapping[str, "MarshallableTypes"],
        "Model",
        None,
    ]:
        pass

    @abstractmethod
    def _init_pointer(self) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> "JSONTypes":
        pass

    @abstractmethod
    def _validate(self, raise_errors: bool = True) -> List[str]:
        pass


class Dictionary(Model, metaclass=ABCMeta):

    _meta: Optional[DictionaryMeta]

    @abstractmethod
    def __init__(
        self,
        items: Union[
            "Dictionary",
            Mapping[str, "MarshallableTypes"],
            Iterable[Tuple[str, "MarshallableTypes"]],
            Readable,
            str,
            bytes,
            None,
        ] = None,
        value_types: Union[
            Iterable[Union[type, "Property"]], type, "Property", Types, None
        ] = None,
    ) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> OrderedDict[str, "JSONTypes"]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: "MarshallableTypes") -> None:
        pass

    @abstractmethod
    def __delitem__(self, key: str) -> None:
        raise KeyError

    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        pass

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[str]:
        pass

    @abstractmethod
    def pop(self, key: str, default: Undefined = UNDEFINED) -> Any:
        pass

    @abstractmethod
    def popitem(self) -> Tuple[str, Any]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def update(
        self,
        *args: Union[
            Mapping[str, "MarshallableTypes"],
            Iterable[Tuple[str, "MarshallableTypes"]],
        ],
        **kwargs: "MarshallableTypes",
    ) -> None:
        pass

    @abstractmethod
    def setdefault(self, key: str, default: "MarshallableTypes" = None) -> Any:
        pass

    @abstractmethod
    def get(self, key: str, default: "MarshallableTypes" = None) -> Any:
        pass

    @abstractmethod
    def keys(self) -> KeysView[str]:
        pass

    @abstractmethod
    def items(self) -> ItemsView[str, Any]:
        pass

    @abstractmethod
    def values(self) -> ValuesView[Any]:
        pass


class Object(Model, metaclass=ABCMeta):
    """
    TODO
    """

    _meta: Optional[ObjectMeta]

    @abstractmethod
    def __init__(
        self,
        _data: Union[
            "Object",
            Dictionary,
            Mapping[str, "MarshallableTypes"],
            Iterable[Tuple[str, "MarshallableTypes"]],
            Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> OrderedDict[str, "JSONTypes"]:
        pass

    @abstractmethod
    def __copy__(self) -> "Object":
        pass

    @abstractmethod
    def __deepcopy__(self, memo: Optional[dict]) -> "Object":
        pass

    @abstractmethod
    def __delattr__(self, key: str) -> None:
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> None:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __iter__(self) -> Iterable[str]:  # type: ignore
        pass

    @abstractmethod
    def __ne__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __setattr__(
        self, property_name: str, value: "MarshallableTypes"
    ) -> None:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: "MarshallableTypes") -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def _get_property_validation_error_messages(
        self,
        property_name_: str,
        property_: "Property",
        value: "MarshallableTypes",
    ) -> Iterable[str]:
        pass

    def __reversed__(self) -> Iterator[str]:
        pass


class Array(Model, metaclass=ABCMeta):

    _meta: Optional[ArrayMeta]

    @abstractmethod
    def __init__(
        self,
        items: Union[
            "Array", Iterable["MarshallableTypes"], str, bytes, Readable
        ] = None,
        item_types: Union[
            Iterable[Union[type, "Property"]],
            type,
            "Property",
            Types,
            None,
        ] = None,
    ) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> Sequence["JSONTypes"]:
        pass

    @abstractmethod
    def __getitem__(self, index: int) -> Any:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        pass

    @abstractmethod
    def __contains__(self, value: "MarshallableTypes") -> bool:
        pass

    @abstractmethod
    def __reversed__(self) -> "Array":
        pass

    @abstractmethod
    def index(
        self,
        value: "MarshallableTypes",
        start: int = 0,
        stop: Optional[int] = None,
    ) -> int:
        pass

    @abstractmethod
    def count(self, value: "MarshallableTypes") -> int:
        pass

    @abstractmethod
    def __setitem__(self, index: int, value: "MarshallableTypes") -> None:
        pass

    @abstractmethod
    def __delitem__(self, index: int) -> None:
        pass

    @abstractmethod
    def insert(self, index: int, value: "MarshallableTypes") -> None:
        pass

    @abstractmethod
    def append(self, value: "MarshallableTypes") -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def reverse(self) -> None:
        pass

    @abstractmethod
    def sort(
        self,
        key: Optional[Callable[[Any], Any]] = None,
        reverse: bool = False,
    ) -> None:
        pass

    @abstractmethod
    def extend(self, values: Iterable["MarshallableTypes"]) -> None:
        pass

    @abstractmethod
    def pop(self, index: int = -1) -> Any:
        pass

    @abstractmethod
    def remove(self, value: "MarshallableTypes") -> None:
        pass

    @abstractmethod
    def __iadd__(self, values: Iterable["MarshallableTypes"]) -> "Array":
        pass

    @abstractmethod
    def __add__(self, values: Iterable["MarshallableTypes"]) -> "Array":
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass


class Property(metaclass=ABCMeta):
    """
    TODO
    """

    name: Optional[str]
    required: bool
    _types: Optional[Types]

    # noinspection PyShadowingNames,PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        types: Iterable[Union[type, "Property"]] = None,
        name: Optional[str] = None,
        required: Union[bool, Callable] = False,
        versions: Optional[Iterable[Union[str, "Version"]]] = None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def types(self) -> Optional[Types]:
        pass

    @types.setter  # type: ignore
    @abstractmethod
    def types(
        self,
        types_or_properties: Optional[
            Union[Types, Sequence[Union[type, "Property"]], type, "Property"]
        ],
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def versions(self) -> Optional[Iterable["Version"]]:
        pass

    @versions.setter  # type: ignore
    @abstractmethod
    def versions(
        self,
        versions: Optional[
            Union[str, "Version", Iterable[Union[str, "Version"]]]
        ] = None,
    ) -> None:
        pass


class String(Property, metaclass=ABCMeta):
    """
    TODO
    """

    pass


class Date(Property, metaclass=ABCMeta):
    """
    TODO
    """

    @abstractmethod
    def date2str(self, value: date) -> str:
        pass

    @abstractmethod
    def str2date(self, value: str) -> date:
        pass


class DateTime(Property, metaclass=ABCMeta):
    @abstractmethod
    def datetime2str(self, value: datetime) -> str:
        pass

    @abstractmethod
    def str2datetime(self, value: str) -> datetime:
        pass


class Bytes(Property, metaclass=ABCMeta):
    """
    TODO
    """

    pass


class Enumerated(Property, metaclass=ABCMeta):
    """
    TODO
    """

    @property  # type: ignore
    def values(self) -> Optional[Set[Any]]:
        pass

    @values.setter
    def values(self, values: Optional[Iterable["MarshallableTypes"]]) -> None:
        pass


class Number(Property, metaclass=ABCMeta):

    pass


class Integer(Property, metaclass=ABCMeta):

    pass


class Boolean(Property, metaclass=ABCMeta):

    pass


class ArrayProperty(Property, metaclass=ABCMeta):
    """
    TODO
    """

    @property  # type: ignore
    @abstractmethod
    def item_types(self) -> Optional[Types]:
        pass

    @item_types.setter  # type: ignore
    @abstractmethod
    def item_types(
        self,
        item_types: Union[
            type, Property, Sequence[Union[type, Property]], Types, None
        ],
    ) -> None:
        pass


class DictionaryProperty(Property, metaclass=ABCMeta):
    """
    TODO
    """

    @property  # type: ignore
    @abstractmethod
    def value_types(self) -> Optional[Types]:
        pass

    @value_types.setter  # type: ignore
    @abstractmethod
    def value_types(
        self, value_types: Union[Sequence[Union[type, Property]], Types, None]
    ) -> None:
        pass


class Version(metaclass=ABCMeta):

    specification: Optional[str]
    equals: Optional[Sequence[Union[str, float, int, Decimal]]]
    not_equals: Optional[Sequence[Union[str, float, int, Decimal]]]
    less_than: Optional[Sequence[Union[str, float, int, Decimal]]]
    less_than_or_equal_to: Optional[Sequence[Union[str, float, int, Decimal]]]
    greater_than: Optional[Sequence[Union[str, float, int, Decimal]]]
    greater_than_or_equal_to: Optional[
        Sequence[Union[str, float, int, Decimal]]
    ]

    # noinspection PyUnusedLocal
    @abstractmethod
    def __init__(
        self,
        version_number: Optional[str] = None,
        specification: Optional[str] = None,
        equals: Optional[Sequence[Union[str, float, int, Decimal]]] = None,
        not_equals: Optional[Sequence[Union[str, float, int, Decimal]]] = None,
        less_than: Optional[Sequence[Union[str, float, int, Decimal]]] = None,
        less_than_or_equal_to: Optional[
            Sequence[Union[str, float, int, Decimal]]
        ] = None,
        greater_than: Optional[
            Sequence[Union[str, float, int, Decimal]]
        ] = None,
        greater_than_or_equal_to: Optional[
            Sequence[Union[str, float, int, Decimal]]
        ] = None,
    ) -> None:
        pass


MARSHALLABLE_TYPES: Tuple[type, ...] = (
    str,
    bytes,
    bytearray,
    bool,
    Mapping,
    Collection,
    Iterator,
    Model,
    int,
    float,
    decimal.Decimal,
    date,
    datetime,
    Null,
)
JSON_TYPES: Tuple[type, ...] = (
    str,
    int,
    float,
    bool,
    Mapping,
    Sequence,
    NoneType,
)
JSONTypes = Union[
    str,
    int,
    float,
    bool,
    Mapping[str, Any],
    Sequence,
    None,
]
MarshallableTypes = Union[
    bool,
    str,
    bytes,
    Model,
    Mapping[str, Any],
    Collection,
    Iterator,
    int,
    float,
    Decimal,
    date,
    datetime,
    Null,
    None,
]
