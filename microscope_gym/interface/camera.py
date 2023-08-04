'''Camera interface for microscope_gym.'''
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class CameraSettings(BaseModel):
    pixel_size_um: float = Field(..., ge=0.0, description="physical pixel size of camera chip in µm")
    width_pixels: int = Field(..., ge=0, description="width of camera chip in pixels")
    height_pixels: int = Field(..., ge=0, description="height of camera chip in pixels")
    exposure_time_ms: float = Field(100.0, ge=0.0)
    gain: float = Field(0.0, ge=0.0, description="amplifier gain")

    class Config:
        validate_assignment = True


class Camera(ABC):
    '''Camera interface class.

    methods:
        capture_image()
        configure_camera(settings)

    properties:
        pixel_size_um: float
            pixel size in µm
        width_pixels: int
            camera width in pixels
        height_pixels: int
            camera height in pixels
        image_shape: tuple
            camera image shape (height, width) TODO: implement as getter
        settings: CameraSettings
            vendor-specific camera settings for example: {"exposure_time_ms": 100, "gain": 0}
    '''
    @property
    def pixel_size_um(self):
        return self.settings.pixel_size_um

    @property
    def width_pixels(self):
        return self.settings.width_pixels

    @property
    def height_pixels(self):
        return self.settings.height_pixels

    @property
    def image_shape(self):
        return (self.height_pixels, self.width_pixels)

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self.configure_camera(value)

    def take_snapshot(self) -> "numpy.ndarray":  # type: ignore
        return self.capture_image()

    @abstractmethod
    def capture_image(self) -> "numpy.ndarray":  # type: ignore
        '''Acquire new image.'''
        pass

    @abstractmethod
    def configure_camera(self, settings: CameraSettings) -> None:
        '''Configure camera settings.'''
        pass
