"""
This test suite aims to TODO
"""
import numbers
import typing
from copy import deepcopy
from datetime import datetime
from numbers import Number
from typing import IO, Optional, Sequence, Union

from sob import errors, hooks, meta, model, properties


class Measurement(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        quantity: Optional[Number] = None,
        unit_of_measure: Optional[str] = None,
    ) -> None:
        self.quantity = quantity
        self.unit_of_measure = unit_of_measure
        super().__init__(_)


meta.writable(Measurement).properties = dict(
    quantity=properties.Number(),
    unit_of_measure=properties.Enumerated(
        name='unitOfMeasure',
        types=(str,),
        values=(
            # Length
            'cm',  # Centimeter
            'dm',  # Decimeter
            'ft',  # Foot
            'in',  # Inch
            'km',  # Kilometer
            'm',   # Meter
            'mm',  # Millimeter
            'yd',  # Yard
            'ly',  # Light Year
            'nm',  # Nano Metre
            'µm',  # Micro Meter (Micron)
            # Weight
            'g',  # Gram
            'kg',  # Kilogram
            'oz',  # Ounce
            'lb',  # Pound
            't',  # Tonne (Metric)
            'u',  # Unified Atomic Mass Unit
            # Energy
            'j',  # Jules
            'ev',  # Electron Volt
            'erg',  # erg
            'cal',  # Calorie
            # Volume
            'l',  # Liter
            'ml',  # Milliliter
            'c',  # Cup
            'qt',  # Quart
            'gal',  # Gallon
        )
    )
)


class Energy(Measurement):

    pass


meta.writable(Energy).properties['unit_of_measure'].values = (
    'j',  # Jules
    'ev',  # Electron Volt
    'erg',  # erg
    'cal',  # Calorie
)


class Mass(Measurement):

    pass


meta.writable(Mass).properties['unit_of_measure'].values = (
    'g',   # Gram
    'kg',  # Kilogram
    'oz',  # Ounce
    'lb',  # Pound
    't',   # Tonne (Metric)
    'u',   # Unified Atomic Mass Unit
)


class Length(Measurement):

    pass


meta.writable(Length).properties['unit_of_measure'].values = (
    'cm',  # Centimeter
    'dm',  # Decimeter
    'ft',  # Foot
    'in',  # Inch
    'km',  # Kilometer
    'm',   # Meter
    'mm',  # Millimeter
    'yd',  # Yard
    'ly',  # Light Year
    'nm',  # Nano Metre
    'µm'   # Micro Meter (Micron)
)


class Volume(Measurement):

    pass


meta.writable(Volume).properties['unit_of_measure'].values = (
    'l',   # Liter
    'ml',  # Milliliter
    'c',   # Cup
    'qt',  # Quart
    'gal'  # Gallon
)


