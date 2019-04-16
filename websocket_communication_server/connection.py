import asyncio

import json

from websocket_communication_server.messagetemplates import commandmessage


class Connection:
    def __init__(self, ws, server):
        self.server = server
        self.server.logger.debug("create connection")
        self.ws = ws
        self.identified = False
        self.name = "unknown"
        self.loop = asyncio.get_event_loop()

    def ask_for_identification(self):
        self.server.logger.debug("ask for identification")
        self.sendMsg(commandmessage(sender="server", cmd="indentify"))
        self.sendMsg(
            commandmessage(sender="server", cmd="set_time", time=self.server.t0)
        )

    def sendMsg(self, msg):
        coro = self.ws.send(msg)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def recive(self):
        try:
            async for message in self.ws:
                self.validate_message(message)
                if not self.identified:
                    self.ask_for_identification()
        except asyncio.IncompleteReadError:
            pass

    def validate_message(self, msg):
        self.server.logger.debug(self.name + " recived message: " + msg)
        try:
            jmsg = json.loads(msg)
            if not self.identified:
                if "cmd" not in jmsg["data"]:
                    return
                if jmsg["data"]["cmd"] != "indentify":
                    return
            if "server" in jmsg["target"]:
                if jmsg["type"] == "cmd":
                    self.run_command(jmsg)
                elif jmsg["type"] == "data":
                    pass
                else:
                    self.server.logger.error("unknown message type " + msg)
            return self.server.send_to_names(jmsg["target"], msg)
        except:
            self.server.logger.exception(Exception)
            pass

    def run_command(self, data):
        cmd_data = data["data"]
        if cmd_data["cmd"] == "indentify":
            self.identify(data)
        elif cmd_data["cmd"] == "close_socket":
            self.server.force_stop()
        else:
            self.server.logger.error("unknown command: " + str(cmd_data["cmd"]))

    def identify(self, data):
        cmd_data = data["data"]
        if not self.server.verify_password(cmd_data["kwargs"].get("password","")):
            return
        if "name" in cmd_data["kwargs"]:
            self.name = cmd_data["kwargs"]["name"]
            self.identified = True
