from collections import OrderedDict
from typing import Optional, List, Tuple, Any
import warnings
from pydantic import Field, validator, BaseModel
from copy import deepcopy
import time
import re
from abc import ABC, abstractmethod
from warnings import warn
import json
import numpy as np
import h5py
from pathlib import Path
from microscope_gym import interface
from microscope_gym.interface import Objective, Microscope


import paho.mqtt.client as mqtt


class LuxendoAPIException(Exception):
    pass


class LuxendoAPIHandler:
    def __init__(self, broker_address: str = "localhost", broker_port: int = 1883,
                 serial_number: str = "", reply_timeout_ms=10000):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.main_topic = serial_number
        self.reply_timeout_ms = reply_timeout_ms

        self.connected = False
        self.waiting_for_reply = False
        self.last_published: str
        self.latest_message: bool
        self.reply_json: dict
        self._publish_time: float
        self.message_callbacks = []

        self.mqtt = mqtt.Client()
        self.subscribed_topics = []

        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_message = self.on_message

    def on_message(self, client, userdata, message):
        # print("Received message: " + message.topic + " " + str(message.payload))
        self.latest_message = message
        self.reply_json = json.loads(message.payload)
        self.waiting_for_reply = False
        for callback in self.message_callbacks:
            callback(self.reply_json)

    def on_connect(self, client, userdata, flags, result_code):
        if result_code == 0:
            print("Connected")
            for topic in self.subscribed_topics:
                self.mqtt.subscribe(topic)

            self.connected = True
        else:
            self.connected = False
            self.close()

    def on_disconnect(self, client, userdata, result_code):
        self.connected = False
        if result_code == 0:
            print("Disonnected")
        else:
            raise LuxendoAPIException(f"Connection to MQTT broker lost unexpectedly. Error code: {result_code}")

    def connect(self):
        self.mqtt.connect(self.broker_address, self.broker_port)
        self.mqtt.loop_start()

    def wait_for_connection(self):
        started = time.time()
        while not self.connected and time.time() - started < self.reply_timeout_ms / 1000.0:
            time.sleep(0.1)
        if not self.connected:
            raise LuxendoAPIException(f"Connection to MQTT broker timed out after {self.reply_timeout_ms / 1000.0} s")

    def ensure_connection(self):
        if not self.connected:
            self.connect()
            self.wait_for_connection()

    def close(self):
        self.mqtt.loop_stop()
        self.mqtt.disconnect()

    def subscribe(self, topic: str, callback=None):
        topic = self.main_topic + '/' + topic
        self.subscribed_topics.append(topic)
        if self.connected:
            self.mqtt.subscribe(topic)
            if callback is not None:
                self.mqtt.message_callback_add(topic, callback)

    def publish(self, topic: str, payload: str):
        self._publish_time = time.time()
        self.last_published = f"topic: {topic}, payload: {payload}"
        self.mqtt.publish(topic, payload)

    def send_command(self, command, subtopic='/gui'):
        self.publish(self.main_topic + subtopic, command)

    def send_command_and_wait_for_reply(self, command, poll_interval_ms=10):
        self.send_command(command)
        return self.wait_for_reply(poll_interval_ms)

    def keep_waiting_for_replies(self, wait_timeout_ms=10000):
        while time.time() - self._publish_time < wait_timeout_ms / 1000.0:
            yield self.wait_for_reply(poll_interval_ms=0.1)

    def wait_for_reply(self, poll_interval_ms=10):
        self.waiting_for_reply = True
        waited = 0
        while self.waiting_for_reply and waited < self.reply_timeout_ms:
            time.sleep(poll_interval_ms / 1000.0)
            waited += poll_interval_ms
            if not self.waiting_for_reply:
                return self.reply_json
        raise LuxendoAPIException(
            f"Timeout ({self.reply_timeout_ms / 1000.0} s) while waiting for reply to command: {self.last_published}")

    def __del__(self):
        self.close()


class APIData(BaseModel):
    device: str
    command: str = "get"


class APICommand(BaseModel):
    type: str = "device"
    data: APIData


class DelCommand(APIData):
    command: str = "del"
    device: str
    name: str


