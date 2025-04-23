from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

from sob import abc
from sob._utilities import deprecated
from sob.utilities import (
    get_calling_function_qualified_name,
    get_qualified_name,
    represent,
)

if TYPE_CHECKING:
    from sob.abc import JSONTypes, MarshallableTypes


class Hooks(abc.Hooks):  # pragma: no cover
    """
    Instances of this class hold functions ("hooks") to be executed
    at various points during marshalling, un-marshalling, serializing,
    de-serializing or validation.

    Please note the following context-specific definitions:

    - marshal: To convert an instance of an `sob.Model` sub-class into data
        suitable for serializing with `json.dumps`. For example, marshalling
        an instance of `sob.Dictionary`, or marshalling an instance of a
        sub-class of `sob.Object`, would result in a `dict` object.
    - unmarshal: To convert data de-serialized using `json.loads` into an
        instance of an `sob.Model` sub-class. For example, un-marshalling a
        `dict` object could return in an instance of `sob.Dictionary`
        (this would be the default if no types were specified), or could
        return an instance of one of the `sob.Model` sub-classes
        specified in the `types` parameter passed to `sob.unmarshal`.
    - serialize: To convert a marshalled object into a JSON string.
    - deserialize: To convert a JSON string into a python-native object.
    - validate: To check that the data held by a model instance is in
        compliance with that model's metadata. Because data types are
        enforced when attributes are set, validation only entails verifying
        that all required attributes are present, and that no extraneous
        attributes are present. Validation is only initiated explicitly,
        by passing a model instance to the `sob.validate` function.

    Attributes:
        before_marshal: A function called *before* marshalling a model.
            The `before_marshal` function should accept deserialized JSON
            data (pre-marshalling) as the first argument, and return the
            same type of data (or `None`) as the return value.
        after_marshal: A function to be called *after* marshalling a model.
            The `after_marshal` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_unmarshal: A function to be called *before* un-marshalling a
            model. The `before_unmarshal` function should accept an
            instance of the class to which it is associated as the only
            argument, and must return an instance of that class as the
            return value.
        after_unmarshal: A function to be called *after* un-marshalling a
            model. The `after_unmarshal` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value.
        before_serialize: A function to be called before serializing a
            model. The `before_serialize` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value. For most use cases, assigning a
            function to `after_unmarshal` and to `before_serialize` will
            produce the same result, however it is technically possible to
            unmarshal data without ever serializing it, so both hooks are
            provided.
        after_serialize: A function to be called after serializing a model.
            The `after_serialize` function should accept a JSON string as
            the only argument, and return a JSON string as the return
            value.
        before_validate: A function to be called before validating a model.
            The `before_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        after_validate: A function to be called after validating a model.
            The `after_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
    """

    __module__: str = "sob"

    def __init__(
        self,
        before_marshal: Callable[[abc.Model], abc.Model] | None = None,
        after_marshal: Callable[[JSONTypes], JSONTypes] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_unmarshal: Callable[[abc.Model], abc.Model] | None = None,
        before_serialize: Callable[[JSONTypes], JSONTypes] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[abc.Model], abc.Model] | None = None,
        after_validate: Callable[[abc.Model], None] | None = None,
    ):
        self.before_marshal = before_marshal
        self.after_marshal = after_marshal
        self.before_unmarshal = before_unmarshal
        self.after_unmarshal = after_unmarshal
        self.before_serialize = before_serialize
        self.after_serialize = after_serialize
        self.before_validate = before_validate
        self.after_validate = after_validate

    def __copy__(self) -> Hooks:
        return self.__class__(**vars(self))

    def __deepcopy__(self, memo: dict | None = None) -> Hooks:
        return self.__class__(
            **{
                key: deepcopy(value, memo=memo)
                for key, value in vars(self).items()
            }
        )

    def __bool__(self) -> bool:
        return True


