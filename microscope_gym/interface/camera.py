'''Camera interface for microscope_gym.'''

from abc import ABC, abstractmethod


class Camera(ABC):
    '''Camera interface class.

    methods:
        capture_image()
        configure_camera(settings)

    properties:
        pixel_size(): float
            pixel size in µm
        settings(): dict
            camera settings
    '''

    @abstractmethod
    def capture_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    @abstractmethod
    def configure_camera(self, settings: "dict"):
        '''Configure camera settings.'''
        pass

    @property
    @abstractmethod
    def pixel_size(self) -> "float":
        '''Get pixel size in µm.'''
        pass

    @property
    @abstractmethod
    def width(self) -> "int":
        '''Get camera width in pixels.'''
        pass

    @property
    @abstractmethod
    def height(self) -> "int":
        '''Get camera height in pixels.'''
        pass

    @property
    @abstractmethod
    def settings(self) -> "dict":
        '''Get camera settings.'''
        pass
