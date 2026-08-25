import gpiod
from gpiod.line import Direction, Value
from awning import Motor
from dataclasses import dataclass
from typing import List
import logging
from os import path



@dataclass
class Config:
    name: str
    chip: str
    gpio_forward: int
    gpio_backward: int


def load_tb6612fng(filename: str, chip: str) -> List[Motor]:
    logging.info("loading config " + filename)
    motors = list()
    if "tb6612fng" in filename.lower() and path.exists(filename):
        logging.info("parsing config " + filename)
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
                        logging.info("config entry found: " + name + " with chip=" + chip + ", pin_forward=" + str(pin_forward) + ", pin_backward=" + str(pin_backward) + ", step_duration=" + str(step_duration) + ". Activate motor control")
                        motors.append(TB6612FNGMotor(name, chip, pin_forward, pin_backward, step_duration))
                    except Exception as e:
                        logging.error("invalid syntax in line " + line + "  ignoring it" + str(e))
    return motors




class TB6612FNGMotor(Motor):

    def __init__(self, name: str, chip: str, pin_forward: int, pin_backward: int, sec_per_step: float):
        self.__name = name
        self.__sec_per_step = sec_per_step
        # gpiod expects the full device path (e.g. /dev/gpiochip0), not just the chip name
        self.chip = chip if chip.startswith("/") else "/dev/" + chip
        self.pin_forward = pin_forward
        self.pin_forward_is_on = False
        self.pin_backward = pin_backward
        self.pin_backward_is_on = False
        logging.info(self.__name + " register pin " + str(pin_forward) + " as forward")
        logging.info(self.__name + " register pin " + str(pin_backward) + " as backward")
        self.__request = gpiod.request_lines(
            self.chip,
            consumer="awning-" + name,
            config={
                (pin_forward, pin_backward): gpiod.LineSettings(
                    direction=Direction.OUTPUT,
                    output_value=Value.INACTIVE,
                )
            },
        )

    def terminate(self):
        self.__request.release()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def sec_per_step(self) -> float:
        return self.__sec_per_step


    def stop(self):
        if self.pin_backward_is_on or self.pin_forward_is_on:
            logging.info(self.__name + " stop motor (forward and backward)")
        if self.pin_backward_is_on:
            self.__request.set_value(self.pin_backward, Value.INACTIVE)
            self.pin_backward_is_on = False
        if self.pin_forward_is_on:
            self.__request.set_value(self.pin_forward, Value.INACTIVE)
            self.pin_forward_is_on = False

    def backward(self):
        self.stop()
        logging.info(self.__name + " start backward motor")
        self.__request.set_value(self.pin_backward, Value.ACTIVE)
        self.pin_backward_is_on = True

    def forward(self):
        self.stop()
        logging.info(self.__name + " start forward motor")
        self.__request.set_value(self.pin_forward, Value.ACTIVE)
        self.pin_forward_is_on = True
