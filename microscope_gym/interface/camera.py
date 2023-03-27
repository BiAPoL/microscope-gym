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
            camera settings
        image_shape(): tuple
            camera image shape
    '''

    @abstractmethod
    def capture_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    @abstractmethod
    def configure_camera(self, settings: "dict"):
        '''Configure camera settings.'''
        pass
