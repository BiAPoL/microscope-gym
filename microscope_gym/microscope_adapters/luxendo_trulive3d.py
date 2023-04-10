from collections import OrderedDict
from typing import Optional, List, Tuple
from pydantic import Field, validator
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
        self.message_callbacks = []

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
        for callback in self.message_callbacks:
            callback(self.reply_json)

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

    def wait_for_connection(self):
        started = time.time()
        while not self.connected and time.time() - started < self.reply_timeout_ms / 1000.0:
            time.sleep(0.1)
        if not self.connected:
            raise APIException(f"Connection to MQTT broker timed out after {self.reply_timeout_ms / 1000.0} s")

    def ensure_connection(self):
        if not self.connected:
            self.connect()
            self.wait_for_connection()

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
    position_um: float = Field(..., alias='target')
    value: float
    guiName: Optional[str]
    partOf: Optional[str]
    type: str = 'linear'

    class Config:
        validate_assignment = True


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
        return any([axis.value != axis.position_um for axis in self.axes.values()])

    def __init__(self, api_handler: VendorAPIHandler):
        self.api_handler = api_handler
        self.api_handler.ensure_connection()
        self.api_handler.subscribe("embedded/stages")
        self.default_command = {"type": "device", "data": {"device": "stages", "command": "get"}}
        self.api_handler.message_callbacks.append(self._message_callback)
        self._get_stage_status()

    def _update_axes_positions(self, axis_names: List[str], positions: List[float]):
        command = deepcopy(self.default_command)
        command['data']['command'] = 'set'
        command['data']['axes'] = []
        for name, position in zip(axis_names, positions):
            self.axes[name].position_um = position
            command['data']['axes'].append({"name": name, "value": position})
        self.api_handler.send_command(json.dumps(command))

    def _message_callback(self, payload_dict: dict):
        axes = OrderedDict()
        for axis_data in payload_dict['data']['axes']:
            axis = Axis(**axis_data)
            axes[axis.name] = axis
        if len(axes) > 0:
            self.axes = axes

    def _get_stage_status(self):
        message = self.api_handler.send_command_and_wait_for_reply(json.dumps(self.default_command))
        return message['data']['axes']
