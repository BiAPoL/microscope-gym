import numpy as np
from microscope_gym import interface


class Camera(interface.Camera):
    def __init__(self, pixel_size, height, width, settings, overview_image):
        self.pixel_size = pixel_size
        self.height = height
        self.width = width
        self.settings = settings
        self.overview_image = overview_image

    def capture_image(self, x, y, z):
        return self.overview_image[int(z), int(y):int(y) + self.height, int(x):int(x) + self.width]

    def configure_camera(self, settings):
        self.settings = settings


class Stage(interface.Stage):
    '''Stage class.

    methods:
        move_x_to(absolute_x_position)
        move_x_by(relative_x_position)
        move_y_to(absolute_y_position)
        move_y_by(relative_y_position)
        move_z_to(absolute_z_position)
        move_z_by(relative_z_position)

    properties:
        x_position(): float
            x position in µm
        y_position(): float
            y position in µm
        z_position(): float
            z position in µm
        x_range(): tuple
            x range in µm
        y_range(): tuple
            y range in µm
        z_range(): tuple
            z range in µm
    '''

    def __init__(self, x_range: tuple, y_range: tuple, z_range: tuple):
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.x_position = (x_range[1] - x_range[0]) / 2
        self.y_position = (y_range[1] - y_range[0]) / 2
        self.z_position = (z_range[1] - z_range[0]) / 2

    def move_x_to(self, absolute_x_position: float):
        if absolute_x_position < self.x_range[0] or absolute_x_position > self.x_range[1]:
            raise ValueError("X position out of range.")
        self.x_position = absolute_x_position

    def move_x_by(self, relative_x_position: float):
        if self.x_position + relative_x_position < self.x_range[0] \
                or self.x_position + relative_x_position > self.x_range[1]:
            raise ValueError("X position out of range.")
        self.x_position += relative_x_position

    def move_y_to(self, absolute_y_position: float):
        if absolute_y_position < self.y_range[0] or absolute_y_position > self.y_range[1]:
            raise ValueError("Y position out of range.")
        self.y_position = absolute_y_position

    def move_y_by(self, relative_y_position: float):
        if self.y_position + relative_y_position < self.y_range[0] \
                or self.y_position + relative_y_position > self.y_range[1]:
            raise ValueError("Y position out of range.")
        self.y_position += relative_y_position

    def move_z_to(self, absolute_z_position: float):
        if absolute_z_position < self.z_range[0] or absolute_z_position > self.z_range[1]:
            raise ValueError("Z position out of range.")
        self.z_position = absolute_z_position

    def move_z_by(self, relative_z_position: float):
        if self.z_position + relative_z_position < self.z_range[0] \
                or self.z_position + relative_z_position > self.z_range[1]:
            raise ValueError("Z position out of range.")
        self.z_position += relative_z_position


class Objective(interface.Objective):
    '''Objective class.

    properties:
        magnification: float
            magnification
        working_distance: float
            working distance in µm
        numerical_aperture: float
            numerical aperture
        immersion: str
            immersion medium
    '''

    def __init__(self, magnification: float, working_distance: float, numerical_aperture: float, immersion: str):
        self.magnification = magnification
        self.working_distance = working_distance
        self.numerical_aperture = numerical_aperture
        self.immersion = immersion


class Microscope(interface.Microscope):
    '''Microscope class.

    methods:
        move_stage(x, y, z)
        capture_image()
        get_metadata()

    properties:
        camera: camera object
        stage: stage object
    '''

    def __init__(self, camera: Camera, stage: Stage, objective: Objective):
        self.camera = camera
        self.stage = stage
        self.objective = objective

    def move_stage_to(self, absolute_x_position=None, absolute_y_position=None, absolute_z_position=None):
        if absolute_x_position is not None:
            self.stage.move_x_to(absolute_x_position)
        if absolute_y_position is not None:
            self.stage.move_y_to(absolute_y_position)
        if absolute_z_position is not None:
            self.stage.move_z_to(absolute_z_position)

    def move_stage_by(self, relative_x_position=None, relative_y_position=None, relative_z_position=None):
        if relative_x_position is not None:
            self.stage.move_x_by(relative_x_position)
        if relative_y_position is not None:
            self.stage.move_y_by(relative_y_position)
        if relative_z_position is not None:
            self.stage.move_z_by(relative_z_position)

    def capture_image(self):
        return self.camera.capture_image(self.stage.x_position, self.stage.y_position, self.stage.z_position)

    def get_metadata(self):
        return {
            'camera': {
                'pixel_size': self.camera.pixel_size,
                'width': self.camera.width,
                'height': self.camera.height,
                'settings': self.camera.settings
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
                'pixel_size': self.camera.pixel_size / self.objective.magnification,
                'width': self.camera.width * self.camera.pixel_size / self.objective.magnification,
                'height': self.camera.height * self.camera.pixel_size / self.objective.magnification
            }
        }


def microscope_factory(overview_image=np.random.normal(size=(10, 1024, 1024)), camera_pixel_size=6.5, camera_height_pixels=512, camera_width_pixels=512, settings={},
                       objective_magnification=40.0, objective_working_distance=0.29, objective_numerical_aperture=0.95, objective_immersion="air"):
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

    camera = Camera(camera_pixel_size, camera_height_pixels, camera_width_pixels, settings, overview_image)
    stage = Stage((0, overview_image.shape[2]), (0, overview_image.shape[1]), (0, overview_image.shape[0]))
    objective = Objective(
        objective_magnification,
        objective_working_distance,
        objective_numerical_aperture,
        objective_immersion)
    return Microscope(camera, stage, objective)
