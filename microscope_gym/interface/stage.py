from abc import ABC, abstractmethod


class Stage(ABC):
    '''Stage interface class.

    methods:
        move_z_to(absolute_z_position)
        move_z_by(relative_z_position)
        move_y_to(absolute_y_position)
        move_y_by(relative_y_position)
        move_x_to(absolute_x_position)
        move_x_by(relative_x_position)

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
    '''

    @property
    def z_position(self):
        return self._z_position

    @z_position.setter
    def z_position(self, value):
        if value < self.z_range[0] or value > self.z_range[1]:
            raise ValueError("Stage z position out of range.")
        self._z_position = value

    @property
    def y_position(self):
        return self._y_position

    @y_position.setter
    def y_position(self, value):
        if value < self.y_range[0] or value > self.y_range[1]:
            raise ValueError("Stage y position out of range.")
        self._y_position = value

    @property
    def x_position(self):
        return self._x_position

    @x_position.setter
    def x_position(self, value):
        if value < self.x_range[0] or value > self.x_range[1]:
            raise ValueError("Stage x position out of range.")
        self._x_position = value

    @abstractmethod
    def move_z_to(self, absolute_z_position: "float"):
        '''Move stage to absolute z position in µm.'''
        pass

    @abstractmethod
    def move_z_by(self, relative_z_position: "float"):
        '''Move stage by relative z position in µm.'''
        pass

    @abstractmethod
    def move_y_to(self, absolute_y_position: "float"):
        '''Move stage to absolute y position in µm.'''
        pass

    @abstractmethod
    def move_y_by(self, relative_y_position: "float"):
        '''Move stage by relative y position in µm.'''
        pass

    @abstractmethod
    def move_x_to(self, absolute_x_position: "float"):
        '''Move stage to absolute x position in µm.'''
        pass

    @abstractmethod
    def move_x_by(self, relative_x_position: "float"):
        '''Move stage by relative x position in µm.'''
        pass
