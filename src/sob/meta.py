from __future__ import annotations

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
from sob._utilities import deprecated
from sob.properties import TYPES_PROPERTIES
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


class Meta(abc.Meta):  # pragma: no cover
    """
    This is a base class for
    [`sob.ObjectMeta`](https://sob.enorganic.org/api/types/#sob.meta.ObjectMeta),
    [`sob.ArrayMeta`](https://sob.enorganic.org/api/types/#sob.meta.ArrayMeta),
    and
    [`sob.DictionaryMeta`](https://sob.enorganic.org/api/types/#sob.meta.DictionaryMeta),
    and implements methods common to these three classes.
    """

    __module__: str = "sob"

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


class ObjectMeta(Meta, abc.ObjectMeta):
    """
    This class holds metadata for a sub-class or instance of
    [`sob.Object`](https://sob.enorganic.org/api/model/#sob.model.Object).

    Attributes:
        properties: This is a dictionary-like object mapping property names
            to a corresponding instance (or sub-class instance) of
            [`sob.Property`
            ](https://sob.enorganic.org/api/properties/#sob.properties.Property)
            for a sub-class or sub-class instance of [`sob.Object`
            ](https://sob.enorganic.org/api/properties/#sob.model.Object).
            Attempting to set values for a property which do not correspond
            to the property metadata will raise a `TypeError`. Deserializing
            data with dictionary keys not corresponding to a defined
            property will not raise an error on deserializing, but will raise
            an [`sob.ValidationError`
            ](https://sob.enorganic.org/api/errors/#sob.errors.ValidationError)
            when/if the instance is validated using
            [`sob.validate`
            ](https://sob.enorganic.org/api/model/#sob.model.validate).
    """

    __module__: str = "sob"

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


# For backward compatibility
Object = ObjectMeta


class DictionaryMeta(Meta, abc.DictionaryMeta):
    """
    This class holds metadata for a sub-class or instance of
    [`sob.Dictionary`](https://sob.enorganic.org/api/model/#sob.model.Dictionary).

    Attributes:
        value_types: This is a sequence of types and/or instances of
            [`sob.Property`
            ](https://sob.enorganic.org/api/properties/#sob.properties.Property)
            or one of its sub-classes determining the types of values
            which can be stored in a sub-class or sub-class instance of
            [`sob.Dictionary`
            ](https://sob.enorganic.org/api/model/#sob.model.Dictionary).
            Attempting to set values of a type not described by the
            dictionary value types will raise a `TypeError`.
    """

    __module__: str = "sob"

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


# For backward compatibility
Dictionary = DictionaryMeta


class ArrayMeta(Meta, abc.ArrayMeta):
    """
    This class holds metadata for a sub-class or instance of
    [`sob.Array`](https://sob.enorganic.org/api/model/#sob.model.Array).

    Attributes:
        item_types: This is a sequence of types and/or instances of
            [`sob.Property`
            ](https://sob.enorganic.org/api/properties/#sob.properties.Property)
            or one of its sub-classes determining the types of items
            which can be stored in a sub-class or sub-class instance of
            [`sob.Array`
            ](https://sob.enorganic.org/api/model/#sob.model.Array).
            Attempting to insert or append items of a type not described by the
            array item types will raise a `TypeError`.
    """

    __module__: str = "sob"

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


# For backward compatibility
Array = ArrayMeta


