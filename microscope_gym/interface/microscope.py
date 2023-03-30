'''Microscope interface for microscope_gym.

TODO: consider using pydantic for validation'''


from abc import ABC, abstractmethod
import numpy as np
from .camera import Camera
from .stage import Stage
from .objective import Objective


class Microscope(ABC):
    '''Base microscope class.

    methods:
        move_stage(x, y)
        capture_image()
        acquire_z_stack()
        get_metadata()
        get_stage_position()

    properties:
        camera(): Camera object
        stage(): Stage object
        objective(): Objective object
    '''

    def __init__(self, camera: Camera, stage: Stage,
                 objective: Objective):
        self.camera = camera
        self.stage = stage
        self.objective = objective

    @abstractmethod
    def move_stage_to(self, z: float, y: float, x: float):
        '''Move stage to absolute z, y, x position in µm.'''
        pass

    @abstractmethod
    def move_stage_by(self, z: float, y: float, x: float):
        '''Move stage by relative z, y, x position in µm.'''
        pass

    def get_nearest_position_in_range(self, z_position: float = None,
                                      y_position: float = None, x_position: float = None):
        '''Return nearest safe position to given position.

        Parameters
        ----------
        position: tuple
            position to check

        Returns
        -------
        tuple
            nearest safe position
        '''
        if z_position is None:
            z_position = self.stage.z_position
        if y_position is None:
            y_position = self.stage.y_position
        if x_position is None:
            x_position = self.stage.x_position
        return (max(self.stage.z_range[0], min(z_position, self.stage.z_range[1])),
                max(self.stage.y_range[0], min(y_position, self.stage.y_range[1])),
                max(self.stage.x_range[0], min(x_position, self.stage.x_range[1])))

    def scan_stage_positions(self, y_range: tuple = (), x_range: tuple = ()):
        '''Scan stage across ranges of the sample given in µm.

        Args:
            y_range (start in µm, stop in µm, step in µm):
                range of y positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 90 % of the height of the camera field of view.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage y range.
                If the tuple is empty, the entire Stage.y_range is used.
            x_range (start in µm, stop in µm, step in µm):
                range of x positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 90 % of the width of the camera field of view.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage x range.
                If the tuple is empty, the entire Stage.x_range is used.
        '''
        default_step = self.get_field_of_view_um() * 0.9
        y_range = self._set_range(y_range, default_range=self.stage.y_range + (default_step[0],))
        x_range = self._set_range(x_range, default_range=self.stage.x_range + (default_step[1],))
        x_steps = np.ceil(x_range[1] - x_range[0] / x_range[2])
        y_steps = np.ceil(y_range[1] - y_range[0] / y_range[2])
        x_positions = np.linspace(x_range[0], x_range[1], x_steps)
        y_positions = np.linspace(y_range[0], y_range[1], y_steps)
        all_x_positions, all_y_positions = np.meshgrid(x_positions, y_positions)
        for y, x in zip(all_y_positions.flatten(), all_x_positions.flatten()):
            self.move_stage_to(absolute_y_position=y, absolute_x_position=x)
            yield y, x

    @abstractmethod
    def get_stage_position(self) -> tuple:
        '''Get current stage position in µm. Positions are calculated relative to the center of the field of view.'''
        pass

    @abstractmethod
    def get_sample_pixel_size_um(self) -> float:
        '''Get pixel size in sample space in µm. Calculated from camera pixel size and objective magnification.'''
        pass

    @abstractmethod
    def get_field_of_view_um(self) -> tuple:
        '''Get field of view in µm. calculated from camera pixel size and image dimensions as well as objective magnification.'''
        pass

    @abstractmethod
    def get_metadata(self) -> dict:
        '''Get metadata in OME-XML format.'''
        pass

    @abstractmethod
    def acquire_image(self) -> np.ndarray:
        '''Acquire new image.'''
        pass

    def acquire_z_stack(self, z_range: tuple = ()):
        '''Acquire z-stack.

        Args:
            z_range (start in µm, stop in µm, step in µm):
                range of z positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 1 µm.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage z range.
                If the tuple is empty, the entire Stage.z_range is used.
        '''
        z_position_before = self.stage.z_position
        z_range = self._set_range(z_range, default_range=self.stage.z_range + (1,))
        z_positions = np.arange(z_range[0], z_range[1], z_range[2])
        images = []
        for z in z_positions:
            self.move_stage_to(absolute_z_position=z)
            images.append(self.acquire_image())
        self.move_stage_to(absolute_z_position=z_position_before)
        return np.asarray(images)

    def acquire_tiled_image(self, y_range: tuple, x_range: tuple) -> np.ndarray:
        '''Acquire tiled image.

        Args:
            y_range (start in µm, stop in µm, step in µm):
                range of y positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 90 % of the height of the camera field of view.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage y range.
                If the tuple is empty, the entire Stage.y_range is used.
            x_range (start in µm, stop in µm, step in µm):
                range of x positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 90 % of the width of the camera field of view.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage x range.
                If the tuple is empty, the entire Stage.x_range is used.
        '''
        return self._acquire_tiled(y_range, x_range)

    def acquire_tiled_z_stack(self, z_range: tuple, y_range: tuple, x_range: tuple) -> np.ndarray:
        '''Acquire tiled z-stack.

        Args:
            z_range (start in µm, stop in µm, step in µm):
                range of z positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 1 µm.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage z range.
                If the tuple is empty, the entire Stage.z_range is used.
            y_range (start in µm, stop in µm, step in µm):
                range of y positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 90 % of the height of the camera field of view.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage y range.
                If the tuple is empty, the entire Stage.y_range is used.
            x_range (start in µm, stop in µm, step in µm):
                range of x positions in µm, works like the range(start, stop, step) function argument:
                If step is not given, defaults to 90 % of the width of the camera field of view.
                If stop and step are not given, start is interpreted as the stop argument and start will be the minimum stage x range.
                If the tuple is empty, the entire Stage.x_range is used.
        '''
        return self._acquire_tiled(z_range, y_range, x_range)

    @abstractmethod
    def acquire_overview_image(self) -> np.ndarray:
        '''Acquire overview image that shows a larger part of the sample (often at lower resolution). Depends on the microscope vendor how this is implemented. It is recommended to use acquire_tiled_image instead if the overwiew image is used in an algorithm.'''
        pass

    def _set_range(self, range: tuple, default_range: tuple):
        if len(range) < 1:
            range = default_range
        if len(range) < 2:
            range = (default_range[0], range, default_range[2])
        if len(range) < 3:
            range = range + (default_range[2],)
        return range

    def _acquire_tiled(self, z_range: tuple = (), y_range: tuple = (), x_range: tuple = ()) -> np.ndarray:
        x_position_before = self.stage.x_position
        y_position_before = self.stage.y_position
        if z_range is None:
            image_function = self.acquire_image
        else:
            def image_function(): return self.acquire_z_stack(z_range)
        images = []
        for y, x in self.scan_stage_positions(y_range, x_range):
            images.append(image_function())
        self.move_stage_to(absolute_y_position=y_position_before, absolute_x_position=x_position_before)
        return np.asarray(images)


# make stage position getter and setter
