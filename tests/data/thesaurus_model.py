from __future__ import annotations
import typing
import sob


class AnimalMammal(sob.Object):

    __slots__: tuple[str, ...] = (
        "is_cute",
        "is_delicious",
        "is_furry",
        "name",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        is_cute: (
            bool
            | None
        ) = None,
        is_delicious: (
            bool
            | str
            | None
        ) = None,
        is_furry: (
            bool
            | str
            | None
        ) = None,
        name: (
            str
            | None
        ) = None
    ) -> None:
        self.is_cute: (
            bool
            | None
        ) = is_cute
        self.is_delicious: (
            bool
            | str
            | None
        ) = is_delicious
        self.is_furry: (
            bool
            | str
            | None
        ) = is_furry
        self.name: (
            str
            | None
        ) = name
        super().__init__(_data)


class AnimalBivalve(sob.Object):

    __slots__: tuple[str, ...] = (
        "is_ambulatory",
        "is_delicious",
        "name",
        "spreads_norovirus",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        is_ambulatory: (
            bool
            | None
        ) = None,
        is_delicious: (
            bool
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        spreads_norovirus: (
            bool
            | None
        ) = None
    ) -> None:
        self.is_ambulatory: (
            bool
            | None
        ) = is_ambulatory
        self.is_delicious: (
            bool
            | None
        ) = is_delicious
        self.name: (
            str
            | None
        ) = name
        self.spreads_norovirus: (
            bool
            | None
        ) = spreads_norovirus
        super().__init__(_data)


class PlantVegetable(sob.Object):

    __slots__: tuple[str, ...] = (
        "is_bitter",
        "is_crunchy",
        "is_spicy",
        "is_sweet",
        "name",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        is_bitter: (
            bool
            | None
        ) = None,
        is_crunchy: (
            bool
            | None
        ) = None,
        is_spicy: (
            bool
            | None
        ) = None,
        is_sweet: (
            bool
            | None
        ) = None,
        name: (
            str
            | None
        ) = None
    ) -> None:
        self.is_bitter: (
            bool
            | None
        ) = is_bitter
        self.is_crunchy: (
            bool
            | None
        ) = is_crunchy
        self.is_spicy: (
            bool
            | None
        ) = is_spicy
        self.is_sweet: (
            bool
            | None
        ) = is_sweet
        self.name: (
            str
            | None
        ) = name
        super().__init__(_data)


class Mineral(sob.Object):

    __slots__: tuple[str, ...] = (
        "is_edible",
        "is_radioactive",
        "is_shiny",
        "is_valuable",
        "name",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        is_edible: (
            bool
            | str
            | None
        ) = None,
        is_radioactive: (
            bool
            | None
        ) = None,
        is_shiny: (
            bool
            | None
        ) = None,
        is_valuable: (
            bool
            | None
        ) = None,
        name: (
            str
            | None
        ) = None
    ) -> None:
        self.is_edible: (
            bool
            | str
            | None
        ) = is_edible
        self.is_radioactive: (
            bool
            | None
        ) = is_radioactive
        self.is_shiny: (
            bool
            | None
        ) = is_shiny
        self.is_valuable: (
            bool
            | None
        ) = is_valuable
        self.name: (
            str
            | None
        ) = name
        super().__init__(_data)


class LotteryNumbersPowerBall(sob.Array):

    def __init__(
        self,
        items: (
            typing.Iterable[
                int
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None
    ) -> None:
        super().__init__(items)


sob.get_writable_object_meta(  # type: ignore
    AnimalMammal
).properties = sob.Properties([
    (
        'is_cute',
        sob.BooleanProperty(
            name="isCute"
        )
    ),
    (
        'is_delicious',
        sob.Property(
            name="isDelicious",
            types=sob.Types([
                bool,
                str
            ])
        )
    ),
    (
        'is_furry',
        sob.Property(
            name="isFurry",
            types=sob.Types([
                bool,
                str
            ])
        )
    ),
    (
        'name',
        sob.StringProperty(
            name="name"
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    AnimalBivalve
).properties = sob.Properties([
    (
        'is_ambulatory',
        sob.BooleanProperty(
            name="isAmbulatory"
        )
    ),
    (
        'is_delicious',
        sob.BooleanProperty(
            name="isDelicious"
        )
    ),
    (
        'name',
        sob.StringProperty(
            name="name"
        )
    ),
    (
        'spreads_norovirus',
        sob.BooleanProperty(
            name="spreadsNorovirus"
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    PlantVegetable
).properties = sob.Properties([
    (
        'is_bitter',
        sob.BooleanProperty(
            name="isBitter"
        )
    ),
    (
        'is_crunchy',
        sob.BooleanProperty(
            name="isCrunchy"
        )
    ),
    (
        'is_spicy',
        sob.BooleanProperty(
            name="isSpicy"
        )
    ),
    (
        'is_sweet',
        sob.BooleanProperty(
            name="isSweet"
        )
    ),
    (
        'name',
        sob.StringProperty(
            name="name"
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Mineral
).properties = sob.Properties([
    (
        'is_edible',
        sob.Property(
            name="isEdible",
            types=sob.Types([
                bool,
                str
            ])
        )
    ),
    (
        'is_radioactive',
        sob.BooleanProperty(
            name="isRadioactive"
        )
    ),
    (
        'is_shiny',
        sob.BooleanProperty(
            name="isShiny"
        )
    ),
    (
        'is_valuable',
        sob.BooleanProperty(
            name="isValuable"
        )
    ),
    (
        'name',
        sob.StringProperty(
            name="name"
        )
    )
])
sob.get_writable_array_meta(  # type: ignore
    LotteryNumbersPowerBall
).item_types = sob.Types([
    int
])
