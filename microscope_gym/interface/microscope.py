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
    def move_stage_to(self, z: float, y: float, x: float):
        '''Move stage to absolute z, y, x position in µm.'''
        pass

    @abstractmethod
    def move_stage_by(self, z: float, y: float, x: float):
        '''Move stage by relative z, y, x position in µm.'''
        pass

    @abstractmethod
    def scan_stage_positions(self, y_range: tuple, x_range: tuple):
        '''Scan stage positions in µm.

        Args:
            y_range (tuple of float):
                range of y positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 90 % of the camera field of view height.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage y range.
                If y_range is None, the entire stage y range is used.
                implemented by the _set_range() method.
            x_range (tuple of float):
                range of x positions in µm, works like the range() function argument (start, stop, step).
                If step is not given, it defaults to 90 % of the camera field of view width.
                If only one argument is given, it is interpreted as the stop argument and start will be the minimum stage x range.
                If x_range is None, the entire stage x range is used.
                implemented by the _set_range() method.
        '''
        pass

    @abstractmethod
    def get_stage_position(self) -> tuple:
        '''Get stage position in µm.'''
        pass

    @abstractmethod
    def get_sample_pixel_size_um(self) -> float:
        '''Get pixel size in sample space in µm.'''
        pass

    @abstractmethod
    def get_field_of_view_um(self) -> tuple:
        '''Get field of view in µm.'''
        pass

    @abstractmethod
    def get_metadata(self) -> dict:
        '''Get metadata of microscope components and the corresponding pixel size and image dimensions in the sample.'''
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

    def _set_range(self, range: tuple, default_range: tuple):
        if len(range) < 1:
            range = default_range
        if len(range) < 2:
            range = (default_range[0], range, default_range[2])
        if len(range) < 3:
            range = range + (default_range[2],)
        return range


# make stage position getter and setter
