"""
This module contains abstract base classes declaring the interface for classes
defined in [`sob.model`](https://sob.enorganic.org/api/model/),
[`sob.properties`](https://sob.enorganic.org/api/properties/),
[`sob.types`](https://sob.enorganic.org/api/types/),
[`sob.meta`](https://sob.enorganic.org/api/meta/), and
[`sob.hooks`](https://sob.enorganic.org/api/hooks/).
"""

from __future__ import annotations

import decimal
from abc import ABCMeta, abstractmethod
from collections.abc import (
    Collection,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Sequence,
    ValuesView,
)
from datetime import date, datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Union,
)

from typing_extensions import Self

from sob._types import UNDEFINED, NoneType, Null, Undefined
from sob._utilities import deprecated

if TYPE_CHECKING:
    from types import TracebackType

__all__: tuple[str, ...] = (
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
    "StringProperty",
    "DateProperty",
    "DateTimeProperty",
    "BytesProperty",
    "EnumeratedProperty",
    "NumberProperty",
    "IntegerProperty",
    "BooleanProperty",
    "ArrayProperty",
    "DictionaryProperty",
    "Version",
    "MARSHALLABLE_TYPES",
    "JSON_TYPES",
    "JSONTypes",
    "MarshallableTypes",
)


def _check_methods(class_: type, methods: Iterable[str]) -> bool | None:
    mro: tuple[type, ...] = class_.__mro__
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
    """
    This class is an abstract base for
    [`sob.Types`](https://sob.enorganic.org/api/types/#sob.types.Types).
    """

    @abstractmethod
    def __init__(
        self,
        items: Iterable[type | Property] | type | Property | None = None,
    ) -> None:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[type | Property]:  # type: ignore
        pass

    @abstractmethod
    def __copy__(self) -> Types:
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict | None = None) -> Types:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __contains__(
        self,
        item: type | Property,  # type: ignore
    ) -> bool:
        pass

    @abstractmethod
    def __getitem__(self, index: int) -> type | Property:
        pass

    def __bool__(self) -> bool:
        return bool(len(self))


class MutableTypes(Types, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.MutableTypes`](https://sob.enorganic.org/api/types/#sob.types.MutableTypes).
    """

    @abstractmethod
    def __setitem__(  # type: ignore
        self, index: int, value: type | Property
    ) -> None:
        pass

    @abstractmethod
    def append(self, value: type | Property) -> None:
        pass

    @abstractmethod
    def extend(self, values: Iterable[type | Property]) -> None:
        pass

    @abstractmethod
    def __delitem__(self, index: int) -> None:  # type: ignore
        pass

    @abstractmethod
    def pop(self, index: int = -1) -> type | Property:
        pass


class Hooks(metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Hooks`](https://sob.enorganic.org/api/hooks/#sob.hooks.Hooks).
    """

    before_marshal: Callable[[Model], Any] | None
    after_marshal: Callable[[JSONTypes], Any] | None
    before_unmarshal: Callable[[MarshallableTypes], Any] | None
    after_unmarshal: Callable[[Model], Any] | None
    before_serialize: Callable[[JSONTypes], Any] | None
    after_serialize: Callable[[str], str] | None
    before_validate: Callable[[Model], Any] | None
    after_validate: Callable[[Model], None] | None

    @abstractmethod
    def __init__(
        self,
        before_marshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_marshal: Callable[[JSONTypes], JSONTypes] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        before_serialize: Callable[[JSONTypes], JSONTypes] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[Model], Model] | None = None,
        after_validate: Callable[[Model], None] | None = None,
    ) -> None:
        pass

    @abstractmethod
    def __copy__(self) -> Hooks:
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict | None = None) -> Hooks:
        pass

    @abstractmethod
    def __bool__(self) -> bool:
        pass


class ObjectHooks(Hooks, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.ObjectHooks`](https://sob.enorganic.org/api/hooks/#sob.hooks.ObjectHooks).
    """

    before_setattr: (
        Callable[
            [Object, str, MarshallableTypes], tuple[str, MarshallableTypes]
        ]
        | None
    )
    after_setattr: Callable[[Object, str, MarshallableTypes], None] | None
    before_setitem: (
        Callable[[Object, str, MarshallableTypes], tuple[str, Any]] | None
    )
    after_setitem: Callable[[Object, str, MarshallableTypes], None] | None

    @abstractmethod
    def __init__(
        self,
        before_marshal: Callable[[MarshallableTypes], Any] | None = None,
        after_marshal: Callable[[JSONTypes], Any] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], Any] | None = None,
        after_unmarshal: Callable[[MarshallableTypes], Any] | None = None,
        before_serialize: Callable[[JSONTypes], Any] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[Model], Model] | None = None,
        after_validate: Callable[[Model], None] | None = None,
        before_setattr: Callable[
            [Object, str, MarshallableTypes], tuple[str, MarshallableTypes]
        ]
        | None = None,
        after_setattr: Callable[[Object, str, MarshallableTypes], None]
        | None = None,
        before_setitem: Callable[
            [Object, str, MarshallableTypes], tuple[str, MarshallableTypes]
        ]
        | None = None,
        after_setitem: Callable[[Object, str, MarshallableTypes], None]
        | None = None,
    ) -> None:
        pass


