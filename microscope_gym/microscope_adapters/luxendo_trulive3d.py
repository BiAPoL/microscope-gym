import numpy as np
import time
import h5py
import json
from microscope_gym import interface
from microscope_gym.interface import Objective

import paho.mqtt.client as mqtt


class MqttException(Exception):
    pass


class MqttHandler:
    def __init__(self, broker_address: str = "localhost", broker_port: int = 61614,
                 serial_number: str = "", reply_timeout_ms=10000):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.main_topic = serial_number
        self.reply_timeout_ms = reply_timeout_ms

        self.connected = False
        self.waiting_for_reply = False
        self.result: bool
        self.reply_json: dict

        self.mqttc = mqtt.Client()
        self.subscribedTopics = []

        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect

        def on_message(client, userdata, message):
            print("Received message: " + message.topic + " " + str(message.payload))
            self.result = message.payload[0]
            self.reply_json = json.loads(message.payload[1:])
            self.waiting_for_reply = False

        self.mqttc.on_message = on_message

    def on_connect(self, client, userdata, flags, result_code):
        if result_code == 0:
            print("Connected")
            for topic in self.subscribedTopics:
                self.mqttc.subscribe(topic)

            self.connected = True
        else:
            # couldn't connect
            self.connected = False
            self.close()

    def on_disconnect(self, client, userdata, result_code):
        if result_code == 0:
            # disconnect was successful
            print("Disonnected")
        else:
            # unexpected disconnect
            raise MqttException(f"Connection to MQTT broker lost unexpectedly. Error code: {result_code}")

    def connect(self):
        self.mqttc.connect(self.broker_address, self.broker_port)
        self.mqttc.loop_start()

    def close(self):
        self.mqttc.loop_stop()
        self.mqttc.disconnect()

    def subscribe(self, topic):
        topic = self.main_topic + '/' + topic
        self.subscribedTopics.append(topic)
        if self.connected:
            self.mqttc.subscribe(topic)

    def publish(self, topic, payload):
        self.mqttc.publish(topic, payload)

    def send_command(self, command):
        self.publish(self.main_topic + '/gui', command)

    def send_command_and_wait_for_reply(self, command, poll_interval_ms=10):
        self.send_command(command)
        timeout_ms = self.reply_timeout_ms
        self.waiting_for_reply = True
        while self.waiting_for_reply and timeout_ms > 0:
            time.sleep(poll_interval_ms / 1000.0)
            timeout_ms -= poll_interval_ms
        if self.result:
            return self.reply_json
        else:
            raise MqttException(f"Command {command} failed. Error message: {self.reply_json['message']}")


class Stage(interface.Stage):
    '''Stage class.

    methods:
        move_x_to(absolute_x_position)
        move_x_by(relative_x_position)
        move_y_to(absolute_y_position)
        move_y_by(relative_y_position)
        move_z_to(absolute_z_position)
        move_z_by(relative_z_position)

    properties:
        z_position(): float
            z position in µm
        y_position(): float
            y position in µm
        x_position(): float
            x position in µm
        z_range(): tuple
            z range in µm
        y_range(): tuple
            y range in µm
        x_range(): tuple
            x range in µm
    '''

    def __init__(self, mqtt_handler: MqttHandler):
        self.z_range = None
        self.y_range = None
        self.x_range = None
        self.mqtt_handler = mqtt_handler
        self.mqtt_handler.subscribe("embedded/stages")
        self._get_stage_range_from_hardware()
        self._get_current_position_from_hardware()

    @property
    def z_position(self):
        return super().z_position

    @z_position.setter
    def z_position(self, value):
        super(Stage, type(self)).z_position.fset(self, value)
        self._last_move_time = time.time()

    @property
    def y_position(self):
        return super().y_position

    @y_position.setter
    def y_position(self, value):
        super(Stage, type(self)).y_position.fset(self, value)
        self._last

    def _get_current_position_from_hardware(self, client, userdata, msg):
        axes = self._get_stage_status()
        for axis in axes:
            if axis['name'] == 'z':
                self._z_position = float(axis['position'])
            elif axis['name'] == 'y':
                self._y_position = float(axis['position'])
            elif axis['name'] == 'x':
                self._x_position = float(axis['position'])

    def _get_stage_range_from_hardware(self):
        axes = self._get_stage_status()
        for axis in axes:
            if axis['name'] == 'z':
                self.z_range = (float(axis['min']), float(axis['max']))
            elif axis['name'] == 'y':
                self.y_range = (float(axis['min']), float(axis['max']))
            elif axis['name'] == 'x':
                self.x_range = (float(axis['min']), float(axis['max']))
        assert isinstance(
            self.z_range, tuple) and isinstance(
            self.z_range[0], float) and isinstance(
            self.z_range[1], float), "Could not set stage Z range"
        assert isinstance(
            self.y_range, tuple) and isinstance(
            self.y_range[0], float) and isinstance(
            self.y_range[1], float), "Could not set stage Y range"
        assert isinstance(
            self.x_range, tuple) and isinstance(
            self.x_range[0], float) and isinstance(
            self.x_range[1], float), "Could not set stage X range"

    def _get_stage_status(self):
        message = self.mqtt_handler.send_command_and_wait_for_reply({"command": "get"})
        return message['data']['axes']