class ObjectHooks(Hooks, abc.ObjectHooks):
    """
    Instances of this class hold functions ("hooks") to be executed
    at various points during marshalling, un-marshalling, serializing,
    de-serializing or validation.

    Please note the following context-specific definitions:

    - marshal: To convert an instance of an `sob.Model` sub-class into data
        suitable for serializing with `json.dumps`. For example, marshalling
        an instance of `sob.Dictionary`, or marshalling an instance of a
        sub-class of `sob.Object`, would result in a `dict` object.
    - unmarshal: To convert data de-serialized using `json.loads` into an
        instance of an `sob.Model` sub-class. For example, un-marshalling a
        `dict` object could return in an instance of `sob.Dictionary`
        (this would be the default if no types were specified), or could
        return an instance of one of the `sob.Model` sub-classes
        specified in the `types` parameter passed to `sob.unmarshal`.
    - serialize: To convert a marshalled object into a JSON string.
    - deserialize: To convert a JSON string into a python-native object.
    - validate: To check that the data held by a model instance is in
        compliance with that model's metadata. Because data types are
        enforced when attributes are set, validation only entails verifying
        that all required attributes are present, and that no extraneous
        attributes are present. Validation is only initiated explicitly,
        by passing a model instance to the `sob.validate` function.

    Attributes:
        before_marshal: A function called *before* marshalling a model.
            The `before_marshal` function should accept deserialized JSON
            data (pre-marshalling) as the first argument, and return the
            same type of data (or `None`) as the return value.
        after_marshal: A function to be called *after* marshalling a model.
            The `after_marshal` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_unmarshal: A function to be called *before* un-marshalling a
            model. The `before_unmarshal` function should accept an
            instance of the class to which it is associated as the only
            argument, and must return an instance of that class as the
            return value.
        after_unmarshal: A function to be called *after* un-marshalling a
            model. The `after_unmarshal` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value.
        before_serialize: A function to be called before serializing a
            model. The `before_serialize` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value. For most use cases, assigning a
            function to `after_unmarshal` and to `before_serialize` will
            produce the same result, however it is technically possible to
            unmarshal data without ever serializing it, so both hooks are
            provided.
        after_serialize: A function to be called after serializing a model.
            The `after_serialize` function should accept a JSON string as
            the only argument, and return a JSON string as the return
            value.
        before_validate: A function to be called before validating a model.
            The `before_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        after_validate: A function to be called after validating a model.
            The `after_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_setattr: A function to be called before setting an attribute.
            The `before_setattr` function should accept 3 positional
            arguments: an instance of the class to which it is associated,
            the attribute name, and the value to be assigned to that
            attribute. The function should return a tuple containing an
            attribute name and a value to be assigned to that attribute.
        after_setattr: A function to be called after setting an attribute.
            The `after_setattr` function should accept 3 positional
            arguments: an instance of the class to which it is associated,
            the attribute name, and the value assigned to that
            attribute. The function should return `None`.
        before_setitem: A function to be called before assigning a value
            to an object by key. The `before_setitem` function should accept 3
            positional arguments: an instance of the class to which it is
            associated, the item key, and the value to be assigned to that
            key. The function should return a tuple containing a
            key and a value to be assigned.
        after_setitem: A function to be called after assigning a value
            to an object by key. The `before_setitem` function should accept 3
            positional arguments: an instance of the class to which it is
            associated, the item key, and the value assigned to that
            key. The function should return `None`.
    """

    __module__: str = "sob"

    def __init__(
        self,
        before_marshal: Callable[[abc.Model], abc.Model] | None = None,
        after_marshal: Callable[[JSONTypes], JSONTypes] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_unmarshal: Callable[[abc.Model], abc.Model] | None = None,
        before_serialize: Callable[[JSONTypes], JSONTypes] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[abc.Model], abc.Model] | None = None,
        after_validate: Callable[[abc.Model], None] | None = None,
        before_setattr: Callable[
            [abc.Object, str, MarshallableTypes], tuple[str, MarshallableTypes]
        ]
        | None = None,
        after_setattr: Callable[[abc.Object, str, MarshallableTypes], None]
        | None = None,
        before_setitem: Callable[
            [abc.Object, str, MarshallableTypes], tuple[str, MarshallableTypes]
        ]
        | None = None,
        after_setitem: Callable[[abc.Object, str, MarshallableTypes], None]
        | None = None,
    ) -> None:
        super().__init__(
            before_marshal=before_marshal,
            after_marshal=after_marshal,
            before_unmarshal=before_unmarshal,
            after_unmarshal=after_unmarshal,
            before_serialize=before_serialize,
            after_serialize=after_serialize,
            before_validate=before_validate,
            after_validate=after_validate,
        )
        self.before_setattr = before_setattr
        self.after_setattr = after_setattr
        self.before_setitem = before_setitem
        self.after_setitem = after_setitem


