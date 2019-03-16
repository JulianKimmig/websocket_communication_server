import time

import logging
import random
import threading

from websocket_communication_server.messagetemplates import commandmessage
from websocket_communication_server.socketclient import WebSocketClient
from websocket_communication_server.socketserver import SockerServer, SOCKETPORT


class Testclass:
    def __init__(self, host, name):
        self.runime = 0
        self.name = name
        self.wsc = WebSocketClient(name, host=host)
        self.wsc.add_cmd_function("pass_ball", self.pass_ball) # registers own pass_ball method to be called when reciving the pass_ball command
        self.pingpong = "ping" if "1" in name else "pong"
        self.opponent = "Player2" if "1" in name else "Player1"

    def pass_ball(self, catch=None): #methods called by the message validator should have default attributes to be valid against "TypeError: pass_ball() missing 1 required positional argument: 'catch'"
        if catch is None:
            print("End of the game because the ball went missing somewhere")
            return
        print(self.pingpong)  # prints ping or pong
        if not catch:
            print("Damn!")  # dont like losing the ball
        time.sleep(1)  # delay in game because it would be way to fast without, maybe the flytime of the ball :)
        self.wsc.write_to_socket(
            commandmessage(
                cmd="pass_ball", # the command to call at the reciver
                sender=self.name, # sender of the command
                target=self.opponent, # reciver
                catch=random.random() < 0.8, # 80% ball catch
            )
        )


if __name__ == "__main__":
    # connects to the firsts free port
    notconnected = True
    socketserver = None
    while notconnected:
        try:
            socketserver = SockerServer(port=SOCKETPORT)  # binds to 127.0.0.1:8888++
            notconnected = False
        except:
            SOCKETPORT += 1

    threading.Thread(
        target=socketserver.run_forever
    ).start()  # runs server forever in background
    test1 = Testclass(host=socketserver.ws_adress, name="Player1")  # create player 1
    test2 = Testclass(host=socketserver.ws_adress, name="Player2")  # create player 2
    time.sleep(1)  # gives the players enought timw to identify
    test1.pass_ball(True)  # throw the first ball
    while 1:
        time.sleep(1)  # play forever
