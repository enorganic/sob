from abc import ABC, ABCMeta


class Meta(ABC):

    __metaclass__ = ABCMeta


class Object(Meta, ABC):

    pass


class Dictionary(Meta, ABC):

    pass


class Array(Meta, ABC):

    pass


class Properties(Meta, ABC):

    pass


class Version(Meta, ABC):

    pass
