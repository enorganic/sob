from copy import deepcopy
from typing import Any, Callable, Optional, Tuple, Union

from . import abc
from .utilities.inspect import qualified_name
from .utilities.assertion import assert_is_instance
from .abc import JSONTypes, MarshallableTypes


class Hooks(abc.Hooks):
    """
    TODO
    """

    def __init__(
        self,
        before_marshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_marshal: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        before_unmarshal: Optional[
            Callable[[MarshallableTypes], MarshallableTypes]
        ] = None,
        after_unmarshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        before_serialize: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_validate: Optional[Callable[[abc.Model], None]] = None,
    ):
        self.before_marshal = before_marshal
        self.after_marshal = after_marshal
        self.before_unmarshal = before_unmarshal
        self.after_unmarshal = after_unmarshal
        self.before_serialize = before_serialize
        self.after_serialize = after_serialize
        self.before_validate = before_validate
        self.after_validate = after_validate

    def __copy__(self) -> "Hooks":
        return self.__class__(**vars(self))

    def __deepcopy__(self, memo: dict = None) -> "Hooks":
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
        before_marshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_marshal: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        before_unmarshal: Optional[
            Callable[[MarshallableTypes], MarshallableTypes]
        ] = None,
        after_unmarshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        before_serialize: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_validate: Optional[Callable[[abc.Model], None]] = None,
        before_setattr: Optional[
            Callable[
                [abc.Object, str, MarshallableTypes],
                Tuple[str, MarshallableTypes],
            ]
        ] = None,
        after_setattr: Optional[
            Callable[[abc.Object, str, MarshallableTypes], None]
        ] = None,
        before_setitem: Optional[
            Callable[
                [abc.Object, str, MarshallableTypes],
                Tuple[str, MarshallableTypes],
            ]
        ] = None,
        after_setitem: Optional[
            Callable[[abc.Object, str, MarshallableTypes], None]
        ] = None,
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
        before_marshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_marshal: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        before_unmarshal: Optional[
            Callable[[MarshallableTypes], MarshallableTypes]
        ] = None,
        after_unmarshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        before_serialize: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_validate: Optional[Callable[[abc.Model], None]] = None,
        before_setitem: Optional[
            Callable[
                [abc.Array, int, MarshallableTypes],
                Tuple[int, MarshallableTypes],
            ]
        ] = None,
        after_setitem: Optional[
            Callable[[abc.Array, int, MarshallableTypes], None]
        ] = None,
        before_append: Optional[
            Callable[[abc.Array, MarshallableTypes], MarshallableTypes]
        ] = None,
        after_append: Optional[
            Callable[[abc.Array, MarshallableTypes], None]
        ] = None,
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
        before_marshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_marshal: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        before_unmarshal: Optional[
            Callable[[MarshallableTypes], MarshallableTypes]
        ] = None,
        after_unmarshal: Optional[Callable[[abc.Model], abc.Model]] = None,
        before_serialize: Optional[Callable[[JSONTypes], JSONTypes]] = None,
        after_serialize: Optional[Callable[[str], str]] = None,
        before_validate: Optional[Callable[[abc.Model], abc.Model]] = None,
        after_validate: Optional[Callable[[abc.Model], None]] = None,
        before_setitem: Optional[
            Callable[
                [abc.Dictionary, str, MarshallableTypes],
                Tuple[str, MarshallableTypes],
            ]
        ] = None,
        after_setitem: Optional[
            Callable[[abc.Dictionary, str, MarshallableTypes], None]
        ] = None,
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


def read(model: Union[type, abc.Model]) -> Any:
    """
    Read metadata from a model class or instance (the returned metadata may be
    inherited, and therefore should not be written to)
    """
    hooks: Optional[abc.Hooks] = getattr(model, "_hooks")
    if isinstance(model, abc.Model) and (hooks is None):
        hooks = read(type(model))
    return hooks


def object_read(model: Union[type, abc.Object]) -> Optional[abc.ObjectHooks]:
    """
    Read metadata from an `sob.model.Object` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read(model)


def array_read(model: Union[type, abc.Array]) -> Optional[abc.ArrayHooks]:
    """
    Read metadata from an `sob.model.Array` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read(model)


def dictionary_read(
    model: Union[type, abc.Dictionary]
) -> Optional[abc.DictionaryHooks]:
    """
    Read metadata from an `sob.model.Dictionary` sub-class or instance (the
    returned metadata may be inherited, and therefore should not be written
    to).
    """
    return read(model)


def writable(model: Union[type, abc.Model]) -> Any:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    hooks: Optional[abc.Hooks] = getattr(model, "_hooks")
    writable_hooks: Optional[abc.Hooks] = None
    if isinstance(model, type):
        assert issubclass(model, abc.Model)
        if hooks is None:
            new_hooks: Optional[Hooks] = (
                Object()
                if issubclass(model, abc.Object)
                else Array()
                if issubclass(model, abc.Array)
                else Dictionary()
                if issubclass(model, abc.Dictionary)
                else Hooks()
            )
            writable_hooks = new_hooks
        else:
            for base in model.__bases__:
                base_hooks: Optional[abc.Hooks]
                try:
                    base_hooks = getattr(base, "_hooks")
                except AttributeError:
                    base_hooks = None
                if hooks and (hooks is base_hooks):
                    writable_hooks = deepcopy(hooks)
                    break
    elif isinstance(model, abc.Model):
        if hooks is None:
            writable_hooks = deepcopy(writable(type(model)))
    if writable_hooks:
        setattr(model, "_hooks", writable_hooks)
    else:
        writable_hooks = hooks
    assert writable_hooks is not None
    return writable_hooks


def object_writable(model: Union[type, abc.Object]) -> abc.ObjectHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return writable(model)


def array_writable(model: Union[type, abc.Array]) -> abc.ArrayHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return writable(model)


def dictionary_writable(
    model: Union[type, abc.Dictionary]
) -> abc.DictionaryHooks:
    """
    Retrieve a metadata instance. If the instance currently inherits its
    metadata from a class or superclass, this function will copy that
    metadata and assign it directly to the model instance.
    """
    return writable(model)


def type_(model: Union[type, abc.Model]) -> type:
    """
    Get the type of metadata required for an object
    """
    hooks_type: type
    assert_is_instance(
        "model",
        model,
        (type, abc.Object, abc.Dictionary, abc.Array),
    )
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


def write(model: Union[type, abc.Model], hooks: Optional[abc.Hooks]) -> None:
    """
    Write metadata to a class or instance
    """
    if hooks is not None:
        # Verify that the metadata is of the correct type
        hooks_type: type = type_(model)
        if not isinstance(hooks, hooks_type):
            raise ValueError(
                f"Hooks assigned to `{qualified_name(type(model))}` "
                f"must be of type `{qualified_name(hooks_type)}`"
            )
    setattr(model, "_hooks", hooks)
