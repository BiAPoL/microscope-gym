'''Camera interface for microscope_gym.'''
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import numpy


class CameraSettings(BaseModel):
    pixel_size_um: float = Field(0.0, ge=0.0)
    width_pixels: int = Field(0, ge=0)
    height_pixels: int = Field(0, ge=0)
    exposure_time_ms: float = Field(100.0, ge=0.0)
    gain: float = Field(0.0, ge=0.0)

    class Config:
        validate_assignment = True

# TODO: refactor Camera class to use CameraSettings


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

    @property
    def camera_settings(self):
        return self._camera_settings

    @camera_settings.setter
    def camera_settings(self, value):
        self.configure_camera(value)

    @abstractmethod
    def capture_image(self) -> "numpy.ndarray":
        '''Acquire new image.'''
        pass

    @abstractmethod
    def configure_camera(self, settings: "dict"):
        '''Configure camera settings.'''
        pass