class Properties(abc.Properties):
    """
    Instances of this class are dictionary-like objects mapping property names
    to a corresponding instance (or sub-class instance) of
    [`sob.Property`
    ](https://sob.enorganic.org/api/properties/#sob.properties.Property).
    """

    __module__: str = "sob"

    def __init__(
        self,
        items: Mapping[str, abc.Property]
        | Iterable[tuple[str, abc.Property]]
        | abc.Properties
        | None = None,
    ) -> None:
        self._dict: dict[str, abc.Property] = {}
        if items is not None:
            self.update(items)

    def __setitem__(self, key: str, value: abc.Property) -> None:
        if not isinstance(value, abc.Property):
            if value in TYPES_PROPERTIES:
                value = TYPES_PROPERTIES[value]()
            else:
                message: str = (
                    f"Cannot set `{key}={value!r}`, as properties must be "
                    "either an instance of `sob.Property`"
                    "or one of the following mapped types:\n"
                    f"{represent(TYPES_PROPERTIES)}"
                )
                raise TypeError(message)
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
            else self._dict.pop(key, default=default)  # type: ignore
        )

    def popitem(self) -> tuple[str, abc.Property]:
        return self._dict.popitem()

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


def read_model_meta(model: type | abc.Model) -> abc.Meta | None:
    """
    Read the metadata associated with a sub-class or instance of `sob.Model`,
    or return `None` if no metadata is defined.

    Please note that the returned metadata may be inherited,
    and therefore should not be modified. Use `get_writable_model_meta` to
    retrieve an instance of this metadata suitable for modification.
    """
    message: str
    if isinstance(model, abc.Model):
        return getattr(model, "_instance_meta", None) or read_model_meta(
            type(model)
        )
    if isinstance(model, type) and issubclass(model, abc.Model):
        base: type | None
        try:
            return next(
                getattr(base, "_class_meta", None)
                for base in filter(
                    lambda base: issubclass(base, abc.Model),
                    model.__mro__,
                )
            )
        except StopIteration:
            return None
    repr_model: str = represent(model)
    message = (
        "{} requires a parameter which is an instance or sub-class of "
        "`{}`, not{}".format(
            get_calling_function_qualified_name(),
            get_qualified_name(abc.Model),
            (f":\n{repr_model}" if "\n" in repr_model else f" `{repr_model}`"),
        )
    )
    raise TypeError(message)


read = deprecated(
    "`sob.meta.read` is deprecated and will be removed in "
    "sob 3. Please use `sob.read_model_meta` instead."
)(read_model_meta)


def read_object_meta(model: type | abc.Object) -> abc.ObjectMeta | None:
    """
    Read the metadata associated with a sub-class or instance of `sob.Object`,
    or return `None` if no metadata is defined.

    Please note that the returned metadata may be inherited,
    and therefore should not be modified. Use `get_writable_object_meta` to
    retrieve an instance of this metadata suitable for modification.
    """
    return read_model_meta(model)  # type: ignore


object_read = deprecated(
    "`sob.meta.object_read` is deprecated and will be removed in "
    "sob 3. Please use `sob.read_object_meta` instead."
)(read_object_meta)


def read_array_meta(model: type | abc.Array) -> abc.ArrayMeta | None:
    """
    Read the metadata associated with a sub-class or instance of `sob.Array`,
    or return `None` if no metadata is defined.

    Please note that the returned metadata may be inherited,
    and therefore should not be modified. Use `get_writable_array_meta` to
    retrieve an instance of this metadata suitable for modification.
    """
    return read_model_meta(model)  # type: ignore


array_read = deprecated(
    "`sob.meta.array_read` is deprecated and will be removed in "
    "sob 3. Please use `sob.read_array_meta` instead."
)(read_array_meta)


def read_dictionary_meta(
    model: type[abc.Dictionary] | abc.Dictionary,
) -> abc.DictionaryMeta | None:
    """
    Read metadata from a sub-class or instance of `sob.Dictionary`.

    Please note that the returned metadata may be inherited,
    and therefore should not be modified. Use `get_writable_dictionary_hooks`
    to retrieve an instance of this metadata suitable for modification.
    """
    return read_model_meta(model)  # type: ignore


dictionary_read = deprecated(
    "`sob.meta.dictionary_read` is deprecated and will be removed in "
    "sob 3. Please use `sob.read_dictionary_meta` instead."
)(read_dictionary_meta)


