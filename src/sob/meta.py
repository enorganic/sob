from __future__ import annotations

import collections
import contextlib
from collections.abc import (
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Reversible,
    Sequence,
    ValuesView,
)
from copy import deepcopy
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from sob import abc, errors
from sob._types import UNDEFINED, NoneType, Undefined
from sob.types import MutableTypes
from sob.utilities import (
    get_calling_function_qualified_name,
    get_qualified_name,
    indent,
    iter_properties_values,
    represent,
)

if TYPE_CHECKING:
    from sob.abc import MarshallableTypes


def _is_dictionary(_dictionary: Any) -> bool:
    return isinstance(_dictionary, abc.Dictionary) or (
        isinstance(_dictionary, type)
        and issubclass(_dictionary, abc.Dictionary)
    )


def _is_array(_array: Any) -> bool:
    return isinstance(_array, abc.Array) or (
        isinstance(_array, type) and issubclass(_array, abc.Array)
    )


def _is_object(_object: Any) -> bool:
    return isinstance(_object, abc.Object) or (
        isinstance(_object, type) and issubclass(_object, abc.Object)
    )


def _is_model(_model: Any) -> bool:
    return _is_object(_model) or _is_array(_model) or _is_dictionary(_model)


class Meta(abc.Meta):
    """
    TODO
    """

    def __copy__(self) -> abc.Meta:
        new_instance: Meta = self.__class__()
        attribute_name: str
        value: Any
        for attribute_name in dir(self):
            if attribute_name[0] != "_":
                value = getattr(self, attribute_name)
                if not callable(value):
                    setattr(new_instance, attribute_name, value)
        return cast(abc.Meta, new_instance)

    def __deepcopy__(self, memo: dict | None = None) -> abc.Meta:
        new_instance: Meta = self.__class__()
        property_name: str
        value: Any
        for property_name, value in iter_properties_values(self):
            setattr(new_instance, property_name, deepcopy(value, memo=memo))
        return cast(abc.Meta, new_instance)

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        lines: list[str] = [f"{get_qualified_name(type(self))}("]
        property_name: str
        value: Any
        for property_name, value in iter_properties_values(self):
            if isinstance(value, type):
                value_representation = get_qualified_name(value)
            else:
                value_representation = repr(value)
            lines.append(
                f"    {property_name}={indent(value_representation)},"
            )
        # Strip the trailing comma
        lines[-1] = lines[-1][:-1]
        lines.append(")")
        return "\n".join(lines)


class Object(Meta, abc.ObjectMeta):
    """
    TODO
    """

    def __init__(
        self,
        properties: Mapping[str, abc.Property]
        | Iterable[tuple[str, abc.Property]]
        | abc.Properties
        | None = None,
    ) -> None:
        self._properties: abc.Properties | None = None
        self.properties = properties  # type: ignore

    @property
    def properties(self) -> abc.Properties | None:
        return self._properties

    @properties.setter
    def properties(
        self,
        properties_: Mapping[str, abc.Property]
        | Iterable[tuple[str, abc.Property]]
        | abc.Properties
        | None,
    ) -> None:
        if isinstance(properties_, abc.Properties):
            new_properties = properties_
        else:
            new_properties = Properties(properties_)
        self._properties = new_properties


class Dictionary(Meta, abc.DictionaryMeta):
    """
    TODO
    """

    def __init__(
        self,
        value_types: Iterable[abc.Property | type]
        | abc.Types
        | None
        | abc.Property
        | type = None,
    ) -> None:
        self._value_types: abc.Types | None = None
        self.value_types = value_types  # type: ignore

    @property  # type: ignore
    def value_types(self) -> abc.Types | None:
        return self._value_types

    @value_types.setter
    def value_types(
        self,
        value_types: Iterable[abc.Property | type]
        | abc.Types
        | None
        | abc.Property
        | type,
    ) -> None:
        if (value_types is not None) and not isinstance(
            value_types, abc.Types
        ):
            if isinstance(value_types, (type, abc.Property)):
                value_types = (value_types,)
            value_types = MutableTypes(value_types)
        self._value_types = value_types


