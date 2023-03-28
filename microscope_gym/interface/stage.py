from abc import ABC, abstractmethod
import time


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
            maximum allowed z range in µm
        y_range: tuple
            maximum allowed y range in µm
        x_range: tuple
            maximum allowed x range in µm
        is_moving: bool
            True if stage is moving, false otherwise
    '''

    @property
    def z_position(self):
        return self._z_position

    @z_position.setter
    def z_position(self, value):
        if value < self.z_range[0] or value > self.z_range[1]:
            raise ValueError("Stage z position out of range.")
        self._last_move_time = time.time()
        self._z_position = value

    @property
    def y_position(self):
        return self._y_position

    @y_position.setter
    def y_position(self, value):
        if value < self.y_range[0] or value > self.y_range[1]:
            raise ValueError("Stage y position out of range.")
        self._last_move_time = time.time()
        self._y_position = value

    @property
    def x_position(self):
        return self._x_position

    @x_position.setter
    def x_position(self, value):
        if value < self.x_range[0] or value > self.x_range[1]:
            raise ValueError("Stage x position out of range.")
        self._last_move_time = time.time()
        self._x_position = value

    @property
    def is_moving(self):
        return time.time() - self._last_move_time < self._move_timeout

    def wait_for_move(self):
        while self.is_moving:
            time.sleep(0.1)