class BaseConfig(ABC):
    '''Base class that gets and sets API configuration data.'''

    def __init__(self, api_handler: LuxendoAPIHandler, main_topic: str,
                 request_command: APICommand, subtopic='/gui') -> None:
        self.data = None
        self.timeout = 10
        self.api_handler = api_handler
        self.main_topic = main_topic
        self.api_handler.ensure_connection()
        self.api_handler.subscribe(self.main_topic, self._update)
        self.subtopic = subtopic
        self.request_command = request_command
        self.waiting_for_data = False
        self.request_configuration()

    def request_configuration(self):
        self._send_command(self.request_command.data)

    def wait_for_reply(self):
        timeout = self.timeout
        while self.waiting_for_data and timeout > 0:
            time.sleep(0.01)
            timeout -= 0.01
        if timeout <= 0:
            raise TimeoutError(f"Timeout waiting for configuration data for {self.__class__.__name__}")

    @abstractmethod
    def _parse_data(self, payload_dict: dict) -> Any:
        pass

    def _update(self, client, userdata, msg):
        payload_dict = json.loads(msg.payload)
        self.data = self._parse_data(payload_dict)
        self.waiting_for_data = False

    def _send_command(self, data: APIData, **kwargs):
        command = self.request_command.copy()
        command.data = data
        self.waiting_for_data = True
        self.api_handler.send_command(command.json(**kwargs), subtopic=self.subtopic)
        self.wait_for_reply()


class ConfigList(BaseConfig):
    '''Get and set device configuration.'''
    device: str
    data_class: APIData
    del_command_class = DelCommand

    def __init__(self, api_handler: LuxendoAPIHandler) -> None:
        super().__init__(api_handler, "embedded/" + self.device, APICommand(type="operation", data=APIData(device=self.device)))

    def add_element(self):
        data = self.request_command.data.copy()
        data.command = "add"
        self._send_command(data)

    def remove_element(self, name: str):
        data = self.del_command_class(name=name, device=self.device)
        self._send_command(data)

    def _parse_data(self, payload_dict: dict):
        return [self.data_class(**device_data) for device_data in payload_dict['data'][self.device]]


class Axis(interface.Axis):
    '''Stage axis data class.

    properties:
        name: str
            name of the axis, e.g. 'x', 'y' or 'z'
        min: float
            minimum position in µm
        max: float
            maximum position in µm
        position_um: float
            position in µm
        target: float
            target position in µm if target and position are different, the stage is moving
        guiName: str
            name of the axis as shown in the GUI
        partOf: str
            name of the device the axis belongs to
        type: str
            type of the axis (linear, rotary, ...)
    '''
    position_um: float = Field(..., alias='value')
    target: float
    guiName: Optional[str]
    partOf: Optional[str]
    type: str = 'linear'

    class Config:
        # important to avoid api errors when the position is outside the allowed
        # range (the microscope will not crash the stage, but the api will raise
        # an error and the stage position will be inconsistent)
        validate_assignment = True


class AxisCommand(APIData):
    command: str = "set"
    axes: list