class Array(Meta, abc.ArrayMeta):
    """
    TODO
    """

    def __init__(
        self,
        item_types: Iterable[abc.Property | type]
        | abc.Types
        | None
        | abc.Property
        | type = None,
    ):
        self._item_types: abc.Types | None = None
        self.item_types = item_types  # type: ignore

    @property  # type: ignore
    def item_types(self) -> abc.Types | None:
        return self._item_types

    @item_types.setter  # type: ignore
    def item_types(
        self,
        item_types: Iterable[abc.Property | type]
        | abc.Types
        | None
        | abc.Property
        | type,
    ) -> None:
        if (item_types is not None) and not isinstance(item_types, abc.Types):
            if isinstance(item_types, (type, abc.Property)):
                item_types = (item_types,)
            item_types = MutableTypes(item_types)
        self._item_types = item_types


class Properties(abc.Properties):
    """
    TODO
    """

    def __init__(
        self,
        items: Mapping[str, abc.Property]
        | Iterable[tuple[str, abc.Property]]
        | abc.Properties
        | None = None,
    ) -> None:
        self._dict: abc.OrderedDict[str, abc.Property] = (
            collections.OrderedDict()
        )
        if items is not None:
            self.update(items)

    def __setitem__(self, key: str, value: abc.Property) -> None:
        if not isinstance(value, abc.Property):
            raise TypeError(value)
        self._dict.__setitem__(key, value)

    def __copy__(self) -> abc.Properties:
        new_instance: abc.Properties = self.__class__(self)
        return new_instance

    def __deepcopy__(self, memo: dict | None = None) -> abc.Properties:
        key: str
        value: abc.Property
        new_instance: Properties = self.__class__(
            tuple(
                (key, deepcopy(value, memo=memo))
                for key, value in self.items()
            )
        )
        return cast(abc.Properties, new_instance)

    @staticmethod
    def _repr_item(key: str, value: Any) -> str:
        value_representation: str = (
            get_qualified_name(value)
            if isinstance(value, type)
            else repr(value)
        )
        value_representation_lines: list[str] = value_representation.split(
            "\n"
        )
        if len(value_representation_lines) > 1:
            representation = "\n".join(
                (
                    "    (",
                    f"        {key!r},",
                    f"        {value_representation_lines[0]}",
                    *(
                        f"        {line}"
                        for line in value_representation_lines[1:]
                    ),
                    "    ),",
                )
            )
        else:
            representation = f"    ({key!r}, {value_representation}),"
        return representation

    def __repr__(self) -> str:
        representation = [get_qualified_name(type(self)) + "("]
        items = tuple(self.items())
        if len(items) > 0:
            representation[0] += "["
            for key, value in items:
                representation.append(self._repr_item(key, value))
            representation[-1] = representation[-1].rstrip(",")
            representation.append("]")
        representation[-1] += ")"
        if len(representation) > 2:  # noqa: PLR2004
            return "\n".join(representation)
        return "".join(representation)

    def keys(self) -> KeysView[str]:
        return self._dict.keys()

    def values(self) -> ValuesView[abc.Property]:
        return self._dict.values()

    def items(self) -> ItemsView[str, abc.Property]:
        return self._dict.items()

    def __getitem__(self, key: str) -> abc.Property:
        return self._dict.__getitem__(key)

    def __delitem__(self, key: str) -> None:
        self._dict.__delitem__(key)

    def __iter__(self) -> Iterator[str]:
        return self._dict.__iter__()

    def __contains__(self, key: str) -> bool:
        return self._dict.__contains__(key)

    def pop(
        self, key: str, default: abc.Property | Undefined = UNDEFINED
    ) -> abc.Property:
        return (
            self._dict.pop(key)
            if isinstance(default, Undefined)
            else self._dict.pop(key, default=default)
        )

    def popitem(self, *, last: bool = True) -> tuple[str, abc.Property]:
        return self._dict.popitem(last=last)

    def clear(self) -> None:
        self._dict.clear()

    def update(
        self,
        *args: Mapping[str, abc.Property]
        | Iterable[tuple[str, abc.Property]]
        | abc.Properties,
        **kwargs: abc.Property,
    ) -> None:
        other: (
            abc.Properties
            | Mapping[str, abc.Property]
            | Iterable[tuple[str, abc.Property]]
        )
        key: str
        value: abc.Property
        items: Iterable[tuple[str, abc.Property]] = ()
        for other in args:
            if isinstance(other, (Mapping, abc.Properties)):
                if isinstance(other, (Reversible, abc.Properties)):
                    if not isinstance(other, (Mapping, abc.Properties)):
                        raise TypeError(other)
                    items = chain(items, other.items())
                else:
                    items = chain(
                        items, sorted(other.items(), key=lambda item: item[0])
                    )
            else:
                items = chain(items, other)
        for key, value in chain(
            items, sorted(kwargs.items(), key=lambda item: item[0])
        ):
            self[key] = value

    def setdefault(
        self, key: str, default: abc.Property | None = None
    ) -> abc.Property | None:
        if not isinstance(default, (NoneType, abc.Property)):
            raise TypeError(default)
        return self._dict.setdefault(key, default)

    def get(
        self, key: str, default: abc.Property | None = None
    ) -> abc.Property | None:
        return self._dict.get(key, default)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self._dict.__eq__(other)

    def __len__(self) -> int:
        return self._dict.__len__()