Object = deprecated(
    "`sob.hooks.Object` is deprecated, and will be removed in sob 3. "
    "Please use `sob.ObjectHooks` instead."
)(ObjectHooks)


class ArrayHooks(Hooks, abc.ArrayHooks):
    """
    Instances of this class hold functions ("hooks") to be executed
    at various points during marshalling, un-marshalling, serializing,
    de-serializing or validation.

    Please note the following context-specific definitions:

    - marshal: To convert an instance of an `sob.Model` sub-class into data
        suitable for serializing with `json.dumps`. For example, marshalling
        an instance of `sob.Dictionary`, or marshalling an instance of a
        sub-class of `sob.Object`, would result in a `dict` object.
    - unmarshal: To convert data de-serialized using `json.loads` into an
        instance of an `sob.Model` sub-class. For example, un-marshalling a
        `dict` object could return in an instance of `sob.Dictionary`
        (this would be the default if no types were specified), or could
        return an instance of one of the `sob.Model` sub-classes
        specified in the `types` parameter passed to `sob.unmarshal`.
    - serialize: To convert a marshalled object into a JSON string.
    - deserialize: To convert a JSON string into a python-native object.
    - validate: To check that the data held by a model instance is in
        compliance with that model's metadata. Because data types are
        enforced when attributes are set, validation only entails verifying
        that all required attributes are present, and that no extraneous
        attributes are present. Validation is only initiated explicitly,
        by passing a model instance to the `sob.validate` function.

    Attributes:
        before_marshal: A function called *before* marshalling a model.
            The `before_marshal` function should accept deserialized JSON
            data (pre-marshalling) as the first argument, and return the
            same type of data (or `None`) as the return value.
        after_marshal: A function to be called *after* marshalling a model.
            The `after_marshal` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_unmarshal: A function to be called *before* un-marshalling a
            model. The `before_unmarshal` function should accept an
            instance of the class to which it is associated as the only
            argument, and must return an instance of that class as the
            return value.
        after_unmarshal: A function to be called *after* un-marshalling a
            model. The `after_unmarshal` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value.
        before_serialize: A function to be called before serializing a
            model. The `before_serialize` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value. For most use cases, assigning a
            function to `after_unmarshal` and to `before_serialize` will
            produce the same result, however it is technically possible to
            unmarshal data without ever serializing it, so both hooks are
            provided.
        after_serialize: A function to be called after serializing a model.
            The `after_serialize` function should accept a JSON string as
            the only argument, and return a JSON string as the return
            value.
        before_validate: A function to be called before validating a model.
            The `before_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        after_validate: A function to be called after validating a model.
            The `after_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_setitem: A function to be called before assigning a value
            to an object by index. The `before_setitem` function should accept
            3 positional arguments: an instance of the class to which it is
            associated, the index, and the value to be assigned to that index
            position. The function should return a tuple containing an
            index and a value to be assigned to that position.
        after_setitem: A function to be called after assigning a value
            to an object by index. The `before_setitem` function should accept
            3 positional arguments: an instance of the class to which it is
            associated, the index, and the value assigned to that
            position. The function should return `None`.
        before_append: A function to be called before appending a value
            to the array. The `before_append` function should accept 2
            positional arguments: an instance of the class to which it is
            associated, and the value to be appended. The function should
            return the value to be appended.
        after_append: A function to be called after appending a value
            to the array. The `after_append` function should accept 2
            positional arguments: an instance of the class to which it is
            associated, and the value appended. The function should
            return `None`.
    """

    __module__: str = "sob"

    def __init__(
        self,
        before_marshal: Callable[[abc.Model], abc.Model] | None = None,
        after_marshal: Callable[[JSONTypes], JSONTypes] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_unmarshal: Callable[[abc.Model], abc.Model] | None = None,
        before_serialize: Callable[[JSONTypes], JSONTypes] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[abc.Model], abc.Model] | None = None,
        after_validate: Callable[[abc.Model], None] | None = None,
        before_setitem: Callable[
            [abc.Array, int, MarshallableTypes], tuple[int, MarshallableTypes]
        ]
        | None = None,
        after_setitem: Callable[[abc.Array, int, MarshallableTypes], None]
        | None = None,
        before_append: Callable[
            [abc.Array, MarshallableTypes], MarshallableTypes
        ]
        | None = None,
        after_append: Callable[[abc.Array, MarshallableTypes], None]
        | None = None,
    ) -> None:
        super().__init__(
            before_marshal=before_marshal,
            after_marshal=after_marshal,
            before_unmarshal=before_unmarshal,
            after_unmarshal=after_unmarshal,
            before_serialize=before_serialize,
            after_serialize=after_serialize,
            before_validate=before_validate,
            after_validate=after_validate,
        )
        self.before_setitem = before_setitem
        self.after_setitem = after_setitem
        self.before_append = before_append
        self.after_append = after_append


