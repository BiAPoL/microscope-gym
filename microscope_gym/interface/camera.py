'''Camera interface for microscope_gym.'''
from abc import ABC, abstractmethod
import numpy


class Camera(ABC):
    '''Camera interface class.

    methods:
        capture_image()
        configure_camera(settings)

    properties:
        pixel_size(): float
            pixel size in µm
        width(): int
            camera width in pixels
        height(): int
            camera height in pixels
        settings(): dict
            vendor-specific camera settings for example: {"exposure_time_ms": 100, "gain": 0}
        image_shape(): tuple
            camera image shape (height, width) TODO: implement as getter
    '''

    @abstractmethod
    def capture_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    # TODO: add setter for camera settings that calls configure_camera().

    @abstractmethod
    def configure_camera(self, settings: "dict"):
        '''Configure camera settings.'''
        pass
