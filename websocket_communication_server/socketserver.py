import asyncio

import time

import logging
import websockets

from websocket_communication_server.connection import Connection

SOCKETPORT = 8888


class SockerServer:
    def __init__(self, host="127.0.0.1", port=SOCKETPORT):
        logging.getLogger("websocket").setLevel(logging.ERROR)
        logging.getLogger("asyncio").setLevel(logging.ERROR)
        logging.getLogger("asyncio.coroutines").setLevel(logging.ERROR)
        logging.getLogger("websockets.server").setLevel(logging.ERROR)
        logging.getLogger("websockets.protocol").setLevel(logging.ERROR)
        self.running=True
        self.all_connections = {}
        self.logger = logging.getLogger("sockerserver_" + str(host) + ":" + str(port))
        self.host = host
        self.port = port
        self.ws_adress = "ws://" + host + ":" + str(port)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        ws_serv = websockets.serve(
            self.add_connection, host=host, port=port, max_size=2 ** 25
        )

        self.t0 = time.time()
        self.loop.run_until_complete(ws_serv)
        self.logger.info("Socket created at " + host + ":" + str(port))
        self.ws_server=ws_serv.ws_server

    def send_to_names(self, names, message):
        while "server" in names:
            names.remove("server")
        reached=[]
        for ws, c in self.all_connections.items():
            if c.name in names:
                reached.append(c.name)
                c.sendMsg(message)
        diff=set(names).difference(set(reached))
        if len(diff)>0:
            self.logger.error("targets not found: "+", ".join(diff))


    def send_to_all(self, message):
        for ws, c in self.all_connections.items():
            c.sendMsg(message)

    async def add_connection(self, ws, path):
        if ws not in self.all_connections:
            # from websocket_communication_server.connection import Connection

            self.all_connections[ws] = Connection(ws, self)
            self.all_connections[ws].ask_for_identification()
        connection = self.all_connections[ws]
        try:
            while 1:
                await connection.recive()
        except Exception as e:
            self.logger.error("Conenction Error " + connection.name)
            self.logger.exception(e)
            del self.all_connections[ws]
            del connection

    def run_forever(self):
        self.loop.run_forever()

    def get_www_data_path(self):
        import os
        from websocket_communication_server import www_data
        return os.path.abspath(os.path.dirname(www_data.__file__))

    def force_stop(self):
        self.loop.stop()
        for i in range(10):
            if not self.loop.is_running():
                break
            time.sleep(1)
        self.ws_server.close()

def connect_to_first_free_port(startport=SOCKETPORT):
    notconnected = True
    socketserver = None

    while notconnected:
        try:
            print(startport)
            socketserver = SockerServer(port=startport)
            notconnected = False
        except OSError as e:
            startport += 1
    return socketserver

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(filename)s %(lineno)d %(name)s %(levelname)-8s  %(message)s",
        datefmt="(%H:%M:%S)",
    )

    socketserver=connect_to_first_free_port()

    from websocket_communication_server.socketclient import WebSocketClient

    autoclient = WebSocketClient("testclient", host=socketserver.ws_adress)
    socketserver = connect_to_first_free_port()
    print(socketserver.get_www_data_path())
    socketserver.run_forever()