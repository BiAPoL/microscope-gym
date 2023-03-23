'''Microscope interface class.'''
from abc import ABC, abstractmethod


class Microscope(ABC):
    '''Base microscope class.

    methods:
        move_stage(x, y)
        capture_image()
        acquire_z_stack()
        get_metadata()
        get_stage_position()

    properties:
        camera(): camera object
        stage(): stage object
    '''

    @abstractmethod
    def move_stage_to(self, x: "float", y: "float", z: "float"):
        '''Move stage to absolute x, y, z position in µm.'''
        pass

    @abstractmethod
    def move_stage_by(self, x: "float", y: "float", z: "float"):
        '''Move stage by relative x, y, z position in µm.'''
        pass

    @abstractmethod
    def acquire_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    @abstractmethod
    def acquire_z_stack(self, z_range: tuple, z_step: float) -> "numpy.ndarray":
        '''Acquire z-stack.

        Args:
            z_range (tuple of float): range of z positions in µm
            z_step (float): step size in µm
        '''
        pass

    @abstractmethod
    def get_metadata(self) -> "dict":
        '''Get metadata of microscope components and the corresponding pixel size and image dimensions in the sample.'''
        pass

    @abstractmethod
    def get_stage_position(self) -> "tuple":
        '''Get stage position in µm.'''
        pass