Array = deprecated(
    "`sob.hooks.Array` is deprecated, and will be removed in sob 3. "
    "Please use `sob.ArrayHooks` instead."
)(ArrayHooks)


class DictionaryHooks(Hooks, abc.DictionaryHooks):
    """
    Instances of this class hold functions ("hooks") to be executed
    at various points during marshalling, un-marshalling, serializing,
    de-serializing or validation.

    Please note the following context-specific definitions:

    - marshal: To convert an instance of an `sob.Dictionary` sub-class into
        data suitable for serializing with `json.dumps`. For example,
        marshalling an instance of `sob.Dictionary` would result in a `dict`
        object.
    - unmarshal: To convert data de-serialized using `json.loads` into an
        instance of an `sob.Model` sub-class. For example, un-marshalling a
        `dict` object could return in an instance of `sob.Dictionary`
        (this would be the default if no types were specified), or could
        return an instance of one of the `sob.Model` sub-classes
        specified in the `types` parameter passed to `sob.unmarshal`.
    - serialize: To convert a marshalled object into a JSON string.
    - deserialize: To convert a JSON string into a python-native object.
    - validate: To check that the data held by a model instance is in
        compliance with that model's metadata. Because data types are
        enforced when attributes are set, validation only entails verifying
        that all required attributes are present, and that no extraneous
        attributes are present. Validation is only initiated explicitly,
        by passing a model instance to the `sob.validate` function.

    Attributes:
        before_marshal: A function called *before* marshalling a model.
            The `before_marshal` function should accept deserialized JSON
            data (pre-marshalling) as the first argument, and return the
            same type of data (or `None`) as the return value.
        after_marshal: A function to be called *after* marshalling a model.
            The `after_marshal` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_unmarshal: A function to be called *before* un-marshalling a
            model. The `before_unmarshal` function should accept an
            instance of the class to which it is associated as the only
            argument, and must return an instance of that class as the
            return value.
        after_unmarshal: A function to be called *after* un-marshalling a
            model. The `after_unmarshal` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value.
        before_serialize: A function to be called before serializing a
            model. The `before_serialize` function should accept
            unmarshalled, but pre-serialized, JSON serializable data as
            the first argument, and return the same type of data (or
            `None`) as the return value. For most use cases, assigning a
            function to `after_unmarshal` and to `before_serialize` will
            produce the same result, however it is technically possible to
            unmarshal data without ever serializing it, so both hooks are
            provided.
        after_serialize: A function to be called after serializing a model.
            The `after_serialize` function should accept a JSON string as
            the only argument, and return a JSON string as the return
            value.
        before_validate: A function to be called before validating a model.
            The `before_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        after_validate: A function to be called after validating a model.
            The `after_validate` function should accept an instance of the
            class to which it is associated as the only argument, and must
            return an instance of that class as the return value.
        before_setitem: A function to be called before assigning a value
            to an object by key. The `before_setitem` function should accept 3
            positional arguments: an instance of the class to which it is
            associated, the item key, and the value to be assigned to that
            key. The function should return a tuple containing a
            key and a value to be assigned.
        after_setitem: A function to be called after assigning a value
            to an object by key. The `before_setitem` function should accept 3
            positional arguments: an instance of the class to which it is
            associated, the item key, and the value assigned to that
            key. The function should return `None`.
    """

    __module__: str = "sob"

    def __init__(
        self,
        before_marshal: Callable[[abc.Model], abc.Model] | None = None,
        after_marshal: Callable[[JSONTypes], JSONTypes] | None = None,
        before_unmarshal: Callable[[MarshallableTypes], MarshallableTypes]
        | None = None,
        after_unmarshal: Callable[[abc.Model], abc.Model] | None = None,
        before_serialize: Callable[[JSONTypes], JSONTypes] | None = None,
        after_serialize: Callable[[str], str] | None = None,
        before_validate: Callable[[abc.Model], abc.Model] | None = None,
        after_validate: Callable[[abc.Model], None] | None = None,
        before_setitem: Callable[
            [abc.Dictionary, str, MarshallableTypes],
            tuple[str, MarshallableTypes],
        ]
        | None = None,
        after_setitem: Callable[[abc.Dictionary, str, MarshallableTypes], None]
        | None = None,
    ):
        super().__init__(
            before_marshal=before_marshal,
            after_marshal=after_marshal,
            before_unmarshal=before_unmarshal,
            after_unmarshal=after_unmarshal,
            before_serialize=before_serialize,
            after_serialize=after_serialize,
            before_validate=before_validate,
            after_validate=after_validate,
        )
        self.before_setitem = before_setitem
        self.after_setitem = after_setitem


