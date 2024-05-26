import logging
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from typing import List
from pi_awning_webthing.awning import Awnings


class Switch:
    STOP = (False, False)
    MOVE_FORWARD = (True, False)
    MOVE_BACKWARD = (False, True)
    IDLE = (True, True)

    def __init__(self, pin_forward: int, pin_backward: int, awnings: Awnings):
        self.awnings = awnings
        self.pin_forward = pin_forward
        self.pin_backward = pin_backward
        self.state = self.STOP
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_forward, GPIO.IN, GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin_forward, GPIO.BOTH)
        GPIO.add_event_callback(self.pin_forward, self.on_switch_updated)
        GPIO.setup(self.pin_backward, GPIO.IN, GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin_backward, GPIO.BOTH)
        GPIO.add_event_callback(self.pin_backward, self.on_switch_updated)
        logging.info("Switch bound to pin_forward=" + str(self.pin_forward) + " and pin_backward=" + str(self.pin_backward))

    def is_forward(self) -> bool:
        return self.state[0]

    def is_backward(self) -> bool:
        return self.state[1]

    def on_switch_updated(self, pin: int):
        is_forward = GPIO.input(self.pin_forward) >= 1
        is_backward = GPIO.input(self.pin_backward) >= 1

        new_state = (is_forward, is_backward)
        logging.info("new state " + str(new_state) + " is_moving=" + str(self.awnings.is_moving()))
        try:
            if new_state == self.MOVE_FORWARD:
                if self.awnings.is_moving():
                    self.awnings.set_position(100)
                else:
                    # stop
                    self.awnings.stop()

            elif new_state == self.MOVE_BACKWARD:
                if self.awnings.is_moving():
                    self.awnings.set_position(0)
                else:
                    # stop
                    self.awnings.stop()
        except Exception as e:
            logging.error(e)
        finally:
            self.state = new_state
