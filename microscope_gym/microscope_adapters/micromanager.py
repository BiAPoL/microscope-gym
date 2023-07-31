from collections import OrderedDict
from typing import List
from pathlib import Path
from pycromanager import Core
from microscope_gym import interface
from microscope_gym.interface import Objective, Microscope, Axis


class Stage(interface.Stage):
    def __init__(self, mm_core: Core) -> None:
        self.microscope_handler = mm_core
        self.axes = OrderedDict()
        self._get_axes_positions_from_microscope()

    def _get_axes_positions_from_microscope(self):
        self.axes["z"] = Axis(name='z',
                              position_um=self.microscope_handler.get_position(),
                              min=-10,  # TODO Figure out how to get this from MMCore
                              max=10)  # TODO Figure out how to get this from MMCore
        self.axes["y"] = Axis(name='y',
                              position_um=self.microscope_handler.get_y_position(),
                              min=-10,  # TODO Figure out how to get this from MMCore
                              max=10)  # TODO Figure out how to get this from MMCore
        self.axes["x"] = Axis(name='x',
                              position_um=self.microscope_handler.get_x_position(),
                              min=-10,  # TODO Figure out how to get this from MMCore
                              max=10)  # TODO Figure out how to get this from MMCore

    def is_moving(self):
        focus_device_name = self.microscope_handler.get_focus_device()
        stage_device_name = self.microscope_handler.get_xy_stage_device()

        return self.microscope_handler.device_busy(
            focus_device_name) or self.microscope_handler.device_busy(stage_device_name)

    def _update_axes_positions(self, axis_names: List[str], positions: List[float]):
        '''Write new positions to axes.

        Position validation is done in Axis model.

        Parameters:
            axis_names: list[str]
                list of axis names
            positions: list[float]
                list of new positions (in um)
        '''
        for name, position in zip(axis_names, positions):
            self.axes[name].position_um = position
        self.microscope_handler.set_xy_position(self.axes['x'].position_um, self.axes['y'].position_um)
        self.microscope_handler.set_position(self.axes['z'].position_um)


class Camera(interface.Camera):
    def __init__(self, mm_core: Core, save_path: str = '') -> None:
        self.microscope_handler = mm_core
        if save_path == '':
            import tempfile
            self.save_path = Path(tempfile.mkdtemp)
        else:
            self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True, parents=True)

    def capture_image(self) -> "numpy.ndarray":
        # Trigger the Snap funtion from MicroManager and get the data
        pass  # TODO Figure out how to get this from MMCore
