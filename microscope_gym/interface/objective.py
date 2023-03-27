'''Microscope objective interface class.'''
from abc import ABC


class Objective(ABC):
    '''Microscope objective interface class.

    properties:
        magnification: float
            magnification
        working_distance: float
            working distance in µm
        numerical_aperture: float
            numerical aperture
        immersion: str
            immersion medium
    '''
