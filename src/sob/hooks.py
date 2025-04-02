from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Callable, cast

from sob import abc
from sob.utilities import (
    get_calling_function_qualified_name,
    get_qualified_name,
)

if TYPE_CHECKING:
    from sob.abc import JSONTypes, MarshallableTypes


class Hooks(abc.Hooks):
    """
    TODO
    """

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
    TODO
    """

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


# For backwards compatibility
Object = ObjectHooks


class ArrayHooks(Hooks, abc.ArrayHooks):
    """
    TODO
    """

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


# For backwards compatibility
Array = ArrayHooks


class DictionaryHooks(Hooks, abc.DictionaryHooks):
    """
    TODO
    """

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


# For backwards compatibility
Dictionary = DictionaryHooks


def read_model_hooks(model: type | abc.Model) -> abc.Hooks | None:
    """
    Read metadata from a model class or instance (the returned metadata may be
    inherited, and therefore should not be written to)
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


# For backwards compatibility
read = read_model_hooks


def read_object_hooks(model: type | abc.Object) -> abc.ObjectHooks | None:
    """
    Read metadata from an `sob.model.Object` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read_model_hooks(model)  # type: ignore


# For backwards compatibility
object_read = read_object_hooks


def read_array_hooks(model: type | abc.Array) -> abc.ArrayHooks | None:
    """
    Read metadata from an `sob.model.Array` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read_model_hooks(model)  # type: ignore


# For backwards compatibility
array_read = read_array_hooks


def read_dictionary_hooks(
    model: type | abc.Dictionary,
) -> abc.DictionaryHooks | None:
    """
    Read metadata from an `sob.model.Dictionary` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read_model_hooks(model)  # type: ignore


# For backwards compatibility
dictionary_read = read_dictionary_hooks


def get_writable_model_hooks(model: type[abc.Model] | abc.Model) -> abc.Hooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    instance_hooks: abc.Hooks | None = model._instance_hooks  # noqa: SLF001
    writable_hooks: abc.Hooks | None = None
    if isinstance(model, type):
        if not issubclass(model, abc.Model):
            raise TypeError(model)
        if instance_hooks is None:
            new_hooks: Hooks | None = (
                ObjectHooks()
                if issubclass(model, abc.Object)
                else (
                    ArrayHooks()
                    if issubclass(model, abc.Array)
                    else (
                        DictionaryHooks()
                        if issubclass(model, abc.Dictionary)
                        else Hooks()
                    )
                )
            )
            writable_hooks = new_hooks
        else:
            base: type[abc.Model] | None
            for base in filter(
                lambda base: isinstance(base, type)
                and issubclass(base, abc.Model),
                model.__bases__,
            ):
                base_hooks: abc.Hooks | None
                try:
                    base_hooks = base._class_hooks  # noqa: SLF001
                except AttributeError:
                    base_hooks = None
                if instance_hooks and (instance_hooks is base_hooks):
                    writable_hooks = deepcopy(instance_hooks)
                    break
    elif isinstance(model, abc.Model):
        if instance_hooks is None:
            writable_hooks = deepcopy(get_writable_model_hooks(type(model)))
    if writable_hooks:
        model._instance_hooks = writable_hooks  # noqa: SLF001
    else:
        writable_hooks = instance_hooks
    return cast(abc.Hooks, writable_hooks)


# For backwards compatibility
writable = get_writable_model_hooks


def get_writable_object_hooks(model: type | abc.Object) -> abc.ObjectHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return get_writable_model_hooks(model)  # type: ignore


# For backwards compatibility
object_writable = get_writable_object_hooks


def get_writable_array_hooks(model: type | abc.Array) -> abc.ArrayHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return get_writable_model_hooks(model)  # type: ignore


# For backwards compatibility
array_writable = get_writable_array_hooks


def get_writable_dictionary_hooks(
    model: type | abc.Dictionary,
) -> abc.DictionaryHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return get_writable_model_hooks(model)  # type: ignore


# For backwards compatibility
dictionary_writable = get_writable_dictionary_hooks


def get_model_hooks_type(model: type | abc.Model) -> type:
    """
    Get the type of metadata required for an object
    """
    hooks_type: type
    if not isinstance(model, (type, abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model)
    if isinstance(model, type):
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


# For backwards compatibility
type_ = get_model_hooks_type


def write_model_hooks(
    model: type[abc.Model] | abc.Model, hooks: abc.Hooks | None
) -> None:
    """
    Write metadata to a class or instance
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


# For backwards compatibility
write = write_model_hooks