class SpatialPosition(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        x: Optional[numbers.Number] = None,
        y: Optional[numbers.Number] = None,
        z: Optional[numbers.Number] = None,
        unit_of_measure: Optional[str] = None,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.unit_of_measure = unit_of_measure
        super().__init__(_)


meta.writable(SpatialPosition).properties = dict(
    x=properties.Number(),
    y=properties.Number(),
    z=properties.Number(),
    unit_of_measure=deepcopy(
        meta.read(Length).properties['unit_of_measure']
    )
)


class Vector(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        x: Optional[numbers.Number] = None,
        y: Optional[numbers.Number] = None,
        z: Optional[numbers.Number] = None,
    ):
        self.x = x
        self.y = y
        self.z = z
        super().__init__(_)


meta.writable(Vector).properties = dict(
    x=properties.Number(),
    y=properties.Number(),
    z=properties.Number()
)


def after_validate_vector(vector: Vector) -> None:
    """
    Verifies that the direction vector is normalized (sum of all coordinates
    is equal to 1)
    """
    assert vector.x + vector.y + vector.z == 1


hooks.writable(SpatialPosition).after_validate = after_validate_vector


class SpaceTimeCoordinates(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        spacial_coordinates: Optional[SpatialPosition] = None,
        time: Optional[datetime] = None,
    ):
        self.spacial_coordinates = spacial_coordinates
        self.time = time
        super().__init__(_)


meta.writable(SpaceTimeCoordinates).properties = dict(
    spacial_coordinates=properties.Property(
        name='spacialCoordinates',
        types=(SpaceTimeCoordinates,),
        required=True
    ),
    time=properties.DateTime(
        required=True
    )
)


class Frequency(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        quantity: Optional[numbers.Number] = None,
        unit_of_measure: Optional[str] = None,
    ):
        self.quantity = quantity
        self.unit_of_measure = unit_of_measure
        super().__init__(_)


meta.writable(Frequency).properties = dict(
    quantity=properties.Number(
        required=True
    ),
    unit_of_measure=properties.Enumerated(
        name='unitOfMeasure',
        types=(str,),
        values=(
            'seconds',
            'minutes',
            'hours',
            'days'
        ),
        required=True
    )
)


class Speed(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        distance: Optional[Length] = None,
        frequency: Optional[Frequency] = None,
    ):
        self.distance = distance
        self.frequency = frequency
        super().__init__(_)


meta.writable(Speed).properties = dict(
    distance=properties.Property(
        types=(Length,),
        required=True
    ),
    frequency=properties.Property(
        types=(Frequency,),
        required=True
    )
)


class Velocity(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        direction: Optional[Vector] = None,
        magnitude: Optional[Speed] = None,
    ):
        self.direction = direction
        self.magnitude = magnitude
        super().__init__(_)


meta.writable(Velocity).properties = dict(
    direction=properties.Property(
        types=(Vector,),
        required=True
    ),
    magnitude=properties.Property(
        types=(Speed,),
        required=True
    )
)


class Acceleration(Velocity):

    pass


class Spin(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        axis: Optional[Vector] = None,
        frequency: Optional[Frequency] = None,
    ):
        self.axis = axis
        self.frequency = frequency
        super().__init__(_)


meta.writable(Spin).properties = dict(
    axis=properties.Property(
        types=(Vector,),
        required=True
    ),
    frequency=properties.Property(
        types=(Frequency,),
        required=True
    )
)


class Orbit(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        spin: Optional[Spin] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        radius: Optional[Length] = None,
    ):
        self.rotation = spin
        self.origin = origin
        self.radius = radius
        super().__init__(_)


meta.writable(Orbit).properties = dict(
    spin=properties.Property(
        types=(Spin,)
    ),
    origin=properties.Property(
        types=(SpaceTimeCoordinates,)
    ),
    radius=properties.Property(
        types=(Length,)
    )
)


class RotationMatrix(model.Array):

    pass


meta.writable(RotationMatrix).item_types = [
    properties.Array(
        item_types=[model.Number]
    )
]


def after_validate_rotation_matrix(
    rotation_matrix: RotationMatrix
) -> RotationMatrix:
    """
    This function checks to make sure that the matrix contains 3 rows of 3
    numbers, and throws a validation error otherwise.
    """
    row_quantity = len(rotation_matrix)
    if row_quantity != 3:
        raise errors.ValidationError(
            'A rotation matrix must consist of exactly 3 rows (currently has '
            '%s)' % str(row_quantity)
        )
    i = 1
    for row in rotation_matrix:
        row_length = len(row)
        if row_length != 3:
            raise errors.ValidationError(
                'Each row in a rotation matrix must consist of exactly 3 '
                'numbers, row %s contains %s numbers:\n%s' % (
                    str(i), str(row_length), repr(rotation_matrix)
                )
            )
        i += 1
    return rotation_matrix


hooks.writable(RotationMatrix).after_validate = after_validate_rotation_matrix


class Matter(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Velocity] = None,
        acceleration: Optional[Acceleration] = None,
    ):
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        super().__init__(_)


meta.writable(Matter).properties = dict(
    name=properties.String(
        required=False
    ),
    mass=properties.Property(
        types=(Measurement,),
        required=True
    ),
    origin=properties.Property(
        types=(SpaceTimeCoordinates,),
        required=True
    ),
    velocity=properties.Property(
        types=(Velocity,)
    ),
    acceleration=properties.Property(
        types=(Acceleration,)
    )
)


