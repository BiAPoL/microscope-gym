from abc import ABC, abstractmethod


class Stage(ABC):
    '''Stage interface class.

    methods:
        move_x_to(absolute_x_position)
        move_x_by(relative_x_position)
        move_y_to(absolute_y_position)
        move_y_by(relative_y_position)
        move_z_to(absolute_z_position)
        move_z_by(relative_z_position)

    properties:
        x_position()
        y_position()
        z_position()
        x_range()
        y_range()
        z_range()
    '''

    @abstractmethod
    def move_x_to(self, absolute_x_position: "float"):
        '''Move stage to absolute x position in µm.'''
        pass

    @abstractmethod
    def move_x_by(self, relative_x_position: "float"):
        '''Move stage by relative x position in µm.'''
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
    def move_z_to(self, absolute_z_position: "float"):
        '''Move stage to absolute z position in µm.'''
        pass

    @abstractmethod
    def move_z_by(self, relative_z_position: "float"):
        '''Move stage by relative z position in µm.'''
        pass

    @property
    @abstractmethod
    def x_position(self) -> "float":
        '''Get current x position in µm.'''
        pass

    @property
    @abstractmethod
    def y_position(self) -> "float":
        '''Get current y position in µm.'''
        pass

    @property
    @abstractmethod
    def z_position(self) -> "float":
        '''Get current z position in µm.'''
        pass

    @property
    @abstractmethod
    def x_range(self) -> "tuple[float, float]":
        '''Get x range in µm.'''
        pass

    @property
    @abstractmethod
    def y_range(self) -> "tuple[float, float]":
        '''Get y range in µm.'''
        pass

    @property
    @abstractmethod
    def z_range(self) -> "tuple[float, float]":
        '''Get z range in µm.'''
        pass
