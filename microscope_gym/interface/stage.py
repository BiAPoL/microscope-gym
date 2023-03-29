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
        self._last_move_time = time.time()
        self._z_position = value

    @property
    def y_position(self):
        return self._y_position

    @y_position.setter
    def y_position(self, value):
        if value < self.y_range[0] or value > self.y_range[1]:
            raise ValueError(f"Stage y position {value} out of allowed range: {self.y_range}")
        self._last_move_time = time.time()
        self._y_position = value

    @property
    def x_position(self):
        return self._x_position

    @x_position.setter
    def x_position(self, value):
        if value < self.x_range[0] or value > self.x_range[1]:
            raise ValueError(f"Stage x position {value} out of allowed range: {self.x_range}")
        self._last_move_time = time.time()
        self._x_position = value

    @property
    def is_moving(self):
        return time.time() - self._last_move_time < self._move_timeout

    def wait_for_move(self, check_interval=0.1):
        while self.is_moving:
            time.sleep(check_interval)