Dictionary = deprecated(
    "`sob.hooks.Dictionary` is deprecated, and will be removed in sob 3. "
    "Please use `sob.DictionaryHooks` instead."
)(DictionaryHooks)


def read_model_hooks(model: type | abc.Model) -> abc.Hooks | None:
    """
    Read the hooks associated with a sub-class or instance of `sob.Model`,
    or return `None` if no hooks are defined.

    Please note that the returned hooks may be inherited,
    and therefore should not be modified. Use `get_writable_model_hooks` to
    retrieve an instance of these hooks suitable for modification.
    """
    message: str
    if isinstance(model, abc.Model):
        return getattr(model, "_instance_hooks", None) or read_model_hooks(
            type(model)
        )
    if isinstance(model, type) and issubclass(model, abc.Model):
        base: type
        try:
            return next(
                getattr(base, "_class_hooks", None)
                for base in filter(
                    lambda base: issubclass(base, abc.Model),
                    model.__mro__,
                )
            )
        except StopIteration:
            return None
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


read = deprecated(
    "`sob.hooks.read` is deprecated, and will be removed in sob 3. "
    "Please use `sob.read_model_hooks` instead."
)(read_model_hooks)


def read_object_hooks(model: type | abc.Object) -> abc.ObjectHooks | None:
    """
    Read the hooks associated with a sub-class or instance of `sob.Object`,
    or return `None` if no hooks are defined.

    Please note that the returned hooks may be inherited,
    and therefore should not be modified. Use `get_writable_object_hooks` to
    retrieve an instance of these hooks suitable for modification.
    """
    return read_model_hooks(model)  # type: ignore


object_read = deprecated(
    "`sob.hooks.object_read` is deprecated, and will be removed in sob 3. "
    "Please use `sob.read_object_hooks` instead."
)(read_object_hooks)


def read_array_hooks(model: type | abc.Array) -> abc.ArrayHooks | None:
    """
    Read the hooks associated with a sub-class or instance of `sob.Array`,
    or return `None` if no hooks are defined.

    Please note that the returned hooks may be inherited,
    and therefore should not be modified. Use
    `get_writable_array_hooks` to retrieve an instance of these hooks
    suitable for modification.
    """
    return read_model_hooks(model)  # type: ignore


