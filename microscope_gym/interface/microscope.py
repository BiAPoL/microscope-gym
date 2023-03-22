'''Microscope interface class.'''
from abc import ABC, abstractmethod


class Microscope(ABC):
    '''Base microscope class.

    methods:
        move_stage(x, y)
        capture_image()
        get_metadata()

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
    def capture_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    @abstractmethod
    def get_metadata(self) -> "dict":
        '''Get metadata of microscope components and the corresponding pixel size and image dimensions in the sample.'''
        pass