def get_writable_model_meta(model: type | abc.Model) -> abc.Meta:
    """
    Retrieve an instance of `sob.Meta` which is associated directly with the
    `model` class or instance, and therefore suitable for modifying.

    If `model` is an instance of an `sob.Model` sub-class, and the instance
    does not have any metadata associated, the class hooks will be
    copied to the instance and returned

    If `model` is a sub-class of `sob.Model`, but does not have any metadata
    associated, hooks will be copied from the first parent class which
    has metadata attributed, and the copy will be returned.

    If neither the `model` class or instance, nor any parent classes,
    have any metadata associated—a new instance of `sob.Meta` will be
    created, attributed to `model`, and returned.
    """
    if not _is_model(model):
        raise TypeError(model)
    if isinstance(model, abc.Model):
        if model._instance_meta is None:  # noqa: SLF001
            model._instance_meta = deepcopy(  # noqa: SLF001
                read_model_meta(type(model))
            )
        if model._instance_meta is None:  # noqa: SLF001
            model._instance_meta = (  # noqa: SLF001
                ObjectMeta()
                if isinstance(model, abc.Object)
                else ArrayMeta()
                if isinstance(model, abc.Array)
                else DictionaryMeta()
            )
        return model._instance_meta  # noqa: SLF001
    if isinstance(model, type) and issubclass(model, abc.Model):
        if model._class_meta is None:  # noqa: SLF001
            model._class_meta = deepcopy(  # noqa: SLF001
                read_model_meta(model)
            )
        if model._class_meta is None:  # noqa: SLF001
            model._class_meta = (  # noqa: SLF001
                ObjectMeta()
                if issubclass(model, abc.Object)
                else ArrayMeta()
                if issubclass(model, abc.Array)
                else DictionaryMeta()
            )
        return model._class_meta  # noqa: SLF001
    repr_model: str = represent(model)
    message: str = (
        "{} requires a parameter which is an instance or sub-class of "
        "`{}`, not{}".format(
            get_calling_function_qualified_name(),
            get_qualified_name(abc.Model),
            (":\n" + repr_model if "\n" in repr_model else f" `{repr_model}`"),
        )
    )
    raise TypeError(message)


# For backward compatibility
writable = get_writable_model_meta


def get_writable_object_meta(
    object_: type[abc.Object] | abc.Object,
) -> abc.ObjectMeta:
    """
    Retrieve an instance of `sob.ObjectMeta` which is associated directly with
    the `model` class or instance, and therefore suitable for modifying.

    If `model` is an instance of an `sob.Object` sub-class, and the instance
    does not have any metadata associated, the class metadata will be
    copied to the instance and returned.

    If `model` is a sub-class of `sob.Object`, but does not have any metadata
    associated, metadata will be copied from the first parent class which
    has metadata attributed, and the copy will be returned.

    If neither the `model` class or instance, nor any parent classes,
    have any metadata associated—a new instance of `sob.ObjectMeta` will be
    created, attributed to `model`, and returned.
    """
    return get_writable_model_meta(object_)  # type: ignore


# For backward compatibility
object_writable = get_writable_object_meta


def get_writable_array_meta(model: type | abc.Array) -> abc.ArrayMeta:
    """
    Retrieve an instance of `sob.ArrayMeta` which is associated directly with
    the `model` class or instance, and therefore suitable for modifying.

    If `model` is an instance of an `sob.Array` sub-class, and the instance
    does not have any metadata associated, the class metadata will be
    copied to the instance and returned.

    If `model` is a sub-class of `sob.Array`, but does not have any metadata
    associated, metadata will be copied from the first parent class which
    has metadata attributed, and the copy will be returned.

    If neither the `model` class or instance, nor any parent classes,
    have any metadata associated—a new instance of `sob.ArrayMeta` will be
    created, attributed to `model`, and returned.
    """
    return get_writable_model_meta(model)  # type: ignore


