'''Microscope objective interface class.'''
from abc import ABC, abstractmethod


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

    @property
    @abstractmethod
    def magnification(self) -> "float":
        '''Get current magnification.'''
        pass

    @property
    @abstractmethod
    def working_distance(self) -> "float":
        '''Get current working distance.'''
        pass

    @property
    @abstractmethod
    def numerical_aperture(self) -> "float":
        '''Get current numerical aperture.'''
        pass

    @property
    @abstractmethod
    def immersion(self) -> "str":
        '''Get current immersion medium.'''
        pass
