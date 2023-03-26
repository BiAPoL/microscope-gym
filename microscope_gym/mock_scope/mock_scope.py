import numpy as np
from microscope_gym import interface


class Camera(interface.Camera):
    '''Camera class.

    methods:
        capture_image(x, y, z): numpy.ndarray
            Capture image at x, y, z position in µm. x, y, z are the position of the top left corner of the image.
        configure_camera(settings): None
            Configure camera settings.

    properties:
        pixel_size(): float
            Pixel size in µm.
        height_pixels(): int
            Height ov camera chip in pixels.
        width_pixels(): int
            Width of camera chip in pixels.
        settings(): dict
            Camera settings.
        overview_image(): numpy.ndarray
            Overview image of the sample. In order to conform with the image dimensions commonly used in microscopy, the overview image should be a 3D array with dimensions (z, y, x).
    '''

    def __init__(self, pixel_size, height_pixels, width_pixels, settings, overview_image):
        self.pixel_size = pixel_size
        self.height_pixels = height_pixels
        self.width_pixels = width_pixels
        self.settings = settings
        self.overview_image = overview_image
        self.image_shape = (self.height_pixels, self.width_pixels)

    def capture_image(self, x: float, y: float, z: float) -> np.ndarray:
        '''Capture image at x, y, z position in µm. x, y, z are the position of the top left corner of the image.'''
        return self.overview_image[int(z), int(y):int(y) + self.height_pixels, int(x):int(x) + self.width_pixels]

    def configure_camera(self, settings: dict) -> None:
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
        self._x_position = (x_range[1] - x_range[0]) / 2
        self._y_position = (y_range[1] - y_range[0]) / 2
        self._z_position = (z_range[1] - z_range[0]) / 2

    @property
    def x_position(self):
        return self._x_position

    @x_position.setter
    def x_position(self, value):
        if value < self.x_range[0] or value > self.x_range[1]:
            raise ValueError("X position out of range.")
        self._x_position = value

    @property
    def y_position(self):
        return self._y_position

    @y_position.setter
    def y_position(self, value):
        if value < self.y_range[0] or value > self.y_range[1]:
            raise ValueError("Y position out of range.")
        self._y_position = value

    @property
    def z_position(self):
        return self._z_position

    @z_position.setter
    def z_position(self, value):
        if value < self.z_range[0] or value > self.z_range[1]:
            raise ValueError("Z position out of range.")
        self._z_position = value

    def move_x_to(self, absolute_x_position: float):
        self.x_position = absolute_x_position

    def move_x_by(self, relative_x_position: float):
        self.move_x_to(self.x_position + relative_x_position)

    def move_y_to(self, absolute_y_position: float):
        self.y_position = absolute_y_position

    def move_y_by(self, relative_y_position: float):
        self.move_y_to(self.y_position + relative_y_position)

    def move_z_to(self, absolute_z_position: float):
        self.z_position = absolute_z_position

    def move_z_by(self, relative_z_position: float):
        self.move_z_to(self.z_position + relative_z_position)


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

    def acquire_image(self):
        return self.camera.capture_image(self.stage.x_position, self.stage.y_position, self.stage.z_position)

    def acquire_z_stack(self, z_range: tuple, z_step: float):
        z_position_before = self.stage.z_position
        z_positions = np.arange(z_range[0], z_range[1], z_step)
        images = []
        for z in z_positions:
            self.move_stage_to(absolute_z_position=z)
            images.append(self.acquire_image())
        self.move_stage_to(absolute_z_position=z_position_before)
        return np.asarray(images)

    def acquire_tiled_image(self, x_range: tuple, y_range: tuple, x_step: float = None,
                            y_step: float = None) -> np.ndarray:
        return self._acquire_tiled(x_range, y_range, x_step=x_step, y_step=y_step)

    def acquire_tiled_z_stack(self, x_range: tuple, y_range: tuple, z_range: tuple,
                              x_step: float = None, y_step: float = None, z_step: float = 1.0) -> np.ndarray:
        return self._acquire_tiled(x_range, y_range, z_range, x_step=x_step, y_step=y_step, z_step=z_step)

    def acquire_overview_image(self):
        return self.camera.overview_image

    def get_metadata(self):
        sample_pixel_size = self.camera.pixel_size / self.objective.magnification
        width_um = self.camera.width_pixels * sample_pixel_size
        height_um = self.camera.height_pixels * sample_pixel_size
        return {
            'camera': {
                'pixel_size': self.camera.pixel_size,
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

    def get_stage_position(self):
        return self.stage.x_position, self.stage.y_position, self.stage.z_position

    def get_sample_pixel_size_um(self):
        return self.camera.pixel_size / self.objective.magnification

    def get_field_of_view_um(self):
        sample_pixel_size = self.get_sample_pixel_size_um
        width_um = self.camera.width_pixels * sample_pixel_size
        height_um = self.camera.height_pixels * sample_pixel_size
        return height_um, width_um

    def scan_stage(self, x_range: tuple, y_range: tuple, x_step: float = None, y_step: float = None):
        field_of_view = self.get_field_of_view_um()
        if y_step is None:
            y_step = field_of_view[0] * 0.9
        if x_step is None:
            x_step = field_of_view[1] * 0.9
        x_steps = np.ceil(x_range[1] - x_range[0] / x_step)
        y_steps = np.ceil(y_range[1] - y_range[0] / y_step)
        x_positions = np.linspace(x_range[0], x_range[1], x_steps)
        y_positions = np.linspace(y_range[0], y_range[1], y_steps)
        all_x_positions, all_y_positions = np.meshgrid(x_positions, y_positions)
        return all_y_positions, all_x_positions

    def _acquire_tiled(self, x_range: tuple, y_range: tuple,
                       z_range: tuple = None, x_step: float = None, y_step: float = None, z_step: float = 1.0) -> np.ndarray:
        x_position_before = self.stage.x_position
        y_position_before = self.stage.y_position
        field_of_view = self.get_field_of_view_um()
        if y_step is None:
            y_step = field_of_view[0] * 0.9
        if x_step is None:
            x_step = field_of_view[1] * 0.9
        if z_range is None:
            image_function = self.acquire_image
        else:
            def image_function(): return self.acquire_z_stack(z_range, z_step)
        x_positions = np.arange(x_range[0], x_range[1], x_step)
        y_positions = np.arange(y_range[0], y_range[1], y_step)
        images = []
        for x in x_positions:
            self.move_stage_to(absolute_x_position=x)
            for y in y_positions:
                self.move_stage_to(absolute_y_position=y)
                images.append(image_function())
        self.move_stage_to(absolute_x_position=x_position_before, absolute_y_position=y_position_before)
        return np.asarray(images)


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

    # makes sure that the overview image has at least 3 dimensions
    while overview_image.ndim < 3:
        overview_image = np.expand_dims(overview_image, axis=0)

    # set up the microscope components
    camera = Camera(camera_pixel_size, camera_height_pixels, camera_width_pixels, settings, overview_image)
    stage = Stage((0, overview_image.shape[2] - camera_width_pixels - 1),
                  (0, overview_image.shape[1] - camera_height_pixels - 1),
                  (0, overview_image.shape[0] - 1))
    objective = Objective(
        objective_magnification,
        objective_working_distance,
        objective_numerical_aperture,
        objective_immersion)
    return Microscope(camera, stage, objective)
