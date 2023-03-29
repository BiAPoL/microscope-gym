'''Microscope objective class.

Since the objective does not have any methods, it is not implemented as an interface, but as a real class.'''


class Objective():
    '''Microscope objective class.

    properties:
        magnification: float
            magnification factor
        working_distance: float
            working distance in µm
        numerical_aperture: float
            numerical aperture - NA = sin(θ) (θ = half angle of cone of light captured by objective)
        immersion: str
            immersion medium (e.g. "air", "oil", "water", "glycerol", "silicone oil")
    '''

    def __init__(self, magnification: float, working_distance: float, numerical_aperture: float, immersion: str):
        self.magnification = magnification
        self.working_distance = working_distance
        self.numerical_aperture = numerical_aperture
        self.immersion = immersion
