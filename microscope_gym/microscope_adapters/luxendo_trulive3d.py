from collections import OrderedDict
from typing import Optional, List, Tuple
from pydantic import validator
from copy import deepcopy
import time
import json
import numpy as np
import h5py
from microscope_gym import interface
from microscope_gym.interface import Objective, Microscope


import paho.mqtt.client as mqtt


class APIException(Exception):
    pass


class VendorAPIHandler:
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

        self.mqttc = mqtt.Client()
        self.subscribed_topics = []

        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_message = self.on_message

    def on_message(self, client, userdata, message):
        print("Received message: " + message.topic + " " + str(message.payload))
        self.latest_message = message
        self.reply_json = json.loads(message.payload)
        self.waiting_for_reply = False

    def on_connect(self, client, userdata, flags, result_code):
        if result_code == 0:
            print("Connected")
            for topic in self.subscribed_topics:
                self.mqttc.subscribe(topic)

            self.connected = True
        else:
            self.connected = False
            self.close()

    def on_disconnect(self, client, userdata, result_code):
        self.connected = False
        if result_code == 0:
            print("Disonnected")
        else:
            raise APIException(f"Connection to MQTT broker lost unexpectedly. Error code: {result_code}")

    def connect(self):
        self.mqttc.connect(self.broker_address, self.broker_port)
        self.mqttc.loop_start()

    def close(self):
        self.mqttc.loop_stop()
        self.mqttc.disconnect()

    def subscribe(self, topic):
        topic = self.main_topic + '/' + topic
        self.subscribed_topics.append(topic)
        if self.connected:
            self.mqttc.subscribe(topic)

    def publish(self, topic: str, payload: str):
        self._publish_time = time.time()
        self.last_published = f"topic: {topic}, payload: {payload}"
        self.mqttc.publish(topic, payload)

    def send_command(self, command):
        self.publish(self.main_topic + '/gui', command)

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
        raise APIException(
            f"Timeout ({self.reply_timeout_ms / 1000.0} s) while waiting for reply to command: {self.last_published}")

    def __del__(self):
        self.close()


class Axis(interface.stage.Axis):
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
        is_moving: bool
            True if the axis is moving, False otherwise.
    '''
    target: float
    guiName: Optional[str]
    partOf: Optional[str]
    type: str = 'linear'

    @validator('target')
    @classmethod
    def target_in_range(cls, target, values, **kwargs):
        if target < values['min'] or target > values['max']:
            raise ValueError(
                f"{values['name']}-axis target position {target} is not in range {values['min']} - {values['max']}")
        return target


class Stage(interface.Stage):
    '''Stage class.

    methods:
        get_nearest_positions_in_range(z_position: float, y_position: float, x_position: float) -> tuple
            get nearest position in range
        wait_until_stopped(timeout_ms: float) -> bool
            wait until stage is stopped, return True if stopped, False if timeout

    properties:
        axes: list[Axes]
            list of Axis objects
        axes_dict: dict
            dictionary where keys are the axes names
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

    def is_moving(self):
        return any([axis.target != axis.position_um for axis in self.axes.values()])

    def __init__(self, mqtt_handler: VendorAPIHandler):
        self.z_range = None
        self.y_range = None
        self.x_range = None
        self.mqtt_handler = mqtt_handler
        self.mqtt_handler.connect()
        self.mqtt_handler.subscribe("embedded/stages")
        self.default_command = {"type": "device", "data": {"device": "stages", "command": "get"}}
        self._update_axes_from_device_message(self._get_stage_status())

    def wait_until_stopped(self, wait_timeout_ms=10000):
        for message in self.mqtt_handler.keep_waiting_for_replies(wait_timeout_ms):
            self._update_axes_from_device_message(message['data']['axes'])
            if not self.is_moving():
                return True
        return False

    def _update_axes_positions(self, axis_names: List[str], positions: List[float]):
        command = deepcopy(self.default_command)
        command['data']['command'] = 'set'
        command['data']['axes'] = []
        for name, position in zip(axis_names, positions):
            command['data']['axes'].append({"name": name, "target": position})
        self.mqtt_handler.send_command(str(command))

    def _update_axes_from_device_message(self, axes_data_from_device):
        self.axes = OrderedDict()
        for axis_data in axes_data_from_device:
            axis = self._axis_from_dict(axis_data)
            self.axes[axis.name] = axis

    def _get_stage_status(self):
        message = self.mqtt_handler.send_command_and_wait_for_reply(str(self.default_command))
        return message['data']['axes']

    @staticmethod
    def _axis_from_dict(axis_dict: dict) -> Axis:
        axis_dict['position'] = float(axis_dict.pop('value'))
        return Axis(**axis_dict)

    @staticmethod
    def _axis_to_dict(axis: Axis) -> dict:
        axis_dict = axis.dict()
        axis_dict['value'] = axis_dict.pop('position')
        return axis_dict