class Nucleus(Matter):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        spin: Optional[Spin] = None,
    ):
        # This needs to come before attribute assignment when inheriting
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        self.spin = spin


meta.writable(Nucleus).properties.update(
    spin=properties.Property(
        types=(Spin,),
        required=True
    )
)


class Neutron(Matter):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Velocity] = None,
        acceleration: Optional[Acceleration] = None,
        orbit: Optional[Orbit] = None,
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        self.orbit = orbit


meta.writable(Neutron).properties.update(
    orbit=properties.Property(
        types=(Orbit,),
        required=True
    )
)


class Electron(Neutron):

    pass


class Proton(Neutron):

    pass


class Positron(Neutron):

    pass


class Neutrino(Neutron):

    pass


class Atom(Matter):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        mass: Optional[Measurement] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        nucleus: Optional[Nucleus] = None,
        protons: Optional[Sequence[Proton]] = None,
        electrons: Optional[Sequence[Electron]] = None,
        neutrons: Optional[Sequence[Neutron]] = None,
        name: Optional[str] = None,
    ):
        super().__init__(_)
        self.origin = origin
        self.mass = mass
        self.velocity = velocity
        self.acceleration = acceleration
        self.nucleus = nucleus
        self.protons = protons
        self.electrons = electrons
        self.neutrons = neutrons
        self.name = name


meta.writable(Atom).properties.update(
    nucleus=properties.Property(
        types=(Nucleus,),
        required=True
    ),
    neutrons=properties.Array(
        item_types=(Neutron,),
        required=True
    ),
    protons=properties.Array(
        item_types=(Proton,),
        required=True
    ),
    electrons=properties.Array(
        item_types=(Electron,),
        required=True
    ),
    positrons=properties.Array(
        item_types=(Positron,),
        required=True
    )
)


class Molecule(Matter):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        atoms: Optional[Sequence[Atom]] = None,
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.atoms = atoms
        self.velocity = velocity
        self.acceleration = acceleration


meta.writable(Molecule).properties.update(
    atoms=properties.Array(
        item_types=(Atom,),
        required=True
    ),
    velocity=properties.Property(
        types=(Vector,)
    ),
    acceleration=properties.Property(
        types=(Vector,)
    )
)


class Ion(Molecule):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        atoms: Optional[Sequence[Atom]] = None,
        charge: Optional[int] = None
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.atoms = atoms
        self.velocity = velocity
        self.acceleration = acceleration
        self.charge = charge


meta.writable(Ion).properties.update(
    charge=properties.Integer()
)


class Body(Matter):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        contents: Optional[Sequence['Body', Ion, 'Molucule', Atom]] = None,
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        self.contents = contents


meta.writable(Body).properties.update(
    contents=properties.Array(
        item_types=(
            Body,
            Ion,
            Molecule,
            Atom
        ),
        required=True
    )
)


class Satellite(Matter):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        axial_rotation: Optional[Spin] = None,
        orbital_rotation: Optional[Orbit] = None,
        satellites: Optional[Sequence['Satellite']] = None,
        contents: Optional[Sequence[Body]] = None,
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        self.axial_rotation = axial_rotation
        self.orbital_rotation = orbital_rotation
        self.satellites = satellites
        self.contents = contents


meta.writable(Satellite).properties.update(
    axial_rotation=properties.Property(
        name='axialRotation',
        types=(Spin,)
    ),
    orbital_rotation=properties.Property(
        name='orbitalRotation',
        types=(Orbit,)
    ),
    satellites=properties.Array(
        item_types=(
            Satellite,
        )
    ),
    contents=properties.Array(
        item_types=(
            Body,
            Ion,
            Molecule,
            Atom,
            Matter
        )
    )
)


class Asteroid(Satellite):

    pass


class Comet(Satellite):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        spin: Optional[Spin] = None,
        orbit: Optional[Orbit] = None,
        satellites: Optional[Sequence[Satellite]] = None,
        nucleus: Optional[Body] = None,
        tail: Optional[Sequence[Ion, Molecule, Atom]] = None,
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        self.spin = spin
        self.orbit = orbit
        self.satellites = satellites
        self.nucleus = nucleus
        self.tail = tail


