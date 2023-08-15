import os.path
from collections import OrderedDict
from typing import List
from pathlib import Path
# from pycromanager import Core
# [Jamie] I think this should be pymmcore_plus, not pycromanager
# pycromanager interfaces with the jova objects in the gui
# pymmcore(_plus) interface directly with the microscope devices
# defined by the configuration file
# the goal should be to translate a micromanager .cfg file into a microscope-gym adapter
# would it be better to just access micromanager directly from the smart module??

from pymmcore_plus import CMMCorePlus, Device, find_micromanager
from microscope_gym import interface
from microscope_gym.interface import Objective, Microscope, Axis, Camera


class Stage(interface.Stage):
    def __init__(self, mm_core: CMMCorePlus) -> None:
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
    def __init__(self, mm_core: CMMCorePlus, save_path: str = '', micromanager_path: str = '/Applications/Micro-Manager', config_file: str = 'MMConfig_demo.cfg' ) -> None:
        self.microscope_handler = mm_core
        if save_path == '':
            import tempfile
            self.save_path = Path(tempfile.mkdtemp)
        else:
            self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True, parents=True)
        if find_micromanager() == '':
            raise Exception('Micro-manager installation not found or environment variable not set.')
        else:
            self.micromanager_path = find_micromanager()
        config_path = os.path.join(mm_dir, config_file)
        if not Path(config_path):
            raise Exception(f'Configuration file {config_file} not found in folder {micromanager_path}.')
        else:
            print(f'Loading configuration file {config_path}.')
            self.microscope_handler.loadSystemConfiguration()

    def capture_image(self) -> "numpy.ndarray":

        # mmc.snap can take a channel as a parameter (for multi-channel cameras)

        """
        Trigger the Snap function from MicroManager and get the data

        **from mmcore docs**

        Signature: `mmc.snap(numChannel: 'int | None' = None, *, fix: 'bool' = True) -> 'np.ndarray'`

        Source:
        def snap(self, numChannel: int | None = None, *, fix: bool = True) -> np.ndarray:

        Snap and return an image.

        :sparkles: *This method is new in `CMMCorePlus`.*

        Convenience for calling `self.snapImage()` followed by returning the value
        of `self.getImage()`.

        Parameters
        ----------
        numChannel : int, optional
            The camera channel to get the image from.  If None, (the default), then
            Multi-Channel cameras will return the content of the first channel.
        fix : bool, default: True
            If `True` (the default), then images with n_components > 1 (like RGB images)
            will be reshaped to (w, h, n_components) using `fixImage`.

        Returns
        -------
        img : np.ndarray

        Example from pymmcore-plus
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.snapImage()
        img = self.getImage(numChannel, fix=fix)  # type: ignore
        self.events.imageSnapped.emit(img)
        return img

        """
        return self.microscope_handler.snap()