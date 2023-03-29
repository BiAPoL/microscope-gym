from abc import ABC, abstractmethod
import time

# TODO: refactor into real class


class Stage(ABC):
    '''Stage interface class.

    methods:
        get_nearest_position_in_range(z_position: float, y_position: float, x_position: float) -> tuple
            get nearest position in range
        wait_until_stopped(timeout: float) -> bool

    properties:
        z_position: float
            z position in µm
        y_position: float
            y position in µm
        x_position: float
            x position in µm
        z_range: tuple
            possible z range in µm
        y_range: tuple
            possible y range in µm
        x_range: tuple
            possible x range in µm
        is_moving: bool
            True if stage is currently moving, false otherwise
    '''

    def __init__(self, z_range: tuple, y_range: tuple, x_range: tuple):
        self.z_range = z_range
        self.y_range = y_range
        self.x_range = x_range

    @property
    def z_position(self):
        return self._z_position

    @z_position.setter
    def z_position(self, value):
        if value < self.z_range[0] or value > self.z_range[1]:
            raise ValueError(f"Stage z position {value} out of allowed range: {self.z_range}")
        self._z_position = value

    @property
    def y_position(self):
        return self._y_position

    @y_position.setter
    def y_position(self, value):
        if value < self.y_range[0] or value > self.y_range[1]:
            raise ValueError(f"Stage y position {value} out of allowed range: {self.y_range}")
        self._y_position = value

    @property
    def x_position(self):
        return self._x_position

    @x_position.setter
    def x_position(self, value):
        if value < self.x_range[0] or value > self.x_range[1]:
            raise ValueError(f"Stage x position {value} out of allowed range: {self.x_range}")
        self._x_position = value

    @property
    @abstractmethod
    def is_moving(self):
        '''Return True if stage is moving, False otherwise.'''
        pass

    @abstractmethod
    def wait_until_stopped(self):
        '''Wait until stage is not moving anymore.'''
        pass
