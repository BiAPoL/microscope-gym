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
        x_position: float
            x position in µm
        y_position: float
            y position in µm
        z_position: float
            z position in µm
        x_range: tuple
            maximum allowed x range in µm
        y_range: tuple
            maximum allowed y range in µm
        z_range: tuple
            maximum allowed z range in µm
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