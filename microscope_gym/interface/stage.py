from abc import ABC, abstractmethod
import time

# TODO: refactor into real class


class Stage(ABC):
    '''Stage interface class.

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

    def get_nearest_position_in_range(self, z_position: float = None,
                                      y_position: float = None, x_position: float = None):
        '''Return nearest safe position to given position.

        Parameters
        ----------
        position: tuple
            position to check

        Returns
        -------
        tuple
            nearest safe position
        '''
        if z_position is None:
            z_position = self.z_position
        if y_position is None:
            y_position = self.y_position
        if x_position is None:
            x_position = self.x_position
        return (max(self.z_range[0], min(z_position, self.z_range[1])),
                max(self.y_range[0], min(y_position, self.y_range[1])),
                max(self.x_range[0], min(x_position, self.x_range[1])))

    @property
    @abstractmethod
    def is_moving(self):
        '''Return True if stage is moving, False otherwise.'''
        pass

    @abstractmethod
    def wait_for_move(self):
        '''Wait until stage is not moving anymore.'''
        pass
