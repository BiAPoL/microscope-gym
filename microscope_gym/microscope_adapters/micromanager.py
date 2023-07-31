from collections import OrderedDict
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


class Camera(interface.Camera):
    def __init__(self, mm_core: Core) -> None:
        self.microscope_handler = mm_core

    def capture_image(self) -> "numpy.ndarray":
        # Trigger the Snap funtion from MicroManager and get the data
        pass  # TODO Figure out how to get this from MMCore
