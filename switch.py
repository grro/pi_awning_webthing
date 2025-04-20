import logging
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from awning import Awnings


class Switch:
    STOP = (False, False)
    MOVE_FORWARD = (True, False)
    MOVE_BACKWARD = (False, True)
    IDLE = (True, True)

    def __init__(self, pin_forward: int, pin_backward: int, awnings: Awnings):
        self.awnings = awnings
        self.pin_forward = pin_forward
        self.pin_backward = pin_backward
        self.last_pressed = datetime.now()
        self.state = self.IDLE
        GPIO.setmode(GPIO.BCM)
        logging.info("Switch register pin " + str(self.pin_forward) + " as forward")
        GPIO.setup(self.pin_forward, GPIO.IN, GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin_forward, GPIO.BOTH)
        GPIO.add_event_callback(self.pin_forward, self.on_switch_updated)
        logging.info("Switch register pin " + str(self.pin_backward) + " as backward")
        GPIO.setup(self.pin_backward, GPIO.IN, GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin_backward, GPIO.BOTH)
        GPIO.add_event_callback(self.pin_backward, self.on_switch_updated)
        logging.info("Switch bound to pin_forward=" + str(self.pin_forward) + " and pin_backward=" + str(self.pin_backward))

    def on_switch_updated(self, pin: int):
        is_forward = GPIO.input(self.pin_forward) >= 1
        is_backward = GPIO.input(self.pin_backward) >= 1
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
