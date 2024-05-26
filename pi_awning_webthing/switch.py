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
        self.last_time_pressed = datetime.now()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_forward, GPIO.IN, GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin_forward, GPIO.BOTH)
        GPIO.add_event_callback(self.pin_forward, self.on_switch_updated)
        GPIO.setup(self.pin_backward, GPIO.IN, GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin_backward, GPIO.BOTH)
        GPIO.add_event_callback(self.pin_backward, self.on_switch_updated)
        logging.info("Switch bound to pin_forward=" + str(self.pin_forward) + " and pin_backward=" + str(self.pin_backward))

    def on_switch_updated(self, pin: int):
        is_forward = GPIO.input(self.pin_forward) >= 1
        is_backward = GPIO.input(self.pin_backward) >= 1
        new_state = (is_forward, is_backward)
        logging.info("\n\n\nnew state Forward=" + str(new_state[0]) + "; Backward=" + str(new_state[1]) + " is_moving=" + str(self.awnings.is_moving()))

        if datetime.now() > (self.last_time_pressed + timedelta(seconds=0.5)):
            self.last_time_pressed = datetime.now()
            try:
                if new_state == self.MOVE_FORWARD:
                    if self.awnings.is_moving():
                        logging.info("Forward and motion. stop")
                        self.awnings.stop()
                    else:
                        logging.info("Forward set pos 0")
                        self.awnings.set_position(100)
                elif new_state == self.MOVE_BACKWARD:
                    if self.awnings.is_moving():
                        logging.info("Bckward and motion. stop")
                        self.awnings.stop()
                    else:
                        logging.info("Bckward set pos 0")
                        self.awnings.set_position(0)
            except Exception as e:
                logging.error(e)
        else:
            logging.info("double click")