import os.path
from collections import OrderedDict
from typing import List
from pathlib import Path
from warnings import warn
# from pycromanager import Core
# [Jamie] I think this should be pymmcore_plus, not pycromanager
# pycromanager interfaces with the jova objects in the gui
# pymmcore(_plus) interface directly with the microscope devices
# defined by the configuration file
# the goal should be to translate a micromanager .cfg file into a microscope-gym adapter
# would it be better to just access micromanager directly from the smart module??

from pymmcore_plus import CMMCorePlus, Device, find_micromanager
from microscope_gym import interface
from microscope_gym.interface import Objective, Microscope, Axis, Camera, CameraSettings


class Stage(interface.Stage):
    def __init__(self, mm_core: CMMCorePlus) -> None:
        self.microscope_handler = mm_core
        self.axes = OrderedDict()
        self._get_axes_positions_from_microscope()

    def _get_axes_positions_from_microscope(self):
        # Todo: limits. There is no general way to get the X and Y limits for a particular stage from mmcore.
        self.axes["z"] = Axis(name='z',
                              position_um=self.microscope_handler.getZPosition(),
                              min=-10,  # TODO Figure out how to get this from MMCore
                              max=10)  # TODO Figure out how to get this from MMCore
        self.axes["y"] = Axis(name='y',
                              position_um=self.microscope_handler.getYPosition(),
                              min=-10,  # TODO Figure out how to get this from MMCore
                              max=10)  # TODO Figure out how to get this from MMCore
        self.axes["x"] = Axis(name='x',
                              position_um=self.microscope_handler.getXPosition(),
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


# assume only one camera per microscope for now
class Camera(interface.Camera):
    def __init__(self, mm_core: CMMCorePlus, save_path: str = '',
                 micromanager_path: str = '/Applications/Micro-Manager', config_file: str = 'MMConfig_demo.cfg',
                 pixel_size_um=None) -> None:
        self.microscope_handler = mm_core
        # if save_path == '':
        #     import tempfile
        #     self.save_path = Path(tempfile.mkdtemp)
        # else:
        #     self.save_path = Path(save_path)
        # self.save_path.mkdir(exist_ok=True, parents=True)
        # self.micromanager_path = find_micromanager()
        # # use assertion?
        # # why would we not?  There was a reason. What was it??
        # if self.micromanager_path == '':
        #     raise Exception('Micro-manager installation not found or environment variable not set.')
        # config_path = os.path.join(mm_dir, config_file)
        # if not Path(config_path):
        #     raise Exception(f'Configuration file {config_file} not found in folder {self.micromanager_path}.')
        # else:
        #     print(f'Loading configuration file {config_path}.')
        #     self.microscope_handler.loadSystemConfiguration()
        self.microscope_handler.loadSystemConfiguration()

        self.camera_device = Device(
            self.microscope_handler.getCameraDevice(),
            self.microscope_handler
        )
        self._settings = CameraSettings(
            pixel_size_um=self.microscope_handler.getPixelSizeUm(),
            width_pixels=self.camera_device.getPropertyObject(
                'OnCameraCCDXSize').value,
            height_pixels=self.camera_device.getPropertyObject(
                'OnCameraCCDYSize').value,
            exposure_time_ms=self.camera_device.getPropertyObject(
                'Exposure').value,
            gain=self.camera_device.getPropertyObject(
                'Gain').value
        )
        # assert self.settings.pixel_size_um !=0 and self.settings.pixel_size_um !=1, f"Pixel size is set to {pixel_size}; it is likely not set or calibrated."
        if self._settings.pixel_size_um == 0 or self._settings.pixel_size_um == 1:
            warn(f'Pixel size is set to {self._settings.pixel_size_um}; it may not be set or calibrated.')

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

    # todo: use a logger -> make issue

    def configure_camera(self, settings: CameraSettings) -> None:
        '''
        Configure camera settings.

        from pymmcore-plus source code:

        @synchronized(_lock)
        def setProperty(self,
                label: str,
                propName: str,
                propValue: bool | float | int | str) -> None
        '''

        # Micromanager sets different pixel sizes for a configuration using a resolutionID
        # set the current pixel size (they should all be set in the MM configuration file)
        # self.microscope_handler.setPixelSizeUm(
        #     resolutionID=self.microscope_handler.getCurrentPixelSizeConfig(),
        #     pixSize=settings.pixel_size_um
        # ),
        # # using luxendo code as a hint...
        # self.microscope_handler.setProperty(
        #     self.camera_device.label,
        #     'OnCameraCCDXSize',
        #     settings.width_pixels
        # )
        # self.microscope_handler.setProperty(
        #     self.camera_device.label,
        #     'OnCameraCCDYSize',
        #     settings.height_pixels
        # )
        self.microscope_handler.setProperty(
            self.camera_device.label,
            'Exposure',
            settings.exposure_time_ms
        )
        self.microscope_handler.setProperty(
            self.camera_device.label,
            'Gain',
            settings.gain
        )
        # save the settings in the Camera object
        # self._settings = settings
        self._settings.exposure_time_ms = settings.gain
        self._settings.gain = settings.gain

        return