def read(model: type | abc.Model) -> Any:
    message: str
    if isinstance(model, abc.Model):
        return model._meta or read(type(model))  # noqa: SLF001
    if isinstance(model, type):
        if issubclass(model, abc.Model):
            return model._meta  # noqa: SLF001
        message = (
            f"{get_calling_function_qualified_name()} "
            "requires a parameter which is an instance or sub-class of "
            f"`{get_qualified_name(abc.Model)}`, not "
            f"`{get_qualified_name(model)}`"
        )
        raise TypeError(message)
    repr_model: str = repr(model)
    message = (
        "{} requires a parameter which is an instance or sub-class of "
        "`{}`, not{}".format(
            get_calling_function_qualified_name(),
            get_qualified_name(abc.Model),
            (f":\n{repr_model}" if "\n" in repr_model else f" `{repr_model}`"),
        )
    )
    raise TypeError(message)


def object_read(model: type | abc.Object) -> abc.ObjectMeta | None:
    return read(model)


def array_read(model: type | abc.Array) -> abc.ArrayMeta | None:
    return read(model)


def dictionary_read(
    model: type | abc.Dictionary,
) -> abc.DictionaryMeta | None:
    return read(model)


def writable(model: type | abc.Model) -> Any:
    """
    This function returns an instance of [sob.meta.Meta](#Meta) which can
    be safely modified. If the class or model instance inherits its metadata
    from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    if not _is_model(model):
        raise TypeError(model)
    if isinstance(model, abc.Model):
        if model._meta is None:  # noqa: SLF001
            model._meta = deepcopy(writable(type(model)))  # noqa: SLF001
    elif isinstance(model, type) and issubclass(
        model, (abc.Object, abc.Dictionary, abc.Array)
    ):
        if TYPE_CHECKING:
            assert model._meta is not None  # noqa: SLF001
        model_meta: abc.ObjectMeta | abc.DictionaryMeta | abc.ArrayMeta = (
            model._meta  # noqa: SLF001
        )
        if model_meta is None:
            # If this model doesn't have any metadata yet--create an
            # appropriate metadata instance
            model._meta = (  # noqa: SLF001
                Object()
                if issubclass(model, abc.Object)
                else Array()
                if issubclass(model, abc.Array)
                else Dictionary()
            )
        else:
            # Ensure that the metadata is not being inherited from a base
            # class by copying the metadata if it has the same ID as any
            # base class
            for base in model.__bases__:
                base_meta: abc.Meta | None = None
                with contextlib.suppress(AttributeError):
                    base_meta = cast(abc.Model, base)._meta  # noqa: SLF001
                if (base_meta is not None) and (model_meta is base_meta):
                    model._meta = deepcopy(model_meta)  # noqa: SLF001
                    break
    else:
        repr_model = represent(model)
        msg = (
            "{} requires a parameter which is an instance or sub-class of "
            "`{}`, not{}".format(
                get_calling_function_qualified_name(),
                get_qualified_name(abc.Model),
                (
                    ":\n" + repr_model
                    if "\n" in repr_model
                    else f" `{repr_model}`"
                ),
            )
        )
        raise TypeError(msg)
    return model._meta  # noqa: SLF001


def object_writable(model: type | abc.Object) -> abc.ObjectMeta:
    """
    This function returns an instance of [sob.meta.Object](#meta-Object) which
    can be safely modified. If the class or model instance inherits its
    metadata from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    return writable(model)


def array_writable(model: type | abc.Array) -> abc.ArrayMeta:
    """
    This function returns an instance of [sob.meta.Array](#meta-Array) which
    can be safely modified. If the class or model instance inherits its
    metadata from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    return writable(model)


def dictionary_writable(
    model: type | abc.Dictionary,
) -> abc.DictionaryMeta:
    """
    This function returns an instance of
    [sob.meta.Dictionary](#meta-Dictionary) which can be safely modified. If
    the class or model instance inherits its metadata from a class or base
    class, this function will create and return a duplicate of that metadata
    assigned directly to the class or instance represented by `model`.
    """
    return writable(model)


def write(model: type[abc.Model] | abc.Model, meta: abc.Meta | None) -> None:
    message: str
    if meta is not None:
        model_type: type
        if isinstance(model, abc.Model):
            model_type = type(model)
        elif isinstance(model, type) and issubclass(model, abc.Model):
            model_type = model
        else:
            repr_model = repr(model)
            message = (
                "{} requires a value for the parameter `model` which is an "
                "instance or sub-class of `{}`, not{}".format(
                    get_calling_function_qualified_name(),
                    get_qualified_name(abc.Model),
                    (
                        ":\n" + repr_model
                        if "\n" in repr_model
                        else f" `{repr_model}`"
                    ),
                )
            )
            raise TypeError(message)
        metadata_type: type = (
            Object
            if issubclass(model_type, abc.Object)
            else (
                Array
                if issubclass(model_type, abc.Array)
                else (
                    Dictionary
                    if issubclass(model_type, abc.Dictionary)
                    else Meta
                )
            )
        )
        if not isinstance(meta, metadata_type):
            message = (
                f"Metadata assigned to `{get_qualified_name(model_type)}` "
                f"must be of type `{get_qualified_name(metadata_type)}`"
            )
            raise ValueError(message)
    if TYPE_CHECKING:
        assert (meta is None) or isinstance(meta, abc.Meta)
    model._meta = meta  # noqa: SLF001


def get_pointer(model: abc.Model) -> str | None:
    return model._pointer  # noqa: SLF001


def _read_object(model: abc.Object | type) -> abc.ObjectMeta:
    metadata: abc.Meta | None = read(model)
    if not isinstance(metadata, abc.ObjectMeta):
        raise TypeError(metadata)
    return metadata


def _read_object_properties(
    model: abc.Object | type,
) -> Iterable[tuple[str, abc.Property]]:
    metadata: abc.ObjectMeta = _read_object(model)
    return (metadata.properties or collections.OrderedDict()).items()


def _read_object_property_names(
    model: abc.Object | type,
) -> Iterable[str]:
    metadata: abc.ObjectMeta = _read_object(model)
    return (metadata.properties or collections.OrderedDict()).keys()


def escape_reference_token(reference_token: str) -> str:
    return reference_token.replace("~", "~0").replace("/", "~1")


def set_pointer(model: abc.Model, pointer_: str) -> None:
    key: str
    value: Any
    model._pointer = pointer_  # noqa: SLF001
    if isinstance(model, abc.Dictionary):
        for key, value in model.items():
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                pointer(
                    value,
                    "{}/{}".format(
                        pointer_,
                        (
                            escape_reference_token(key)
                            if isinstance(key, str)
                            else str(key)
                        ),
                    ),
                )
    elif isinstance(model, abc.Object):
        property_name: str
        property_: abc.Property
        for property_name, property_ in _read_object_properties(model):
            key = property_.name or property_name
            value = getattr(model, property_name)
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                pointer(
                    value,
                    "{}/{}".format(
                        pointer_,
                        (
                            escape_reference_token(key)
                            if isinstance(key, str)
                            else str(key)
                        ),
                    ),
                )
    elif isinstance(model, abc.Array):
        index: int
        for index in range(len(model)):
            value = model[index]
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                pointer(value, f"{pointer_}/{index!s}")


def pointer(model: abc.Model, pointer_: str | None = None) -> str | None:
    """
    Get or set a model's pointer
    """
    if not isinstance(model, (abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model)
    if pointer_ is not None:
        set_pointer(model, pointer_)
    return get_pointer(model)


def _traverse_models(
    model_instance: abc.Model,
) -> Iterable[abc.Model]:
    """
    Iterate over all child model instances
    """
    if isinstance(model_instance, abc.Dictionary):
        for value in model_instance.values():
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                yield value
    elif isinstance(model_instance, abc.Object):
        property_name: str
        for property_name in _read_object_property_names(model_instance):
            value = getattr(model_instance, property_name)
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                yield value
    elif isinstance(model_instance, abc.Array):
        for value in model_instance:
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                yield value


def set_url(model_instance: abc.Model, source_url: str | None) -> None:
    if not isinstance(model_instance, (abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model_instance)
    if (source_url is not None) and not isinstance(source_url, str):
        raise TypeError(source_url)
    model_instance._url = source_url  # noqa: SLF001
    child_model: abc.Model
    for child_model in _traverse_models(model_instance):
        set_url(child_model, source_url)


def get_url(model: abc.Model) -> str | None:
    return model._url  # noqa: SLF001


def url(model: abc.Model, url_: str | None = None) -> str | None:
    if url_ is not None:
        set_url(model, url_)
    return get_url(model)


def _version_match(
    property_: abc.Property,
    specification: str,
    version_number: str | int | Sequence[int],
) -> bool:
    if property_.versions is not None:
        version_matched = False
        specification_matched = False
        for applicable_version in property_.versions:
            if applicable_version.specification == specification:
                specification_matched = True
                if applicable_version == version_number:
                    version_matched = True
                    break
        if specification_matched and (not version_matched):
            return False
    return True


def _version_properties(
    properties_: abc.Types | Iterable[abc.Property | type],
    specification: str,
    version_number: str | int | Sequence[int],
) -> tuple[abc.Property | type, ...] | None:
    changed: bool = False
    new_properties: list[abc.Property | type] = []
    property_: abc.Property | type
    for property_ in properties_:
        if isinstance(property_, abc.Property):
            if _version_match(property_, specification, version_number):
                new_property = _version_property(
                    property_, specification, version_number
                )
                if new_property is not property_:
                    changed = True
                new_properties.append(new_property)
            else:
                # Exclude this property, as it's not a match
                changed = True
        else:
            new_properties.append(property_)
    if changed:
        return tuple(new_properties)
    return None


def _version_property(  # noqa: C901
    property_: abc.Property,
    specification: str,
    version_number: str | int | Sequence[int],
) -> abc.Property:
    changed: bool = False
    if isinstance(property_, abc.ArrayProperty) and (
        property_.item_types is not None
    ):
        item_type_items = _version_properties(
            property_.item_types, specification, version_number
        )
        if item_type_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            item_types = MutableTypes(item_type_items)
            if not isinstance(item_types, abc.Types):
                raise TypeError(item_types)
            property_.item_types = item_types  # type: ignore
            changed = True
    elif isinstance(property_, abc.DictionaryProperty) and (
        property_.value_types is not None
    ):
        value_types_items = _version_properties(
            property_.value_types, specification, version_number
        )
        if value_types_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            value_types = MutableTypes(value_types_items)
            if not isinstance(value_types, abc.Types):
                raise TypeError(value_types)
            property_.value_types = value_types  # type: ignore
            changed = True
    if property_.types is not None:
        types_items = _version_properties(
            property_.types, specification, version_number
        )
        if types_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            types = MutableTypes(types_items)
            if not isinstance(types, abc.Types):
                raise TypeError(types)
            property_.types = types  # type: ignore
    return property_


def _version_object(  # noqa: C901
    data: abc.Object,
    specification: str,
    version_number: str | int | Sequence[int],
) -> None:
    instance_meta: abc.ObjectMeta = cast(abc.ObjectMeta, read(data))
    if TYPE_CHECKING:
        assert isinstance(instance_meta.properties, abc.Properties)
    if instance_meta.properties:
        class_meta = read(type(data))
        property_name: str
        property_: abc.Property
        for property_name, property_ in tuple(
            instance_meta.properties.items()
        ):
            if _version_match(property_, specification, version_number):
                new_property = _version_property(
                    property_, specification, version_number
                )
                if new_property is not property_:
                    if instance_meta is class_meta:
                        instance_meta = writable(data)
                    if TYPE_CHECKING:
                        assert isinstance(instance_meta, abc.ObjectMeta)
                        assert isinstance(
                            instance_meta.properties, abc.Properties
                        )
                    instance_meta.properties[property_name] = new_property
            else:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                if TYPE_CHECKING:
                    assert isinstance(instance_meta, abc.ObjectMeta)
                    assert isinstance(instance_meta.properties, abc.Properties)
                del instance_meta.properties[property_name]
                version_ = getattr(data, property_name)
                if version_ is not None:
                    message: str = (
                        f"{get_qualified_name(type(data))} - the property "
                        f"`{property_name}` is not applicable in "
                        f"{specification} version {version_number}:\n{data!s}"
                    )
                    raise errors.VersionError(message)
            value = getattr(data, property_name)
            if isinstance(value, abc.Model):
                version(value, specification, version_number)


def _version_dictionary(
    data: abc.Dictionary,
    specification: str,
    version_number: str | int | Sequence[int],
) -> None:
    instance_meta: abc.Meta | None = read(data)
    if TYPE_CHECKING:
        assert isinstance(instance_meta, abc.DictionaryMeta)
    class_meta = read(type(data))
    if instance_meta and instance_meta.value_types:
        new_value_types = _version_properties(
            instance_meta.value_types, specification, version_number
        )
        if new_value_types:
            if instance_meta is class_meta:
                instance_meta = writable(data)
                if TYPE_CHECKING:
                    assert isinstance(instance_meta, abc.DictionaryMeta)
            instance_meta.value_types = new_value_types  # type: ignore
    for value in data.values():
        if isinstance(value, (abc.Object, abc.Dictionary, abc.Array)):
            version(value, specification, version_number)


def _version_array(
    data: abc.Array,
    specification: str,
    version_number: str | int | Sequence[int],
) -> None:
    instance_meta = read(data)
    class_meta = read(type(data))
    if isinstance(instance_meta, abc.ArrayMeta) and instance_meta.item_types:
        new_item_types = _version_properties(
            instance_meta.item_types, specification, version_number
        )
        if new_item_types:
            if instance_meta is class_meta:
                instance_meta = writable(data)
            instance_meta.item_types = new_item_types
    for item in data:
        if isinstance(item, abc.Model):
            version(item, specification, version_number)


def version(
    data: abc.Model,
    specification: str,
    version_number: str | int | Sequence[int],
) -> None:
    """
    Recursively alters model class or instance metadata based on version number
    metadata associated with an object's properties. This allows one data model
    to represent multiple versions of a specification and dynamically change
    based on the version of a specification represented.

    Parameters:

    - data ([sob.model.Model](#Model))
    - specification (str): The specification to which the `version_number`
      argument applies.
    - version_number (str|int|[int]): A version number represented as text
      (in the form of integers separated by periods), an integer, or a
      sequence of integers.
    """
    if not (
        isinstance(version_number, (str, float))
        or (
            isinstance(version_number, Sequence)
            and isinstance(next(iter(version_number)), int)
        )
    ):
        raise TypeError(version_number)
    if not isinstance(data, abc.Model):
        raise TypeError(data)
    if isinstance(data, abc.Object):
        _version_object(data, specification, version_number)
    elif isinstance(data, abc.Dictionary):
        _version_dictionary(data, specification, version_number)
    elif isinstance(data, abc.Array):
        _version_array(data, specification, version_number)


def _copy_object_to(
    source: abc.Object,
    target: abc.Object,
) -> None:
    source_meta: abc.ObjectMeta = cast(abc.ObjectMeta, read(source))
    if (source_meta is not None) and (source_meta.properties is not None):
        for property_name in source_meta.properties:
            source_property_value = getattr(source, property_name)
            target_property_value = getattr(target, property_name)
            if target_property_value and isinstance(
                source_property_value, abc.Model
            ):
                copy_to(source_property_value, target_property_value)


def _copy_array_to(source: abc.Array, target: abc.Array) -> None:
    for index, value in enumerate(source):
        target_value = target[index]
        if target_value and isinstance(value, abc.Model):
            if not isinstance(target_value, abc.Model):
                raise TypeError(target_value)
            copy_to(value, target_value)


def _copy_dictionary_to(
    source: abc.Dictionary, target: abc.Dictionary
) -> None:
    key: str
    value: MarshallableTypes
    for key, value in source.items():
        target_value: MarshallableTypes | None = target[key]
        if (
            target_value
            and isinstance(value, abc.Model)
            and isinstance(target_value, abc.Model)
        ):
            copy_to(value, target_value)


def copy_to(source: abc.Model, target: abc.Model) -> None:  # noqa: C901
    """
    This function copies metadata from one model instance to another
    """
    # Verify both arguments are models
    if not isinstance(source, abc.Model):
        raise TypeError(source)
    if not isinstance(target, abc.Model):
        raise TypeError(target)
    # Verify both arguments are of of the same `type`
    if type(source) is not type(target):
        raise TypeError(source, target)
    # Copy the metadata
    source_meta: abc.Meta | None = read(source)
    target_meta: abc.Meta | None = read(target)
    if source_meta is not target_meta:
        write(target, source_meta)
    # ... and recursively do the same for member data
    if isinstance(source_meta, abc.ObjectMeta) and (
        source_meta.properties is not None
    ):
        if not isinstance(source, abc.Object):
            raise TypeError(source)
        if not isinstance(target, abc.Object):
            raise TypeError(target)
        _copy_object_to(source, target)
    elif isinstance(source, abc.Array):
        if not isinstance(target, abc.Array):
            raise TypeError(target)
        _copy_array_to(source, target)
    elif isinstance(source, abc.Dictionary):
        if not isinstance(target, abc.Dictionary):
            raise TypeError(target)
        _copy_dictionary_to(source, target)
