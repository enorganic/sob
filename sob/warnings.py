from typing import Optional, Type

from sob.utilities.inspect import qualified_name

from . import abc, meta


class UndefinedObjectPropertyWarning(Warning):
    def __init__(
        self, object_instance: abc.Object, property_name: str
    ) -> None:
        self.object_instance: abc.Object = object_instance
        self.object_type: Type[abc.Object] = type(object_instance)
        self.property_name: str = property_name
        object_meta: Optional[abc.ObjectMeta] = meta.object_read(
            object_instance
        )
        repr_object_meta: str = ""
        if object_meta and object_meta.properties:
            repr_object_meta = f":\n{repr(object_meta.properties)}"
        super().__init__(
            f"The property `{property_name}` is not defined for "
            f"{qualified_name(self.object_type)}"
            f"{repr_object_meta}"
        )
