import logging
import threading
import time

import json

import websocket
from filter_dict import filter_dict

from websocket_communication_server.messagetemplates import commandmessage


class WebSocketClient:
    def __init__(self, name, logger=None, host=None, reconnect=True):
        name = str(name)
        self.message_cmd_functions = {}
        self.message_types = {}
        self.ws = None
        self.time = time.time()
        self._on_open_functions = {}
        self._on_error_functions = {}
        self._on_close_functions = {}
        self._on_message_functions = {}
        if logger is None:
            logger = logging.getLogger("ListenWebsocket_" + name)
        self.logger = logger
        self.ws_thread = None
        self.reconnect = reconnect
        self.host = None
        self.reconnect_time = 1
        self.name = name

        self.add_on_message(name="default", func=self.default_messagevalidator)

        self.add_message_type("cmd", self.default_command_validator)
        self.add_cmd_function(
            "indentify",
            lambda: self.write_to_socket(
                commandmessage(cmd="indentify", sender=self.name, name=self.name)
            ),
        )
        self.add_cmd_function("set_time", self.set_time)
        if host is not None:
            self.connect_to_socket(host)

    def set_time(self, time=None):
        if time is None:
            return
        self.time = time

    def connect_to_socket(self, host):
        if self.ws is not None:
            self.close()
        self.ws = websocket.WebSocketApp(
            host,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        self.logger.info("conenct to websocket: " + host)
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)

        self.ws_thread.start()
        time.sleep(1)
        if self.ws is None:
            self.host = None
            return False
        self.host = host
        self.logger.debug("websocket connected")

    def on_open(self):
        self.logger.debug("websocket opened")
        for n, f in self._on_open_functions.items():
            f()

    def on_message(self, message):
        self.logger.debug("message " + message)
        for n, f in self._on_message_functions.items():
            f(message)

    def on_error(self, ws):
        self.logger.debug("socket error")
        for n, f in self._on_error_functions.items():
            f()

    def on_close(self):
        self.logger.info("websocket closed")
        for n, f in self._on_close_functions.items():
            f()
        self.ws = None
        self.ws_thread = None
        if self.reconnect and self.host is not None:
            time.sleep(self.reconnect_time)
            self.connect_to_socket(self.host)

    def add_on_open(self, name, func, overwrite=False):
        if name in self._on_open_functions and not overwrite:
            self.logger.error("on_open_functions " + name + " already defined!")
            return
        self._on_open_functions[name] = func

    def add_on_error(self, name, func, overwrite=False):
        if name in self._on_error_functions and not overwrite:
            self.logger.error("on_error_functions " + name + " already defined!")
            return
        self._on_error_functions[name] = func

    def add_on_close(self, name, func, overwrite=False):
        if name in self._on_close_functions and not overwrite:
            self.logger.error("on_close_function " + name + " already defined!")
            return
        self._on_close_functions[name] = func

    def add_on_message(self, name, func, overwrite=False):
        if name in self._on_message_functions and not overwrite:
            self.logger.error("on_message_function " + name + " already defined!")
            return
        self._on_message_functions[name] = func

    def write_to_socket(self, msg):
        if self.ws is not None:
            if self.ws_thread is not None:
                try:
                    self.ws.send(msg)
                except Exception as e:
                    self.logger.exception(e)

    def close(self):
        self.reconnect = False
        if self.ws is not None:
            self.ws.close()
            if self.ws_thread is not None:
                try:
                    self.ws_thread.join()
                except:
                    pass
                self.ws_thread = None
            self.ws = None

    def default_command_validator(self, data):
        cmd_data = data["data"]
        if cmd_data["cmd"] in self.message_cmd_functions:
            try:
                self.message_cmd_functions[cmd_data["cmd"]](
                    **filter_dict(
                        cmd_data["kwargs"], self.message_cmd_functions[cmd_data["cmd"]]
                    )
                )
            except Exception as e:
                self.logger.exception(e)
        else:
            self.logger.error("unknown command: " + cmd_data["cmd"])

    def default_messagevalidator(self, msg):
        try:
            jmsg = json.loads(msg)
            if jmsg["type"] in self.message_types:
                self.message_types[jmsg["type"]](jmsg)
            else:
                self.logger.error("unknown message type " + msg)
        except:
            self.logger.exception(Exception)

    def add_cmd_function(self, name, func, overwrite=False):
        if name in self.message_cmd_functions and not overwrite:
            self.logger.error("function " + name + " already defined!")
            return
        self.message_cmd_functions[name] = func

    def add_message_type(self, name, func, overwrite=False):
        if name in self.message_types and not overwrite:
            self.logger.error("message type " + name + " already defined!")
            return
        self.message_types[name] = func