array_read = deprecated(
    "`sob.hooks.array_read` is deprecated, and will be removed in sob 3. "
    "Please use `sob.read_array_hooks` instead."
)(read_array_hooks)


def read_dictionary_hooks(
    model: type | abc.Dictionary,
) -> abc.DictionaryHooks | None:
    """
    Read hooks from a sub-class or instance of `sob.Dictionary`.

    Please note that the returned hooks may be inherited,
    and therefore should not be modified. Use `get_writable_dictionary_hooks`
    to retrieve an instance of these hooks suitable for modification.
    """
    return read_model_hooks(model)  # type: ignore


dictionary_read = deprecated(
    "`sob.hooks.dictionary_read` is deprecated, and will be removed in sob 3. "
    "Please use `sob.read_dictionary_hooks` instead."
)(read_dictionary_hooks)


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


def get_writable_model_hooks(model: type[abc.Model] | abc.Model) -> abc.Hooks:
    """
    Retrieve an instance of `sob.Hooks` which is associated directly with the
    `model` class or instance, and therefore suitable for modifying.

    If `model` is an instance of an `sob.Model` sub-class, and the instance
    does not have any hooks associated, the class hooks will be
    copied to the instance and returned.

    If `model` is a sub-class of `sob.Model`, but does not have any hooks
    associated, hooks will be copied from the first parent class which
    has hooks attributed, and the copy will be returned.

    If neither the `model` class or instance, nor any parent classes,
    have any hooks associated—a new instance of `sob.Hooks` will be
    created, attributed to `model`, and returned.
    """
    if not _is_model(model):
        raise TypeError(model)
    if isinstance(model, abc.Model):
        if model._instance_hooks is None:  # noqa: SLF001
            model._instance_hooks = deepcopy(  # noqa: SLF001
                read_model_hooks(type(model))
            )
        if model._instance_hooks is None:  # noqa: SLF001
            model._instance_hooks = (  # noqa: SLF001
                ObjectHooks()
                if isinstance(model, abc.Object)
                else ArrayHooks()
                if isinstance(model, abc.Array)
                else DictionaryHooks()
            )
        return model._instance_hooks  # noqa: SLF001
    if isinstance(model, type) and issubclass(model, abc.Model):
        if model._class_hooks is None:  # noqa: SLF001
            model._class_hooks = deepcopy(  # noqa: SLF001
                read_model_hooks(model)
            )
        if model._class_hooks is None:  # noqa: SLF001
            model._class_hooks = (  # noqa: SLF001
                ObjectHooks()
                if issubclass(model, abc.Object)
                else ArrayHooks()
                if issubclass(model, abc.Array)
                else DictionaryHooks()
            )
        return model._class_hooks  # noqa: SLF001
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


writable = deprecated(
    "`sob.hooks.writable` is deprecated, and will be removed in sob 3. "
    "Please use `sob.get_writable_model_hooks` instead."
)(get_writable_model_hooks)


def get_writable_object_hooks(model: type | abc.Object) -> abc.ObjectHooks:
    """
    Retrieve an instance of `sob.ObjectHooks` which is associated directly with
    the `model` class or instance, and therefore suitable for modifying.

    If `model` is an instance of an `sob.Object` sub-class, and the instance
    does not have any hooks associated, the class hooks will be
    copied to the instance and returned.

    If `model` is a sub-class of `sob.Object`, but does not have any hooks
    associated, hooks will be copied from the first parent class which
    has hooks attributed, and the copy will be returned.

    If neither the `model` class or instance, nor any parent classes,
    have any hooks associated—a new instance of `sob.ObjectHooks` will be
    created, attributed to `model`, and returned.
    """
    return get_writable_model_hooks(model)  # type: ignore


object_writable = deprecated(
    "`sob.hooks.object_writable` is deprecated, and will be removed in sob 3. "
    "Please use `sob.get_writable_object_hooks` instead."
)(get_writable_object_hooks)


