'''Microscope interface for microscope_gym.'''
from abc import ABC, abstractmethod
import numpy


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
    def move_stage_to(self, z: "float", y: "float", x: "float"):
        '''Move stage to absolute z, y, x position in µm.'''
        pass

    @abstractmethod
    def move_stage_by(self, z: "float", y: "float", x: "float"):
        '''Move stage by relative z, y, x position in µm.'''
        pass

    @abstractmethod
    def acquire_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    @abstractmethod
    def acquire_z_stack(self, z_range: tuple) -> "numpy.ndarray":
        '''Acquire z-stack.

        Args:
            z_range (tuple of float):
                range of z positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 1 µm.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage z range.
                If z_range is None, the entire stage z range is used.
        '''
        pass

    @abstractmethod
    def acquire_tiled_image(self, y_range: tuple, x_range: tuple) -> "numpy.ndarray":
        '''Acquire tiled image.

        Args:
            y_range (tuple of float):
                range of y positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 90 % of the camera field of view height.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage y range.
                If y_range is None, the entire stage y range is used.
            x_range (tuple of float):
                range of x positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 90 % of the camera field of view width.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage x range.
                If x_range is None, the entire stage x range is used.
        '''
        pass

    @abstractmethod
    def acquire_tiled_z_stack(self, z_range: tuple, y_range: tuple, x_range: tuple) -> "numpy.ndarray":
        '''Acquire tiled z-stack.

        Args:
            z_range (tuple of float):
                range of z positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 1 µm.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage z range.
                If z_range is None, the entire stage z range is used.
            y_range (tuple of float):
                range of y positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 90 % of the camera field of view height.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage y range.
                If y_range is None, the entire stage y range is used.
            x_range (tuple of float):
                range of x positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 90 % of the camera field of view width.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage x range.
                If x_range is None, the entire stage x range is used.
        '''
        pass

    @abstractmethod
    def acquire_overview_image(self) -> "numpy.ndarray":
        '''Acquire overview image.'''
        pass

    @abstractmethod
    def get_metadata(self) -> "dict":
        '''Get metadata of microscope components and the corresponding pixel size and image dimensions in the sample.'''
        pass

    @abstractmethod
    def get_stage_position(self) -> "tuple":
        '''Get stage position in µm.'''
        pass
