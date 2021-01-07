import RPi.GPIO as GPIO
from pi_awning_webthing.awning import Motor
from dataclasses import dataclass
from typing import List
import logging
from os import path


@dataclass
class Config:
    name: str
    gpio_forward: int
    gpio_backward: int


def load_tb6612fng(filename: str) -> List[Motor]:
    motors = list()
    if "tb6612fng" in filename.lower() and path.exists(filename):
        with open(filename, "r") as file:
            for line in file.readlines():
                line = line.strip()
                if not line.startswith("#") and len(line) > 0:
                    try:
                        parts = line.split(",")
                        name = parts[0].strip()
                        pin_forward = int(parts[1].strip())
                        pin_backward = int(parts[2].strip())
                        step_duration = float(parts[3].strip())
                        motors.append(TB6612FNGMotor(name, pin_forward, pin_backward, step_duration))
                        logging.info("config entry found: " + name + " with pin_forward=" + str(pin_forward) + ", pin_backward=" + str(pin_backward) + ", step_duration=" + str(step_duration))
                    except Exception as e:
                        logging.error("invalid syntax in line " + line + "  ignoring it" + str(e))
    return motors



class TB6612FNGMotor(Motor):

    def __init__(self, name: str, pin_forward: int, pin_backward: int, sec_per_step: float):
        self.__name = name
        self.__sec_per_step = sec_per_step
        GPIO.setmode(GPIO.BCM)
        self.pin_forward = pin_forward
        self.pin_forward_is_on = False
        GPIO.setup(pin_forward, GPIO.OUT, initial=0)
        self.pin_backward = pin_backward
        self.pin_backward_is_on = False
        GPIO.setup(pin_backward, GPIO.OUT, initial=0)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def sec_per_step(self) -> float:
        return self.__sec_per_step


    def stop(self):
        if self.pin_backward_is_on or self.pin_forward_is_on:
            logging.info("stop motor")
        if self.pin_backward_is_on:
            GPIO.output(self.pin_backward, 0)
            self.pin_backward_is_on = False
        if self.pin_forward_is_on:
            GPIO.output(self.pin_forward, 0)
            self.pin_forward_is_on = False

    def backward(self):
        self.stop()
        logging.info("start backward motor")
        GPIO.output(self.pin_backward, 1)
        self.pin_backward_is_on = True

    def forward(self):
        self.stop()
        logging.info("start forward motor")
        GPIO.output(self.pin_forward, 1)
        self.pin_forward_is_on = True