class Stage(BaseConfig, interface.Stage):
    '''Stage class.

    methods:
        get_nearest_positions_in_range(z_position: float, y_position: float, x_position: float) -> tuple
            get nearest position in range
        wait_until_stopped(timeout_ms: float) -> bool
            wait until stage is stopped, return True if stopped, False if timeout

    properties:
        axes: OrderedDict[Axes]
            list of Axis objects
        position_um: list[float]
            list of positions in um
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

    def __init__(self, api_handler: LuxendoAPIHandler) -> None:
        super().__init__(
            api_handler=api_handler,
            main_topic="embedded/stages",
            request_command=APICommand(
                type="device",
                data=APIData(device="stages")))

    def is_moving(self):
        return any([axis.target != axis.position_um for axis in self.axes.values()])

    def _parse_data(self, payload_dict: dict) -> OrderedDict:
        axes = OrderedDict()
        for axis_data in payload_dict['data']['axes']:
            axis = Axis(**axis_data)
            axes[axis.name] = axis
        if len(axes) > 0:
            self.axes = axes
        return axes

    def _update_axes_positions(self, axis_names: List[str], positions: List[float]):
        for name, position in zip(axis_names, positions):
            self.axes[name].position_um = position
        command = self.request_command.copy()
        command.data = AxisCommand(command="set", device="stages", axes=list(self.axes.values()))
        self.api_handler.send_command(command.json(by_alias=True))

    def _process_stage_reply(self, client, userdata, message):
        payload_dict = json.loads(message.payload)
        axes = OrderedDict()
        for axis_data in payload_dict['data']['axes']:
            axis = Axis(**axis_data)
            axes[axis.name] = axis
        if len(axes) > 0:
            self.axes = axes

    def _get_stage_status(self):
        message = self.api_handler.send_command_and_wait_for_reply(self.default_command.json())
        return message['data']['axes']


class ROIProperty(BaseModel):
    min: int
    max: int
    inc: int
    value: int

    @validator('value', pre=True, always=True)
    @classmethod
    def validate_value(cls, v, values):
        if v < values['min']:
            raise ValueError(f"Value {v} is smaller than min {values['min']}")
        if v > values['max']:
            raise ValueError(f"Value {v} is larger than max {values['max']}")
        if v % values['inc'] != 0:
            raise ValueError(f"Value {v} is not a multiple of increment {values['inc']}")
        return v

    class Config:
        validate_assignment = True


class CameraSettings(BaseModel):
    name: str
    width_props: ROIProperty
    height_props: ROIProperty
    top_props: ROIProperty
    left_props: ROIProperty
    width_pixels: int
    height_pixels: int
    top: int
    left: int
    exposure_time_ms: float = Field(50.0, ge=0.0, alias='exposure')
    delay: float = Field(12.0, ge=12.0)
    pixel_size_um: float = 6.5

    @validator('top')
    @classmethod
    def validate_top(cls, v, values):
        values['top_props'].value = v
        if v + values['height_pixels'] > values['height_props'].max:
            raise ValueError(f"ROI top {v} + height {values['height_pixels']} exceeds max {values['height_props'].max}")
        return int(v)

    @validator('left')
    @classmethod
    def validate_left(cls, v, values):
        values['left_props'].value = v
        if v + values['width_pixels'] > values['width_props'].max:
            raise ValueError(f"ROI left {v} + width {values['width_pixels']} exceeds max {values['width_props'].max}")
        return int(v)

    @validator('width_pixels')
    @classmethod
    def validate_width_pixels(cls, v, values):
        values['width_props'].value = v
        return int(v)

    @validator('height_pixels')
    @classmethod
    def validate_height_pixels(cls, v, values):
        values['height_props'].value = v
        return int(v)

    class Config:
        validate_assignment = True


class ChannelDevice(BaseModel):
    name: str
    type: str
    text: str


class Channel(BaseModel):
    name: str
    description: str = ""
    devices: List[ChannelDevice]


class ChannelConfig(ConfigList):
    '''Get and set channel configuration.'''
    device = "channels"
    data_class = Channel


class StackElement(BaseModel):
    name: str
    start: int
    end: int
    instack: Optional[bool]
    canTile: Optional[bool]


class Stack(BaseModel):
    elements: List[StackElement]
    n: int
    reps: int
    name: str
    ref: Optional[str]
    description: str


class NewStack(APIData, Stack):
    pass


class StackConfig(ConfigList):
    '''Get and set stack configuration.'''
    device: str = "stacks"
    data_class = Stack

    def new_stack_from_stage(self, stage: Stage) -> NewStack:
        stack = NewStack(
            device="stacks",
            command="add",
            elements=[],
            n=1,
            reps=1,
            name=f"stack_{len(self.data)}",
            description="created by Mic Gym API")
        for axis in stage.axes.values():
            stack.elements.append(StackElement(start=axis.position_um, name=axis.name, end=axis.position_um))
        return stack

    def add_element(self, new_stack: NewStack):
        self._send_command(data=new_stack, exclude_unset=True)


class Time(BaseModel):
    h: int
    m: int
    s: int


class Trigger(BaseModel):
    name: str
    type: str = "StartIntervalRepeats"
    start: Time = Time(h=0, m=0, s=0)
    interval: Time = Time(h=0, m=0, s=0)
    reps: int


class Task(BaseModel):
    name: str
    type: str = "StackChannel"
    channel: str = Field(..., description="name of the channel to be used for the task")
    stack: str = Field(..., description="name of the stack to be used for the task")
    configuration: str = "default"
    order: int = 0
    ablation: list = []  # TODO: add ablation model


class Event(BaseModel):
    name: str
    tasks: List[Task]
    triggers: List[Trigger]


class Events(APIData):
    device: str = "events"
    events: List[Event]


class EventCommand(APIData):
    device: str = "events"
    command: str = "addtask"
    event: str = Field(..., description="name of the event to which the task should be added")
    tasks: Optional[List[Task]]
    triggers: Optional[List[Trigger]]
    task: Optional[str]
    trigger: Optional[str]


class EventDelCommand(DelCommand):
    event: str = Field(..., alias="name", description="name of the event from which the task should be deleted")


class EventConfig(ConfigList):
    '''Get and set event configuration.'''
    device: str = "events"
    data_class = Event
    del_command_class = EventDelCommand

    def add_task(self, event_name: str, task: Task):
        command_data = EventCommand(device="events", command="addtask", event=event_name, tasks=[task])
        self._send_command(data=command_data, exclude_unset=True)

    def del_task(self, event_name: str, task_name: str):
        command_data = EventCommand(device="events", command="del", event=event_name, task=task_name)
        self._send_command(data=command_data, exclude_unset=True)

    def add_trigger(self, event_name: str, trigger: Trigger):
        command_data = EventCommand(device="events", command="addtrigger", event=event_name, triggers=[trigger])
        self._send_command(data=command_data, exclude_unset=True)

    def del_trigger(self, event_name: str, trigger_name: str):
        command_data = EventCommand(device="events", command="del", event=event_name, trigger=trigger_name)
        self._send_command(data=command_data, exclude_unset=True)


class FolderChild(BaseModel):
    name: str
    size: float
    mime: str
    type: str
    creationtime: str


class Folder(BaseModel):
    name: str
    path: str
    parent: bool
    children: List[FolderChild]


class DiskMessage(BaseModel):
    command: str
    message: str
    success: bool


class Source(BaseModel):
    name: str
    free: int
    size: int
    speed: float


class Sources(BaseModel):
    options: List[Source]
    value: str


class Disk(APIData):
    device: str = "disk"
    command: str = "set"
    folder: Folder
    message: DiskMessage
    selectedpath: str
    selectedsource: str
    sources: Sources


class DiskCommand(APIData):
    device: str = "disk"
    command: str = "getconfig"
    type: str = "camerasaving"


class DiskConfig(BaseConfig):

    def __init__(self, api_handler: LuxendoAPIHandler):
        super().__init__(
            api_handler,
            main_topic="datahub/directory",
            request_command=APICommand(
                type="device",
                data=DiskCommand()),
            subtopic='/gui/directory')

    def _parse_data(self, payload_dict: dict):
        return Disk(**payload_dict['data'])


class Camera(interface.Camera):
    def __init__(self, api_handler: LuxendoAPIHandler, stage: Stage, stacks: StackConfig, events: EventConfig,
                 channels: ChannelConfig, new_image_timeout_ms=60000):
        self.file_paths = {}
        self.has_new_image = False
        self.current_images = {}
        self.current_metadatas = {}
        self.new_image_timeout_ms = new_image_timeout_ms
        self.metadata = {}
        self.stage = stage
        self.stacks = stacks
        self.events = events
        self.channels = channels
        self.active_channel = "channel_0"
        self.api_handler = api_handler
        self.api_handler.ensure_connection()
        self.api_handler.subscribe("datahub/cameras/#", self._update_camera)
        self.api_handler.subscribe("embedded/cameras", self._update_camera)
        self.api_handler.subscribe("embedded/timings", self._update_exposure_settings)
        self.timings_command = {"type": "device", "data": {"device": "timings", "command": "set"}}
        self.cameras_command = {"type": "device", "data": {"device": "cameras", "command": "setroi"}}
        self.file_command = {
            "type": "device",
            "data": {
                "device": "disk",
                "command": "getconfig",
                "type": "camerasaving"}}
        self.active_channel = "channel_0"
        self.cameras = {}
        self.serial_number_names = {}
        self._get_config()

    def capture_image(self) -> np.ndarray:
        assert len(self.channels.data) > 0, "No channels configured, please configure an imaging channel in LuxControl"
        if len(self.channels.data) > 1:
            warnings.warn(
                f"More than one channel configured, using {self.active_channel}. If you want to use a different channel, please use the set_active_channel property to the name of that channel.")
        self.has_new_image = False
        self._send_capture_command()
        timeout = self.new_image_timeout_ms / 1000.0
        poll_interval = 0.01
        while not self.has_new_image and timeout > 0:
            time.sleep(poll_interval)
            timeout -= poll_interval
        if timeout <= 0:
            raise LuxendoAPIException(f"Timeout ({self.new_image_timeout_ms / 1000.0} s) while waiting for new image")
        # TODO: remoe new stack and experiment settings with current stage position
        self.has_new_image = False
        return self.current_images

    def configure_camera(self, settings: CameraSettings) -> None:
        command = deepcopy(self.timings_command)
        command['data']['timings'] = {}
        command['data']['timings']['exposure'] = settings.exposure_time_ms
        command['data']['timings']['delaybefore'] = 0
        command['data']['timings']['delayafter'] = settings.delay
        self.api_handler.send_command(json.dumps(command))
        command = deepcopy(self.cameras_command)
        command['data']['name'] = settings.name
        command['data']['roi'] = {}
        command['data']['roi']['top'] = settings.top
        command['data']['roi']['left'] = settings.left
        command['data']['roi']['width'] = settings.width_pixels
        command['data']['roi']['height'] = settings.height_pixels
        self.api_handler.publish(self.api_handler.main_topic + "/gui/datahub", json.dumps(command))

    def _update_camera(self, client, userdata, message):
        print(message.payload)
        data = json.loads(message.payload)['data']
        if data['device'] == 'cameras':
            if 'mode' in data.keys() \
                    and data['mode']["value"] == 'area' \
                    and 'roi' in data.keys():
                top = ROIProperty(**data['roi']['top'])
                left = ROIProperty(**data['roi']['left'])
                width = ROIProperty(**data['roi']['width'])
                height = ROIProperty(**data['roi']['height'])
                self.cameras[data['name']] = CameraSettings(name=data['name'],
                                                            top_props=top,
                                                            left_props=left,
                                                            width_props=width,
                                                            height_props=height,
                                                            top=top.value,
                                                            left=left.value,
                                                            width_pixels=width.value,
                                                            height_pixels=height.value)
            if 'sn' in data.keys() and 'name' in data.keys():
                self.serial_number_names[data['sn']] = data['name']
            if 'file_paths' in data.keys():
                cam_name = self.serial_number_names[data['sn']]
                self.file_paths[cam_name] = [Path(path_string) for path_string in data['file_paths']]
                self._load_images()

    def _update_exposure_settings(self, client, userdata, message):
        payload_dict = json.loads(message.payload)
        for camera in self.cameras.values():
            camera.exposure_time_ms = payload_dict['data']['exposure']
            camera.delay = payload_dict['data']['delay']

    def _get_current_path(self):
        self.api_handler.publish(self.api_handler.main_topic + "/gui/directory", json.dumps(self.file_command))

    def _send_capture_command(self):
        # TODO: add new stack and experiment settings with current stage position

        command = {"type": "operation", "data": {"device": "execution", "command": "run", "state": True}}
        self.api_handler.send_command(json.dumps(command))

    def _load_images(self):
        time.sleep(1)
        for name, paths in self.file_paths.items():
            self.current_images[name] = []
            self.current_metadatas[name] = []
            for path in paths:
                print(path)
                with h5py.File(path, 'r') as image:
                    print(image)
                    self.current_metadatas[name].append(json.loads(image['metadata'][()]))
                    self.current_images[name].append(np.asarray(image['Data']))
                self.has_new_image = True

    def _get_config(self):
        command = {
            "type": "operation",
            "data": {
                "device": "system",
                "command": "scopeconfig"
            }
        }
        self.api_handler.send_command(json.dumps(command))
        timeout = 10
        while self.cameras == {} and timeout > 0:
            time.sleep(0.1)
            timeout -= 0.1
        if timeout <= 0:
            raise LuxendoAPIException("Timeout while waiting for camera configuration")
