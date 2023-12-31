import pytest
import numpy as np
from microscope_gym import interface
from microscope_gym.mock_scope import Camera, Stage, Objective, Microscope, microscope_factory


# Camera tests
def test_camera_capture_image():
    settings = {"exposure_time": 100}
    overview_image = np.random.rand(10, 20, 30)
    camera = Camera(pixel_size=1, height_pixels=5, width_pixels=2, settings=settings, overview_image=overview_image)
    image_slice = camera.capture_image(x=5, y=5, z=5)
    assert image_slice.shape == (5, 2)
    np.testing.assert_array_equal(image_slice, overview_image[5, 5:10, 5:7])


def test_camera_configure_camera():
    settings = {"exposure_time": 100}
    overview_image = np.random.rand(10, 20, 30)
    camera = Camera(pixel_size=1, height_pixels=20, width_pixels=10, settings=settings, overview_image=overview_image)
    new_settings = {"exposure_time": 200}
    camera.configure_camera(settings=new_settings)
    assert camera.settings == new_settings
    assert isinstance(camera, interface.Camera)


# Stage tests
def test_stage_constructor():
    stage = Stage((0, 10), (0, 20), (0, 30))
    assert stage.x_range == (0, 10)
    assert stage.y_range == (0, 20)
    assert stage.z_range == (0, 30)
    assert stage.x_position == 5
    assert stage.y_position == 10
    assert stage.z_position == 15
    assert isinstance(stage, interface.Stage)


def test_stage_move_x_to():
    stage = Stage((0, 10), (0, 20), (0, 30))
    stage.move_x_to(5)
    assert stage.x_position == 5


def test_stage_move_y_to():
    stage = Stage((0, 10), (0, 20), (0, 30))
    stage.move_y_to(15)
    assert stage.y_position == 15


def test_stage_move_z_to():
    stage = Stage((0, 10), (0, 20), (0, 30))
    stage.move_z_to(25)
    assert stage.z_position == 25


# Objective tests
def test_objective_constructor():
    objective = Objective(magnification=40, working_distance=5, numerical_aperture=0.95, immersion="oil")
    assert objective.magnification == 40
    assert objective.working_distance == 5
    assert objective.numerical_aperture == 0.95
    assert objective.immersion == "oil"
    assert isinstance(objective, interface.Objective)


# Microscope tests
# Sample input for testing
pixel_size = 0.1
camera_height_pixels = 20
camera_width_pixels = 40
settings = {}
overview_image = np.random.normal(size=(10, 100, 200))
magnification = 40
working_distance = 5
numerical_aperture = 0.95
immersion = "oil"


# microscope_factory tests
def test_microscope_factory():
    # create microscope object using factory function
    microscope = microscope_factory(
        overview_image,
        pixel_size,
        camera_height_pixels,
        camera_width_pixels,
        settings,
        magnification,
        working_distance,
        numerical_aperture,
        immersion)

    # assert that object is an instance of Microscope class
    assert isinstance(microscope, interface.Microscope)

    # assert that object has a Camera and Stage attribute
    assert hasattr(microscope, 'camera')
    assert isinstance(microscope.camera, interface.Camera)
    assert hasattr(microscope, 'stage')
    assert isinstance(microscope.stage, interface.Stage)

    # assert that Camera object is correctly initialized
    assert microscope.camera.pixel_size_um == pixel_size
    assert microscope.camera.height_pixels == camera_height_pixels
    assert microscope.camera.width_pixels == camera_width_pixels
    assert microscope.camera.settings == settings
    np.testing.assert_array_equal(microscope.camera.overview_image, overview_image)

    # assert that Stage object is correctly initialized
    np.testing.assert_array_equal(microscope.stage.x_range, [0, 159])
    np.testing.assert_array_equal(microscope.stage.y_range, [0, 79])
    np.testing.assert_array_equal(microscope.stage.z_range, [0, 9])
    assert microscope.stage.x_position == 79.5
    assert microscope.stage.y_position == 39.5
    assert microscope.stage.z_position == 4.5

    # assert that Microscope object can capture an image without errors
    img = microscope.acquire_image()
    assert img.shape == (camera_height_pixels, camera_width_pixels)