class ArrayHooks(Hooks, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.ArrayHooks`](https://sob.enorganic.org/api/hooks/#sob.hooks.ArrayHooks).
    """

    before_setitem: (
        Callable[[Array, int, MarshallableTypes], tuple[int, Any]] | None
    )
    after_setitem: Callable[[Array, int, MarshallableTypes], None] | None
    before_append: (
        Callable[[Array, MarshallableTypes], MarshallableTypes] | None
    )
    after_append: Callable[[Array, MarshallableTypes], None] | None

    @abstractmethod
    def __init__(
        self,
        before_marshal: Callable[[MarshallableTypes], Any] | None = None,
        after_marshal: Callable[[JSONTypes], Any] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], Any] | None = None,
        after_unmarshal: Callable[[MarshallableTypes], Any] | None = None,
        before_serialize: Callable[[JSONTypes], Any] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[Model], Model] | None = None,
        after_validate: Callable[[Model], None] | None = None,
        before_setitem: Callable[
            [Array, int, MarshallableTypes], tuple[int, Any]
        ]
        | None = None,
        after_setitem: Callable[[Array, int, MarshallableTypes], None]
        | None = None,
        before_append: Callable[[Array, MarshallableTypes], Any | None]
        | None = None,
        after_append: Callable[[Array, MarshallableTypes], None] | None = None,
    ) -> None:
        pass


class DictionaryHooks(Hooks, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.DictionaryHooks`
    ](https://sob.enorganic.org/api/hooks/#sob.hooks.DictionaryHooks).
    """

    before_setitem: (
        Callable[[Dictionary, str, MarshallableTypes], tuple[str, Any]] | None
    )
    after_setitem: Callable[[Dictionary, str, MarshallableTypes], None] | None

    def __init__(
        self,
        before_marshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_marshal: Callable[[JSONTypes], JSONTypes] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        before_serialize: Callable[[JSONTypes], Any] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[Model], Model] | None = None,
        after_validate: Callable[[Model], None] | None = None,
        before_setitem: Callable[
            [Dictionary, str, MarshallableTypes], tuple[str, Any]
        ]
        | None = None,
        after_setitem: Callable[[Dictionary, str, MarshallableTypes], None]
        | None = None,
    ) -> None:
        pass


class Readable(metaclass=ABCMeta):
    """
    This is an abstract base for file-like objects which are readable, but not
    *necessarily* writable (such an which are found in the `io` module, but
    also objects such as `http.client.HTTPResponse`). Objects will be
    identified as sub-classes if they have a callable `read` method.
    """

    register: Callable[[type], None]

    @abstractmethod
    def read(self, n: int = -1) -> str | bytes:
        pass

    @abstractmethod
    def readline(self, limit: int = -1) -> str | bytes:
        pass

    @abstractmethod
    def readlines(self, hint: int = -1) -> list[str | bytes]:
        pass

    @abstractmethod
    def seek(self, offset: int, whence: int = 0) -> int:
        pass

    @abstractmethod
    def __enter__(self) -> Self:
        pass

    @abstractmethod
    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    @classmethod
    def __subclasshook__(  # type: ignore
        cls, subclass: type
    ) -> bool | None:
        if cls is Readable:
            return _check_methods(subclass, ("read",))
        return NotImplemented


class Meta(metaclass=ABCMeta):  # noqa: B024
    """
    This class is an abstract base for
    [`sob.Meta`](https://sob.enorganic.org/api/meta/#sob.meta.Meta).
    """


class ObjectMeta(Meta, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.ObjectMeta`](https://sob.enorganic.org/api/meta/#sob.meta.ObjectMeta).
    """

    @abstractmethod
    def __init__(
        self,
        properties: Mapping[str, Property]
        | Iterable[tuple[str, Property]]
        | Properties
        | None = None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def properties(self) -> Properties | None:
        pass

    @properties.setter  # type: ignore
    @abstractmethod
    def properties(
        self,
        properties_: Mapping[str, Property]
        | Iterable[tuple[str, Property]]
        | Properties
        | None,
    ) -> None:
        pass


class DictionaryMeta(Meta, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.DictionaryMeta`](https://sob.enorganic.org/api/meta/#sob.meta.DictionaryMeta).
    """

    @abstractmethod
    def __init__(
        self,
        value_types: Iterable[Property | type]
        | Types
        | None
        | Property
        | type = None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def value_types(self) -> Types | None:
        pass

    @value_types.setter  # type: ignore
    @abstractmethod
    def value_types(
        self,
        value_types: Iterable[Property | type]
        | Types
        | None
        | Property
        | type,
    ) -> None:
        pass


class ArrayMeta(Meta, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.ArrayMeta`](https://sob.enorganic.org/api/meta/#sob.meta.ArrayMeta).
    """

    @abstractmethod
    def __init__(
        self,
        item_types: Iterable[Property | type]
        | Types
        | None
        | Property
        | type = None,
    ):
        pass

    @property  # type: ignore
    @abstractmethod
    def item_types(self) -> Types | None:
        pass

    @item_types.setter  # type: ignore
    @abstractmethod
    def item_types(
        self,
        item_types: Iterable[Property | type] | Types | None | Property | type,
    ) -> None:
        pass


class Properties(Meta, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Properties`](https://sob.enorganic.org/api/meta/#sob.meta.Properties).
    """

    @abstractmethod
    def __init__(
        self,
        items: Mapping[str, Property]
        | Iterable[tuple[str, Property]]
        | Properties
        | None = None,
    ) -> None:
        pass

    @abstractmethod
    def keys(self) -> KeysView[str]:
        pass

    @abstractmethod
    def values(self) -> ValuesView[Property]:
        pass

    @abstractmethod
    def items(self) -> ItemsView[str, Property]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: Property) -> None:
        pass

    @abstractmethod
    def __copy__(self) -> Properties:
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict | None = None) -> Properties:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> Property:
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
    def pop(self, key: str, default: Undefined = UNDEFINED) -> Property:
        pass

    @abstractmethod
    def popitem(self) -> tuple[str, Property]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def update(
        self,
        *args: Mapping[str, Property]
        | Iterable[tuple[str, Property]]
        | Properties,
        **kwargs: Property,
    ) -> None:
        pass

    @abstractmethod
    def setdefault(
        self, key: str, default: Property | None = None
    ) -> Property | None:
        pass

    @abstractmethod
    def get(
        self, key: str, default: Property | None = None
    ) -> Property | None:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass


class Model(metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Model`](https://sob.enorganic.org/api/model/#sob.model.Model).
    """

    _source: str | None
    _pointer: str | None
    _url: str | None
    _class_meta: Meta | None
    _class_hooks: Hooks | None
    _instance_meta: Meta | None
    _instance_hooks: Hooks | None

    @abstractmethod
    def _init_url(
        self,
        data: Collection[MarshallableTypes]
        | dict[str, MarshallableTypes]
        | Model
        | Readable
        | None,
    ) -> None:
        pass

    @abstractmethod
    def _init_format(
        self,
        data: str
        | bytes
        | Readable
        | Mapping[str, MarshallableTypes]
        | Iterable[MarshallableTypes]
        | Model
        | None = None,
    ) -> (
        Iterable[MarshallableTypes]
        | Mapping[str, MarshallableTypes]
        | Model
        | None
    ):
        pass

    @abstractmethod
    def _init_pointer(self) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> JSONTypes:
        pass

    @abstractmethod
    def _validate(self, *, raise_errors: bool = True) -> list[str]:
        pass


class Dictionary(Model, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Dictionary`](https://sob.enorganic.org/api/model/#sob.model.Dictionary).
    """

    _class_meta: DictionaryMeta | None
    _class_hooks: DictionaryHooks | None
    _instance_meta: DictionaryMeta | None
    _instance_hooks: DictionaryHooks | None

    @abstractmethod
    def __init__(
        self,
        items: Dictionary
        | Mapping[str, MarshallableTypes]
        | Iterable[tuple[str, MarshallableTypes]]
        | Readable
        | str
        | bytes
        | None = None,
        value_types: Iterable[type | Property]
        | type
        | Property
        | Types
        | None = None,
    ) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> dict[str, JSONTypes]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: MarshallableTypes) -> None:
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
    def __eq__(self, other: object) -> bool:
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
    def popitem(self) -> tuple[str, Any]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def update(
        self,
        *args: Mapping[str, MarshallableTypes]
        | Iterable[tuple[str, MarshallableTypes]],
        **kwargs: MarshallableTypes,
    ) -> None:
        pass

    @abstractmethod
    def setdefault(self, key: str, default: MarshallableTypes = None) -> Any:
        pass

    @abstractmethod
    def get(self, key: str, default: MarshallableTypes = None) -> Any:
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

    @abstractmethod
    def __reversed__(self) -> Iterator[str]:
        pass


class Object(Model, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Object`](https://sob.enorganic.org/api/model/#sob.model.Object).
    """

    _class_meta: ObjectMeta | None
    _class_hooks: ObjectHooks | None
    _instance_hooks: ObjectHooks | None
    _instance_meta: ObjectMeta | None
    _extra: dict[str, MarshallableTypes] | None

    @abstractmethod
    def __init__(
        self,
        _data: Object
        | Dictionary
        | Mapping[str, MarshallableTypes]
        | Iterable[tuple[str, MarshallableTypes]]
        | Readable
        | str
        | bytes
        | None = None,
    ) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> dict[str, JSONTypes]:
        pass

    @abstractmethod
    def __copy__(self) -> Object:
        pass

    @abstractmethod
    def __deepcopy__(self, memo: dict | None) -> Object:
        pass

    @abstractmethod
    def __delattr__(self, key: str) -> None:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> MarshallableTypes:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[str]:  # type: ignore
        pass

    @abstractmethod
    def __ne__(self, other: object) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __setattr__(
        self, property_name: str, value: MarshallableTypes
    ) -> None:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: MarshallableTypes) -> None:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def _get_property_validation_error_messages(
        self,
        property_name_: str,
        property_: Property,
        value: MarshallableTypes,
    ) -> Iterable[str]:
        pass


class Array(Model, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Array`](https://sob.enorganic.org/api/model/#sob.model.Array).
    """

    _class_meta: ArrayMeta | None
    _class_hooks: ArrayHooks | None
    _instance_hooks: ArrayHooks | None
    _instance_meta: ArrayMeta | None

    @abstractmethod
    def __init__(
        self,
        items: Array
        | Iterable[MarshallableTypes]
        | str
        | bytes
        | Readable
        | None = None,
        item_types: Iterable[type | Property]
        | type
        | Property
        | Types
        | None = None,
    ) -> None:
        pass

    @abstractmethod
    def _marshal(self) -> Sequence[JSONTypes]:
        pass

    @abstractmethod
    def __getitem__(self, index: int) -> Any:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        pass

    @abstractmethod
    def __contains__(self, value: MarshallableTypes) -> bool:
        pass

    @abstractmethod
    def __reversed__(self) -> Array:
        pass

    @abstractmethod
    def index(
        self,
        value: MarshallableTypes,
        start: int = 0,
        stop: int | None = None,
    ) -> int:
        pass

    @abstractmethod
    def count(self, value: MarshallableTypes) -> int:
        pass

    @abstractmethod
    def __setitem__(self, index: int, value: MarshallableTypes) -> None:
        pass

    @abstractmethod
    def __delitem__(self, index: int) -> None:
        pass

    @abstractmethod
    def insert(self, index: int, value: MarshallableTypes) -> None:
        pass

    @abstractmethod
    def append(self, value: MarshallableTypes) -> None:
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
        key: Callable[[Any], Any] | None = None,
        *,
        reverse: bool = False,
    ) -> None:
        pass

    @abstractmethod
    def extend(self, values: Iterable[MarshallableTypes]) -> None:
        pass

    @abstractmethod
    def pop(self, index: int = -1) -> Any:
        pass

    @abstractmethod
    def remove(self, value: MarshallableTypes) -> None:
        pass

    @abstractmethod
    def __iadd__(self, values: Iterable[MarshallableTypes]) -> Array:
        pass

    @abstractmethod
    def __add__(self, values: Iterable[MarshallableTypes]) -> Array:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass


class Property(metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Property`](https://sob.enorganic.org/api/properties/#sob.properties.Property).
    """

    name: str | None
    required: bool
    _types: Types | None

    @abstractmethod
    def __init__(
        self,
        types: Iterable[type | Property] | None = None,
        name: str | None = None,
        *,
        required: bool | Callable = False,
        versions: Iterable[str | Version] | None = None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def types(self) -> Types | None:
        pass

    @types.setter  # type: ignore
    @abstractmethod
    def types(
        self,
        types_or_properties: Types
        | Sequence[type | Property]
        | type
        | Property
        | None,
    ) -> None:
        pass

    @property  # type: ignore
    @abstractmethod
    def versions(self) -> Iterable[Version] | None:
        pass

    @versions.setter  # type: ignore
    @abstractmethod
    def versions(
        self,
        versions: str | Version | Iterable[str | Version] | None = None,
    ) -> None:
        pass


class StringProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.StringProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.StringProperty).
    """


String = deprecated(
    "`sob.abc.String` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.StringProperty` instead."
)(StringProperty)


class DateProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.DateProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.DateProperty).
    """

    @abstractmethod
    def date2str(self, value: date) -> str:
        pass

    @abstractmethod
    def str2date(self, value: str) -> date:
        pass


Date = deprecated(
    "`sob.abc.Date` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.DateProperty` instead."
)(DateProperty)


class DateTimeProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.DateTimeProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.DateTimeProperty).
    """

    @abstractmethod
    def datetime2str(self, value: datetime) -> str:
        pass

    @abstractmethod
    def str2datetime(self, value: str) -> datetime:
        pass


DateTime = deprecated(
    "`sob.abc.DateTime` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.DateTimeProperty` instead."
)(DateTimeProperty)


class BytesProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.BytesProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.BytesProperty).
    """


Bytes = deprecated(
    "`sob.abc.Bytes` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.BytesProperty` instead."
)(BytesProperty)


class EnumeratedProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.EnumeratedProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.EnumeratedProperty).
    """

    @property  # type: ignore
    def values(self) -> set[Any] | None:
        pass

    @values.setter
    def values(self, values: Iterable[MarshallableTypes] | None) -> None:
        pass


Enumerated = deprecated(
    "`sob.abc.Enumerated` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.EnumeratedProperty` instead."
)(EnumeratedProperty)


class NumberProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.NumberProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.NumberProperty).
    """


Number = deprecated(
    "`sob.abc.Number` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.NumberProperty` instead."
)(NumberProperty)


class IntegerProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.IntegerProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.IntegerProperty).
    """


