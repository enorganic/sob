from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

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


class Object(Hooks, abc.ObjectHooks):
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


class Array(Hooks, abc.ArrayHooks):
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


class Dictionary(Hooks, abc.DictionaryHooks):
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


def read(model: type | abc.Model) -> Any:
    """
    Read metadata from a model class or instance (the returned metadata may be
    inherited, and therefore should not be written to)
    """
    message: str
    if isinstance(model, abc.Model):
        return model._hooks or read(type(model))  # noqa: SLF001
    if isinstance(model, type):
        if issubclass(model, abc.Model):
            # return getattr(model, "_hooks")
            base: type
            try:
                return next(
                    filter(
                        None,
                        (
                            getattr(base, "_hooks", None)
                            for base in model.__mro__
                        ),
                    )
                )
            except StopIteration:
                return None
        else:
            message = (
                f"{get_calling_function_qualified_name()} requires a "
                "parameter which is an instance or sub-class of "
                f"`{get_qualified_name(abc.Model)}`, not "
                f"`{get_qualified_name(model)}`"
            )
            raise TypeError(message)
    else:
        repr_model: str = repr(model)
        message = (
            "{} requires a parameter which is an instance or sub-class of "
            "`{}`, not{}".format(
                get_calling_function_qualified_name(),
                get_qualified_name(abc.Model),
                (
                    f":\n{repr_model}"
                    if "\n" in repr_model
                    else f" `{repr_model}`"
                ),
            )
        )
        raise TypeError(message)


def object_read(model: type | abc.Object) -> abc.ObjectHooks | None:
    """
    Read metadata from an `sob.model.Object` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read(model)


def array_read(model: type | abc.Array) -> abc.ArrayHooks | None:
    """
    Read metadata from an `sob.model.Array` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read(model)


def dictionary_read(
    model: type | abc.Dictionary,
) -> abc.DictionaryHooks | None:
    """
    Read metadata from an `sob.model.Dictionary` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read(model)


def writable(model: type[abc.Model] | abc.Model) -> Any:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    hooks: abc.Hooks | None = model._hooks  # noqa: SLF001
    writable_hooks: abc.Hooks | None = None
    if isinstance(model, type):
        if not issubclass(model, abc.Model):
            raise TypeError(model)
        if hooks is None:
            new_hooks: Hooks | None = (
                Object()
                if issubclass(model, abc.Object)
                else (
                    Array()
                    if issubclass(model, abc.Array)
                    else (
                        Dictionary()
                        if issubclass(model, abc.Dictionary)
                        else Hooks()
                    )
                )
            )
            writable_hooks = new_hooks
        else:
            base: type[abc.Model]
            for base in filter(
                lambda base: issubclass(base, abc.Model), model.__bases__
            ):
                base_hooks: abc.Hooks | None
                try:
                    base_hooks = base._hooks  # noqa: SLF001
                except AttributeError:
                    base_hooks = None
                if hooks and (hooks is base_hooks):
                    writable_hooks = deepcopy(hooks)
                    break
    elif isinstance(model, abc.Model):
        if hooks is None:
            writable_hooks = deepcopy(writable(type(model)))
    if writable_hooks:
        model._hooks = writable_hooks  # noqa: SLF001
    else:
        writable_hooks = hooks
    return writable_hooks


def object_writable(model: type | abc.Object) -> abc.ObjectHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return writable(model)


def array_writable(model: type | abc.Array) -> abc.ArrayHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return writable(model)


def dictionary_writable(
    model: type | abc.Dictionary,
) -> abc.DictionaryHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return writable(model)


def type_(model: type | abc.Model) -> type:
    """
    Get the type of metadata required for an object
    """
    hooks_type: type
    if not isinstance(model, (type, abc.Object, abc.Dictionary, abc.Array)):
        raise TypeError(model)
    if isinstance(model, type):
        hooks_type = (
            Object
            if issubclass(model, abc.Object)
            else Array
            if issubclass(model, abc.Array)
            else Dictionary
        )
    else:
        hooks_type = (
            Object
            if isinstance(model, abc.Object)
            else Array
            if isinstance(model, abc.Array)
            else Dictionary
        )
    return hooks_type


def write(model: type[abc.Model] | abc.Model, hooks: abc.Hooks | None) -> None:
    """
    Write metadata to a class or instance
    """
    if hooks is not None:
        # Verify that the metadata is of the correct type
        hooks_type: type[abc.Hooks] = type_(model)
        if not isinstance(hooks, hooks_type):
            message: str = (
                f"Hooks assigned to `{get_qualified_name(type(model))}` "
                f"must be of type `{get_qualified_name(hooks_type)}`"
            )
            raise ValueError(message)
    model._hooks = hooks  # noqa: SLF001
