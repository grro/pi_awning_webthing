import logging
import os
import threading
import gpiod
from gpiod.line import Direction, Edge, Bias, Value
from datetime import datetime, timedelta
from awning import Awnings

class Switch:
    STOP = (False, False)
    MOVE_FORWARD = (True, False)
    MOVE_BACKWARD = (False, True)
    IDLE = (True, True)

    def __init__(self, chip: str, pin_forward: int, pin_backward: int, awnings: Awnings):
        self.awnings = awnings
        self.pin_forward = pin_forward
        self.pin_backward = pin_backward
        # gpiod expects the full device path (e.g. /dev/gpiochip0), not just the chip name
        chip_path = chip if chip.startswith("/") else "/dev/" + chip
        self.last_pressed = datetime.now()
        self.state = self.IDLE
        logging.info("Switch register pin " + str(self.pin_forward) + " as forward")
        logging.info("Switch register pin " + str(self.pin_backward) + " as backward")
        self.__request = gpiod.request_lines(
            chip_path,
            consumer="awning-switch",
            config={
                (pin_forward, pin_backward): gpiod.LineSettings(
                    direction=Direction.INPUT,
                    edge_detection=Edge.BOTH,
                    bias=Bias.PULL_DOWN,
                )
            },
        )
        self.__running = True
        self.__thread = threading.Thread(target=self.__monitor, name="switch-monitor", daemon=True)
        self.__thread.start()
        logging.info("Switch bound to pin_forward=" + str(self.pin_forward) + " and pin_backward=" + str(self.pin_backward))


    def terminate(self):
        self.__running = False
        self.__request.release()


    def __monitor(self):
        while self.__running:
            try:
                if self.__request.wait_edge_events(timedelta(seconds=1)):
                    self.__request.read_edge_events()
                    self.on_switch_updated()
            except Exception as e:
                logging.error(e)


    def on_switch_updated(self):
        is_forward = self.__request.get_value(self.pin_forward) == Value.ACTIVE
        is_backward = self.__request.get_value(self.pin_backward) == Value.ACTIVE
        new_state = (is_forward, is_backward)

        if datetime.now() > self.last_pressed + timedelta(milliseconds=200):
            self.last_pressed = datetime.now()
            try:
                if new_state == self.MOVE_FORWARD:
                    if self.awnings.is_moving_forward():
                        self.awnings.stop()
                    else:
                        self.awnings.set_position(100)
                elif new_state == self.MOVE_BACKWARD:
                    if self.awnings.is_moving_backward():
                        self.awnings.stop()
                    else:
                        self.awnings.set_position(0)
            except Exception as e:
                logging.error(e)