Integer = deprecated(
    "`sob.abc.Integer` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.IntegerProperty` instead."
)(IntegerProperty)


class BooleanProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.BooleanProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.BooleanProperty).
    """


Boolean = deprecated(
    "`sob.abc.Boolean` is deprecated, and will be removed in sob 3. "
    "Please use `sob.abc.BooleanProperty` instead."
)(BooleanProperty)


class ArrayProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.ArrayProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.ArrayProperty).
    """

    @property  # type: ignore
    @abstractmethod
    def item_types(self) -> Types | None:
        pass

    @item_types.setter  # type: ignore
    @abstractmethod
    def item_types(
        self,
        item_types: type | Property | Sequence[type | Property] | Types | None,
    ) -> None:
        pass


class DictionaryProperty(Property, metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.DictionaryProperty`
    ](https://sob.enorganic.org/api/properties/#sob.properties.DictionaryProperty).
    """

    @property  # type: ignore
    @abstractmethod
    def value_types(self) -> Types | None:
        pass

    @value_types.setter  # type: ignore
    @abstractmethod
    def value_types(
        self, value_types: Sequence[type | Property] | Types | None
    ) -> None:
        pass


class Version(metaclass=ABCMeta):
    """
    This class is an abstract base for
    [`sob.Version`
    ](https://sob.enorganic.org/api/properties/#sob.properties.Version).
    """

    specification: str | None
    equals: Sequence[str | float | int | Decimal] | None
    not_equals: Sequence[str | float | int | Decimal] | None
    less_than: Sequence[str | float | int | Decimal] | None
    less_than_or_equal_to: Sequence[str | float | int | Decimal] | None
    greater_than: Sequence[str | float | int | Decimal] | None
    greater_than_or_equal_to: Sequence[str | float | int | Decimal] | None

    @abstractmethod
    def __init__(
        self,
        version_number: str | None = None,
        specification: str | None = None,
        equals: Sequence[str | float | int | Decimal] | None = None,
        not_equals: Sequence[str | float | int | Decimal] | None = None,
        less_than: Sequence[str | float | int | Decimal] | None = None,
        less_than_or_equal_to: Sequence[str | float | int | Decimal]
        | None = None,
        greater_than: Sequence[str | float | int | Decimal] | None = None,
        greater_than_or_equal_to: Sequence[str | float | int | Decimal]
        | None = None,
    ) -> None:
        pass


MARSHALLABLE_TYPES: tuple[type, ...] = (
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
JSON_TYPES: tuple[type, ...] = (
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
