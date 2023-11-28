from typing import List
from pydantic import create_model
import numpy as np
import time
from microscope_gym import interface
from microscope_gym.interface import Objective, CameraSettings


class Axis(interface.stage.Axis):
    last_move_time:float = -1.0
    move_timeout:float = 0.001


class Stage(interface.Stage):
    '''Stage class.

    methods:
        move_x_to(absolute_x_position_um)
        move_x_by(relative_x_position_um)
        move_y_to(absolute_y_position_um)
        move_y_by(relative_y_position_um)
        move_z_to(absolute_z_position_um)
        move_z_by(relative_z_position_um)

    properties:
        z_position_um(): float
            z position in µm
        y_position_um(): float
            y position in µm
        x_position_um(): float
            x position in µm
        z_range(): tuple
            z range in µm
        y_range(): tuple
            y range in µm
        x_range(): tuple
            x range in µm
    '''

    def is_moving(self):
        now = time.time()
        return any([(now - axis.last_move_time) < axis.move_timeout for axis in self.axes.values()])

    def _update_axes_positions(self, axis_names: List[str], positions: List[float]):
        super()._update_axes_positions(axis_names, positions)
        now = time.time()
        for axis_name in axis_names:
            self.axes[axis_name].last_move_time = now


class Camera(interface.Camera):
    '''Camera class.

    methods:
        capture_image(z, y, x): numpy.ndarray
            Capture image at z, y, x position in µm. z, y, x are the position of the top left corner of the image.
        configure_camera(settings): None
            Configure camera settings.

    properties:
        pixel_size_um: float
            Pixel size in µm.
        height_pixels: int
            Height of camera chip in pixels.
        width_pixels: int
            Width of camera chip in pixels.
        settings: interface.CameraSettings
            Camera settings.
        overview_image(): numpy.ndarray
            Overview image of the sample. In order to conform with the image dimensions commonly used in microscopy, the overview image should be a 3D array with dimensions (z, y, x).
    '''

    def __init__(self, settings: interface.CameraSettings, overview_image, stage: Stage):
        self._settings = settings
        self.overview_image = overview_image
        self.stage = stage

    def capture_image(self) -> np.ndarray:
        '''Capture image the current stage position.'''
        z, y, x = self.stage.z_position_um, self.stage.y_position_um, self.stage.x_position_um
        y_offset = self.height_pixels / 2
        x_offset = self.width_pixels / 2
        return self.overview_image[int(z), int(y - y_offset):int(y + y_offset), int(x - x_offset):int(x + x_offset)]

    def configure_camera(self, settings: interface.CameraSettings) -> None:
        self._settings = settings


class Microscope(interface.Microscope):
    '''Microscope class.

    methods:
        move_stage(z, y, x)
        capture_image()
        get_metadata()

    properties:
        camera(): Camera object
        stage(): Stage object
        objective(): Objective object
    '''

    def get_metadata(self):
        '''Get metadata of the microscope.

        In the future this should be OME compliant.'''
        sample_pixel_size = self.get_sample_pixel_size_um()
        width_um = self.camera.width_pixels * sample_pixel_size
        height_um = self.camera.height_pixels * sample_pixel_size
        return {
            'camera': {
                'pixel_size': self.camera.pixel_size_um,
                'width': self.camera.width_pixels,
                'height': self.camera.height_pixels,
                'settings': self.camera.settings,
                'image_shape': self.camera.image_shape
            },
            'stage': {
                'x_range': self.stage.x_range,
                'y_range': self.stage.y_range,
                'z_range': self.stage.z_range
            },
            'objective': {
                'magnification': self.objective.magnification,
                'working_distance': self.objective.working_distance,
                'numerical_aperture': self.objective.numerical_aperture,
                'immersion': self.objective.immersion
            },
            'sample_dimensions': {
                'pixel_size_um': sample_pixel_size,
                'width_um': width_um,
                'height_um': height_um,
                'field_of_view_um': (height_um, width_um),
            }
        }

    def acquire_overview_image(self):
        return self.camera.overview_image


def microscope_factory(overview_image=np.random.normal(size=(10, 1024, 1024)), camera_pixel_size=1, camera_height_pixels=512, camera_width_pixels=512, settings={},
                       objective_magnification=1, objective_working_distance=0.29, objective_numerical_aperture=0.95, objective_immersion="air"):
    '''Create a microscope object.

    Args:
        pixel_size: float
            pixel size in µm
        camera_height_pixels: int
            number of pixels in height
        camera_width_pixels: int
            number of pixels in width
        settings: dict
            camera settings
        overview_image: np.ndarray
            overview image
    '''

    # makes sure that the overview image has at least 3 dimensions
    while overview_image.ndim < 3:
        overview_image = np.expand_dims(overview_image, axis=0)

    # set up the microscope components
    y_offset = int(camera_height_pixels / 2)
    x_offset = int(camera_width_pixels / 2)
    z_range = (0, overview_image.shape[0])
    y_range = (y_offset, overview_image.shape[1] - y_offset)
    x_range = (x_offset, overview_image.shape[2] - x_offset)
    z_position_um = int((z_range[1] - z_range[0]) / 2)
    y_position_um = int((y_range[1] - y_range[0]) / 2)
    x_position_um = int((x_range[1] - x_range[0]) / 2)

    axes = [Axis(name='z', position_um=z_position_um, min=z_range[0], max=z_range[1]),
            Axis(name='y', position_um=y_position_um, min=y_range[0], max=y_range[1]),
            Axis(name='x', position_um=x_position_um, min=x_range[0], max=x_range[1])]
    stage = Stage(axes)
    camera_settings = CameraSettings(
        pixel_size_um=camera_pixel_size,
        height_pixels=camera_height_pixels,
        width_pixels=camera_width_pixels)
    camera = Camera(camera_settings, overview_image, stage)
    objective = Objective(
        name=f"{objective_magnification}x {objective_immersion}",
        magnification=objective_magnification,
        working_distance=objective_working_distance,
        numerical_aperture=objective_numerical_aperture,
        immersion=objective_immersion)
    return Microscope(camera, stage, objective)