# Microscope class tests
def test_microscope_constructor():
    # Test that an instance of Microscope can be created with valid input
    camera = Camera(pixel_size, camera_height_pixels, camera_width_pixels, settings, overview_image)
    stage = Stage((0, overview_image.shape[2]), (0, overview_image.shape[1]), (0, overview_image.shape[0]))
    objective = Objective(40, 0.14, 0.95, 'water')
    microscope = Microscope(camera, stage, objective)

    assert isinstance(microscope, interface.Microscope)
    assert isinstance(microscope.camera, interface.Camera)
    assert isinstance(microscope.stage, interface.Stage)
    assert isinstance(microscope.objective, interface.Objective)


@ pytest.fixture
def microscope():
    microscope = microscope_factory(
        overview_image,
        pixel_size,
        camera_height_pixels,
        camera_width_pixels,
        settings,
        magnification,
        working_distance,
        numerical_aperture,
        immersion)
    return microscope


def test_microscope_acquire_image(microscope):
    # Move the stage to a specific position
    microscope.move_stage_to(50, 40, 5)

    # Capture an image and check that it has the expected shape
    img = microscope.acquire_image()
    assert img.shape == (camera_height_pixels, camera_width_pixels)

    # Check that the image was taken at the correct position
    np.testing.assert_array_equal(
        img, overview_image[5, 40:40 + camera_height_pixels, 50:50 + camera_width_pixels])


def test_microscope_acquire_z_stack(microscope):
    # Move the stage to a specific position
    microscope.move_stage_to(50, 40, 5)
    z_pos = microscope.stage.z_position

    # Capture a z-stack and check that it has the expected shape
    z_stack = microscope.acquire_z_stack(z_range=(1, 5), z_step=1)
    assert z_stack.shape == (4, camera_height_pixels, camera_width_pixels)

    # Check that the z-stack was taken at the correct position
    np.testing.assert_array_equal(z_stack,
                                  overview_image[1:5,
                                                 40:40 + camera_height_pixels,
                                                 50:50 + camera_width_pixels])

    # Check that the z-position of the stage is unchanged
    assert microscope.stage.z_position == z_pos


def test_microscope_get_metadata(microscope):
    metadata = microscope.get_metadata()

    # Check that the metadata contains the expected properties
    assert set(metadata.keys()) == {'camera', 'stage', 'objective', 'sample_dimensions'}
    assert set(metadata['camera'].keys()) == {'pixel_size', 'width', 'height', 'settings'}
    assert set(metadata['stage'].keys()) == {'x_range', 'y_range', 'z_range'}
    assert set(metadata['objective'].keys()) == {'magnification', 'working_distance', 'numerical_aperture', 'immersion'}
    assert set(metadata['sample_dimensions'].keys()) == {'pixel_size', 'width', 'height'}


def test_microscope_move_stage_to(microscope):
    # Move the stage to a specific position
    microscope.move_stage_to(50, 50, 5)
    x_pos, y_pos, z_pos = microscope.stage.x_position, microscope.stage.y_position, microscope.stage.z_position

    # Check that the stage was moved to the correct position
    assert x_pos == 50
    assert y_pos == 50
    assert z_pos == 5


def test_microscope_move_stage_by(microscope):
    # record the starting position of the stage
    x_pos_start = microscope.stage.x_position
    y_pos_start = microscope.stage.y_position
    z_pos_start = microscope.stage.z_position

    # Move the stage by a relative distance
    microscope.move_stage_by(10, 10, 2)

    # Check that the stage was moved to the correct position
    assert microscope.stage.x_position == x_pos_start + 10
    assert microscope.stage.y_position == y_pos_start + 10
    assert microscope.stage.z_position == z_pos_start + 2