comet_properties = meta.writable(Comet).properties
comet_properties.update(
    tail=properties.Array(
        item_types=(Body, Ion, Molecule, Atom)
    ),
)
del comet_properties['contents']


class Moon(Satellite):

    pass


class DwarfPlanet(Satellite):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
        name: Optional[str] = None,
        mass: Optional[Measurement] = None,
        origin: Optional[SpaceTimeCoordinates] = None,
        velocity: Optional[Vector] = None,
        acceleration: Optional[Vector] = None,
        spin: Optional[Spin] = None,
        orbit: Optional[Orbit] = None,
        satellites: Optional[Sequence[Satellite]] = None,
        contents: Optional[Sequence[Body]] = None,
        dwarf: Optional[bool] = None,
    ):
        super().__init__(_)
        self.name = name
        self.mass = mass
        self.origin = origin
        self.velocity = velocity
        self.acceleration = acceleration
        self.spin = spin
        self.orbit = orbit
        self.satellites = satellites
        self.contents = contents
        self.is_dwarf = dwarf


meta.writable(DwarfPlanet).properties.update(
    dwarf=properties.Enumerated(
        types=(properties.Boolean(),),
        values=(True,)
    )
)
meta.writable(DwarfPlanet).properties['satellites'].item_types = [Moon]


class Planet(DwarfPlanet):

    pass


meta.writable(Planet).properties.update(
    dwarf=properties.Enumerated(
        types=(properties.Boolean(),),
        values=(False,)
    )
)


class Star(Satellite):

    pass


meta.writable(Star).properties['satellites'].item_types = [
    Star,
    Planet,
    DwarfPlanet,
    Comet,
    Asteroid,
    Satellite
]


class Galaxy(Satellite):

    pass


meta.writable(Galaxy).properties['satellites'].item_types = [
    Galaxy,
    Star
]


def before_validate_galaxy(galaxy: Galaxy) -> Galaxy:
    if not galaxy.satellites:
        raise errors.ValidationError(
            'All galaxies must contain at least one star or galaxy.'
        )
    return galaxy


hooks.writable(Galaxy).before_validate = before_validate_galaxy


class Universe(model.Object):

    def __init__(
        self,
        _: Optional[Union[str, bytes, dict, typing.Sequence, IO]] = None,
        name: Optional[str] = None,
        galaxies: Optional[Sequence[Galaxy]] = None
    ):
        self.name = name
        self.galaxies = galaxies
        super().__init__(_)


meta.writable(Universe).properties = dict(
    name=properties.String(),
    galaxies=properties.Array(
        item_types=[Galaxy]
    )
)


class Multiverse(model.Array):

    pass


meta.writable(Multiverse).item_types = [Universe]


def get_milky_way():

    # Make some stars
    sun = Star(
        name='Sun'
    )
    alpha_centauri_a = Star(
        name='Alpha Centauri A'
    )
    assert alpha_centauri_a.name == 'Alpha Centauri A'
    alpha_centauri_b = Star(
        name='Alpha Centauri B'
    )
    proxima_centuari = Star(
        name='Proxima Centauri'
    )

    return Galaxy(
        name='Milky Way',
        satellites=[
            sun,
            alpha_centauri_a,
            alpha_centauri_b,
            proxima_centuari
        ]
    )


def get_universe_prime():
    return Universe(
        galaxies=[
            get_milky_way()
        ]
    )


def get_multiverse():
    """
    Build a representation of the multiverse for use in testing `sob`.
    """

    return Multiverse([
        get_universe_prime()
    ])


def test_model_object_multiverse():
    multiverse = get_multiverse()
    # print(meta.read(Star))
    # print(repr(multiverse[0]))
    print(repr(multiverse))
    # multiverse[0].galaxies[0].satellites[0].name = 'Name'
    # print(repr(multiverse[0].galaxies[0].satellites[0].name))


if __name__ == '__main__':
    test_model_object_multiverse()