def get_writable_array_hooks(model: type | abc.Array) -> abc.ArrayHooks:
    """
    Retrieve an instance of `sob.ArrayHooks` which is associated directly with
    the `model` class or instance, and therefore suitable for modifying.

    If `model` is an instance of an `sob.Array` sub-class, and the instance
    does not have any hooks associated, the class hooks will be
    copied to the instance and returned.

    If `model` is a sub-class of `sob.Array`, but does not have any hooks
    associated, hooks will be copied from the first parent class which
    has hooks attributed, and the copy will be returned.

    If neither the `model` class or instance, nor any parent classes,
    have any hooks associated—a new instance of `sob.ArrayHooks` will be
    created, attributed to `model`, and returned.
    """
    return get_writable_model_hooks(model)  # type: ignore


array_writable = deprecated(
    "`sob.hooks.array_writable` is deprecated, and will be removed in sob 3. "
    "Please use `sob.get_writable_array_hooks` instead."
)(get_writable_array_hooks)


def get_writable_dictionary_hooks(
    model: type | abc.Dictionary,
) -> abc.DictionaryHooks:
    """
    Retrieve an instance of `sob.DictionaryHooks` which is associated directly
    with the `model` class or instance, and therefore suitable for writing
    hooks to.

    If `model` is an instance of an `sob.Dictionary` sub-class, and the
    instance does not have any hooks associated, the parent class'es hooks will
    be copied to the instance and returned.

    If `model` is a sub-class of `sob.Dictionary`, but does not have any hooks
    associated, hooks will be copied from the first parent class which does
    have hooks attributed.

    If neither the `model` class or instance, nor any parent classes,
    have any hooks associated—a new instance of `sob.DictionaryHooks` will be
    created, attributed to `model`, and returned.
    """
    return get_writable_model_hooks(model)  # type: ignore


dictionary_writable = deprecated(
    "`sob.hooks.dictionary_writable` is deprecated, and will be removed in "
    "sob 3. Please use `sob.get_writable_dictionary_hooks` instead."
)(get_writable_dictionary_hooks)


def get_model_hooks_type(model: type | abc.Model) -> type:
    """
    Determine the type of metadata required for the specified `model`
    class or instance.
    """
    hooks_type: type
    if not isinstance(model, (type, abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model)
    if isinstance(model, type):
        if not issubclass(model, (abc.Object, abc.Dictionary, abc.Array)):
            raise TypeError(model)
        hooks_type = (
            ObjectHooks
            if issubclass(model, abc.Object)
            else ArrayHooks
            if issubclass(model, abc.Array)
            else DictionaryHooks
        )
    else:
        hooks_type = (
            ObjectHooks
            if isinstance(model, abc.Object)
            else ArrayHooks
            if isinstance(model, abc.Array)
            else DictionaryHooks
        )
    return hooks_type


type_ = deprecated(
    "`sob.hooks.type_` is deprecated, and will be removed in sob 3. "
    "Please use `sob.get_model_hooks_type` instead."
)(get_model_hooks_type)


def write_model_hooks(
    model: type[abc.Model] | abc.Model, hooks: abc.Hooks | None
) -> None:
    """
    Write hooks to a sub-class or instance of `sob.Model`.
    """
    if hooks is not None:
        # Verify that the metadata is of the correct type
        hooks_type: type[abc.Hooks] = get_model_hooks_type(model)
        if not isinstance(hooks, hooks_type):
            message: str = (
                f"Hooks assigned to `{get_qualified_name(type(model))}` "
                f"must be of type `{get_qualified_name(hooks_type)}`"
            )
            raise ValueError(message)
    if isinstance(model, abc.Model):
        model._instance_hooks = hooks  # noqa: SLF001
    else:
        if not issubclass(model, abc.Model):
            raise TypeError(model)
        model._class_hooks = hooks  # noqa: SLF001


write = deprecated(
    "`sob.hooks.write` is deprecated, and will be removed in sob 3. "
    "Please use `sob.write_model_hooks` instead."
)(write_model_hooks)
