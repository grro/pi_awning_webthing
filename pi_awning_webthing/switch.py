import logging
import RPi.GPIO as GPIO
from typing import List
from pi_awning_webthing.awning import Awning


class Switch:
    STOP = (False, False)
    MOVE_FORWARD = (True, False)
    MOVE_BACKWARD = (False, True)
    IDLE = (True, True)

    def __init__(self, pin_forward: int, pin_backward: int, awnings: List[Awning]):
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
        if new_state != self.state:
            logging.info("switch new state     " + str(new_state) + " (old " + str(self.state) + ")")
        try:
            if self.state != new_state:
                if new_state == self.MOVE_FORWARD:
                    for anwing in self.awnings:
                        anwing.set_target_position(100)
                elif new_state == self.MOVE_BACKWARD:
                    for anwing in self.awnings:
                        anwing.set_target_position(0)
                elif new_state == self.STOP:
                    for anwing in self.awnings:
                        current_pos = anwing.get_current_position()
                        anwing.set_target_position(current_pos)
                else:
                    pass
        finally:
            self.state = new_state
