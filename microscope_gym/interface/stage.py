from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field, validator
import time


class Axis(BaseModel):
    name: str
    min: float
    max: float
    position_um: float
    is_moving: bool = Field(default=False)

    @validator('position_um')
    @classmethod
    def position_in_range(cls, position, values, **kwargs):
        if position < values['min'] or position > values['max']:
            raise ValueError(
                f"{values['name']}-axis position {position} is not in range {values['min']} - {values['max']}")
        return position

    class Config:
        validate_assignment = True


def get_nearest_position_in_range(axis: Axis, position: float) -> float:
    return max(axis.min, min(position, axis.max))


class Stage():
    '''Stage interface class.

    methods:
        get_nearest_positions_in_range(z_position: float, y_position: float, x_position: float) -> tuple
            get nearest position in range
        wait_until_stopped(timeout_ms: float) -> bool
            wait until stage is stopped, return True if stopped, False if timeout

    properties:
        axes: list[Axes]
            list of Axis objects
        axes_dict: dict
            dictionary where keys are the axes names
        position_um: list[float]
            list of positions in um
        z_position_um: float
            z-axis position in um
        y_position_um: float
            y-axis position in um
        x_position_um: float
            x-axis position in um
        z_range: tuple[float, float]
            z-axis range in um
        y_range: tuple[float, float]
            y-axis range in um
        x_range: tuple[float, float]
            x-axis range in um
        is_moving: bool
            True if stage is moving, False otherwise
    '''
    axes_dict: Dict[str, Axis]
    axes: List[Axis]

    def __init__(self, axes: List[Axis]):
        self.axes = axes
        self.axes_dict = {axis.name: axis for axis in axes}

    @property
    def position_um(self):
        return tuple([axis.position_um for axis in self.axes])

    @position_um.setter
    def position_um(self, positions: Tuple[float]):
        axis_names = [axis.name for axis in self.axes]
        self._update_axis_positions(axis_names, positions)

    @property
    def z_position_um(self):
        return self.axes_dict['z'].position_um

    @z_position_um.setter
    def z_position_um(self, position: float):
        self._update_axis_positions(['z'], [position])

    @property
    def y_position_um(self):
        return self.axes_dict['y'].position_um

    @y_position_um.setter
    def y_position_um(self, position: float):
        self._update_axis_positions(['y'], [position])

    @property
    def x_position_um(self):
        return self.axes_dict['x'].position_um

    @x_position_um.setter
    def x_position_um(self, position: float):
        self._update_axis_positions(['x'], [position])

    @property
    def z_range(self):
        return self.axes_dict['z'].min, self.axes_dict['z'].max

    @property
    def y_range(self):
        return self.axes_dict['y'].min, self.axes_dict['y'].max

    @property
    def x_range(self):
        return self.axes_dict['x'].min, self.axes_dict['x'].max

    @property
    def is_moving(self):
        return any([axis.is_moving for axis in self.axes])

    def get_zyx_position_in_axes_order(self, z_position_um: float = None,
                                       y_position_um: float = None, x_position_um: float = None):
        '''Return z, y, x position in the order that the axes are stored in the "axes" list.'''
        if z_position_um is None:
            z_position_um = self.z_position_um
        if y_position_um is None:
            y_position_um = self.y_position_um
        if x_position_um is None:
            x_position_um = self.x_position_um
        result = []
        for axis in self.axes:
            if axis.name == 'z':
                result.append(z_position_um)
            elif axis.name == 'y':
                result.append(y_position_um)
            elif axis.name == 'x':
                result.append(x_position_um)
            else:
                result.append(axis.position_um)
        return tuple(result)

    def get_nearest_position_in_range(self, z_position_um: float = None,
                                      y_position_um: float = None, x_position_um: float = None):
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
        ordered_position = self.get_zyx_position_in_axes_order(z_position_um, y_position_um, x_position_um)
        return [get_nearest_position_in_range(axis, position)
                for axis, position in zip(self.axes, ordered_position)]

    def wait_until_stopped(self, timeout_ms: float = 10000):
        '''Wait until stage is not moving anymore.'''
        start_time = time.time()
        while self.is_moving:
            if time.time() - start_time > timeout_ms / 1000:
                return False
        return True

    def _update_axis_positions(self, axis_names: List[str], positions: List[float]):
        for name, position in zip(axis_names, positions):
            self.axes_dict[name].position_um = position