array_writable = deprecated(
    "`sob.meta.array_writable` is deprecated and will be removed in "
    "sob 3. Please use `sob.get_writable_array_meta` instead."
)(get_writable_array_meta)


def get_writable_dictionary_meta(
    model: type | abc.Dictionary,
) -> abc.DictionaryMeta:
    """
    Retrieve an instance of `sob.DictionaryMeta` which is associated directly
    with the `model` class or instance, and therefore suitable for writing
    metadata to.

    If `model` is an instance of an `sob.Dictionary` sub-class, and the
    instance does not have any metadata associated, the parent class metadata
    will be copied to the instance and returned.

    If `model` is a sub-class of `sob.Dictionary`, but does not have any
    metadata associated, metadata will be copied from the first parent class
    which does have metadata attributed.

    If neither the `model` class or instance, nor any parent classes,
    have any metadata associated—a new instance of `sob.DictionaryMeta` will be
    created, attributed to `model`, and returned.
    """
    return get_writable_model_meta(model)  # type: ignore


dictionary_writable = deprecated(
    "`sob.meta.dictionary_writable` is deprecated and will be removed in "
    "sob 3. Please use `sob.get_writable_dictionary_meta` instead."
)(get_writable_dictionary_meta)


def get_model_meta_type(model: type | abc.Model) -> type:
    """
    Determine the type of metadata required for the specified `model`
    class or instance.
    """
    meta_type: type | None
    if not isinstance(model, (type, abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model)
    if isinstance(model, type):
        if not issubclass(model, (abc.Object, abc.Dictionary, abc.Array)):
            raise TypeError(model)
        meta_type = (
            ObjectMeta
            if issubclass(model, abc.Object)
            else ArrayMeta
            if issubclass(model, abc.Array)
            else DictionaryMeta
        )
    else:
        meta_type = (
            ObjectMeta
            if isinstance(model, abc.Object)
            else ArrayMeta
            if isinstance(model, abc.Array)
            else DictionaryMeta
        )
    return meta_type


def write_model_meta(
    model: type[abc.Model] | abc.Model, meta: abc.Meta | None
) -> None:
    """
    Write metadata to a sub-class or instance of `sob.Model`.
    """
    if meta is not None:
        # Verify that the metadata is of the correct type
        meta_type: type[abc.Meta] = get_model_meta_type(model)
        if not isinstance(meta, meta_type):
            message: str = (
                f"Metadata assigned to `{get_qualified_name(type(model))}` "
                f"must be of type `{get_qualified_name(meta_type)}`"
            )
            raise ValueError(message)
    if isinstance(model, abc.Model):
        model._instance_meta = meta  # noqa: SLF001
    else:
        if not issubclass(model, abc.Model):
            raise TypeError(model)
        model._class_meta = meta  # noqa: SLF001


write = deprecated(
    "`sob.meta.write` is deprecated and will be removed in sob 3. "
    "Please use `sob.write_model_meta` instead."
)(write_model_meta)


def get_model_pointer(model: abc.Model) -> str | None:
    """
    Get the JSON pointer associated with this model. Please note that this
    will typically only be available for models which have been deserialized
    from JSON data, otherwise, this function will return `None` (unless
    explicitly set using `set_model_pointer` on this instance, or a parent).
    """
    return model._pointer  # noqa: SLF001


get_pointer = deprecated(
    "`sob.meta.get_pointer` is deprecated and will be removed in sob 3. "
    "Please use `sob.get_model_pointer` instead."
)(get_model_pointer)


def _read_object(model: abc.Object | type) -> abc.ObjectMeta | None:
    metadata: abc.Meta | None = read_model_meta(model)
    if (metadata is not None) and not isinstance(metadata, abc.ObjectMeta):
        raise TypeError(metadata)
    return metadata


def _read_object_properties(
    model: abc.Object | type,
) -> Iterable[tuple[str, abc.Property]] | None:
    metadata: abc.ObjectMeta | None = _read_object(model)
    if metadata is None:
        return None
    return (metadata.properties or {}).items()


def _read_object_property_names(
    model: abc.Object | type,
) -> Iterable[str] | None:
    metadata: abc.ObjectMeta | None = _read_object(model)
    if metadata is None:
        return None
    return (metadata.properties or {}).keys()


def escape_reference_token(reference_token: str) -> str:
    return reference_token.replace("~", "~0").replace("/", "~1")


def set_model_pointer(model: abc.Model, pointer_: str | None) -> None:
    """
    Set the JSON pointer associated with this model, and all models
    assigned to object properties, array items, or dictionary values
    of this model.
    """
    key: str
    value: Any
    model._pointer = pointer_  # noqa: SLF001
    if isinstance(model, abc.Dictionary):
        for key, value in model.items():
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                set_model_pointer(
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
        for property_name, property_ in _read_object_properties(model) or ():
            key = property_.name or property_name
            value = getattr(model, property_name)
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                set_model_pointer(
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
                set_model_pointer(value, f"{pointer_}/{index!s}")


set_pointer = deprecated(
    "`sob.meta.set_pointer` is deprecated and will be removed in sob 3. "
    "Please use `sob.set_model_pointer` instead."
)(set_model_pointer)


@deprecated(
    "`sob.meta.pointer` is deprecated and will be removed in sob 3. "
    "Use `sob.get_model_pointer` and `sob.set_model_pointer` "
    "instead.",
)
def pointer(model: abc.Model, pointer_: str | None = None) -> str | None:
    """
    Get or set a model's pointer
    """
    if not isinstance(model, (abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model)
    if pointer_ is not None:
        set_model_pointer(model, pointer_)
    return get_model_pointer(model)


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
        for property_name in _read_object_property_names(model_instance) or ():
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


def set_model_url(model_instance: abc.Model, source_url: str | None) -> None:
    """
    Set a source URL to be associated with this model, and all models
    assigned to object properties, array items, or dictionary values
    of this model.
    """
    if not isinstance(model_instance, (abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model_instance)
    if (source_url is not None) and not isinstance(source_url, str):
        raise TypeError(source_url)
    model_instance._url = source_url  # noqa: SLF001
    child_model: abc.Model
    for child_model in _traverse_models(model_instance):
        set_model_url(child_model, source_url)


set_url = deprecated(
    "`sob.meta.set_url` is deprecated and will be removed in sob 3. "
    "Please use `sob.set_model_url` instead."
)(set_model_url)


def get_model_url(model: abc.Model) -> str | None:
    """
    Get the source URL from which this model was deserialized.
    """
    return model._url  # noqa: SLF001


get_url = deprecated(
    "`sob.meta.get_url` is deprecated and will be removed in sob 3. "
    "Please use `sob.get_model_url` instead."
)(get_model_url)


@deprecated(
    "`sob.meta.url` is deprecated and will be removed in sob 3. "
    "Use `sob.get_model_url` and `sob.set_model_url` "
    "instead.",
)
def url(model: abc.Model, url_: str | None = None) -> str | None:
    if url_ is not None:
        set_model_url(model, url_)
    return get_model_url(model)


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
    message: str
    meta_: abc.ObjectMeta | None = read_object_meta(data)
    if meta_ is None:
        message = f"Unable to read metadata for {represent(data)}"
        raise RuntimeError(message)
    if TYPE_CHECKING:
        assert isinstance(meta_.properties, abc.Properties)
    if meta_.properties:
        class_meta = read_model_meta(type(data))
        property_name: str
        property_: abc.Property
        for property_name, property_ in tuple(meta_.properties.items()):
            if _version_match(property_, specification, version_number):
                new_property = _version_property(
                    property_, specification, version_number
                )
                if new_property is not property_:
                    if meta_ is class_meta:
                        meta_ = get_writable_object_meta(data)
                    if TYPE_CHECKING:
                        assert isinstance(meta_, abc.ObjectMeta)
                        assert isinstance(meta_.properties, abc.Properties)
                    meta_.properties[property_name] = new_property
            else:
                if meta_ is class_meta:
                    meta_ = get_writable_object_meta(data)
                if TYPE_CHECKING:
                    assert isinstance(meta_, abc.ObjectMeta)
                    assert isinstance(meta_.properties, abc.Properties)
                del meta_.properties[property_name]
                version_ = getattr(data, property_name)
                if version_ is not None:
                    message = (
                        f"{get_qualified_name(type(data))} - the property "
                        f"`{property_name}` is not applicable in "
                        f"{specification} version {version_number}:\n{data!s}"
                    )
                    raise errors.VersionError(message)
            value = getattr(data, property_name)
            if isinstance(value, abc.Model):
                version_model(value, specification, version_number)


def _version_dictionary(
    data: abc.Dictionary,
    specification: str,
    version_number: str | int | Sequence[int],
) -> None:
    instance_meta: abc.Meta | None = read_model_meta(data)
    if TYPE_CHECKING:
        assert isinstance(instance_meta, abc.DictionaryMeta)
    class_meta = read_model_meta(type(data))
    if instance_meta and instance_meta.value_types:
        new_value_types = _version_properties(
            instance_meta.value_types, specification, version_number
        )
        if new_value_types:
            if instance_meta is class_meta:
                instance_meta = get_writable_model_meta(data)
                if TYPE_CHECKING:
                    assert isinstance(instance_meta, abc.DictionaryMeta)
            instance_meta.value_types = new_value_types  # type: ignore
    for value in data.values():
        if isinstance(value, (abc.Object, abc.Dictionary, abc.Array)):
            version_model(value, specification, version_number)


def _version_array(
    data: abc.Array,
    specification: str,
    version_number: str | int | Sequence[int],
) -> None:
    instance_meta = read_model_meta(data)
    class_meta = read_model_meta(type(data))
    if isinstance(instance_meta, abc.ArrayMeta) and instance_meta.item_types:
        new_item_types = _version_properties(
            instance_meta.item_types, specification, version_number
        )
        if new_item_types:
            if instance_meta is class_meta:
                instance_meta = get_writable_array_meta(data)
            instance_meta.item_types = new_item_types  # type: ignore
    for item in data:
        if isinstance(item, abc.Model):
            version_model(item, specification, version_number)


def version_model(
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


version = deprecated(
    "`sob.meta.version` is deprecated and will be removed in "
    "sob 3. Please use `sob.version_model` instead."
)(version_model)


def _copy_object_to(
    source: abc.Object,
    target: abc.Object,
) -> None:
    source_meta: abc.ObjectMeta = cast(abc.ObjectMeta, read_model_meta(source))
    if (source_meta is not None) and (source_meta.properties is not None):
        for property_name in source_meta.properties:
            source_property_value = getattr(source, property_name)
            target_property_value = getattr(target, property_name)
            if target_property_value and isinstance(
                source_property_value, abc.Model
            ):
                _copy_model_meta_to(
                    source_property_value, target_property_value
                )


def _copy_array_to(source: abc.Array, target: abc.Array) -> None:
    for index, value in enumerate(source):
        target_value = target[index]
        if target_value and isinstance(value, abc.Model):
            if not isinstance(target_value, abc.Model):
                raise TypeError(target_value)
            _copy_model_meta_to(value, target_value)


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
            _copy_model_meta_to(value, target_value)


def _copy_model_meta_to(  # noqa: C901
    source: abc.Model, target: abc.Model
) -> None:
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
    source_meta: abc.Meta | None = read_model_meta(source)
    target_meta: abc.Meta | None = read_model_meta(target)
    if source_meta is not target_meta:
        write_model_meta(target, source_meta)
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
