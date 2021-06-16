import logging
import sys
import time
from datetime import datetime
from abc import ABC, abstractmethod
from threading import Thread


class Motor(ABC):

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def backward(self):
        pass

    @abstractmethod
    def forward(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def sec_per_step(self) -> float:
        pass


class AwningPropertyListener:

    def on_current_pos_updated(self, current_position: int):
        pass

    def on_retracting_updated(self, retracting: bool):
        pass

    def on_extenting_updated(self, extenting: bool):
        pass


class Movement:
    SLOT_TOLERANCE = 7

    def __init__(self, motor: Motor, start_pos: int, num_slots: int, sec_per_slot: float, is_positive: bool, awning):
        self.start_time = datetime.now()
        self.awning = awning
        self.motor = motor
        self.start_pos = start_pos
        self.num_slots = num_slots
        self.sec_per_slot = sec_per_slot
        if is_positive:
            self.direction = 1
        else:
            self.direction = -1

    def get_pause_sec(self):
        return 0.5

    def get_current_pos(self) -> int:
        if self.is_target_reached():
            return self.get_target_pos()
        else:
            return self.start_pos + (self.__get_num_processed_slots() * self.direction)

    def get_target_pos(self) -> int:
        return self.start_pos + (self.num_slots * self.direction)

    def is_target_reached(self) -> bool:
        return self.__get_num_processed_slots() >= self.num_slots

    def __get_num_processed_slots(self) -> int:
        elapsed_sec = (datetime.now() - self.start_time).total_seconds()
        num_processed = 0
        if elapsed_sec > 1:
            num_processed = elapsed_sec / self.sec_per_slot
        return int(num_processed)

    def process(self):
        if self.is_target_reached():
            return Idling(self.motor, self.get_target_pos(), self.sec_per_slot, self.awning)
        else:
            self.awning.listener.on_current_pos_updated(self.get_current_pos())
            return self

    def drive_to(self, new_position: int):
        if new_position > 100:
            new_position = 100
        elif new_position < 0:
            new_position = 0
        return self.__create_movement(int(new_position))

    def __create_movement(self, new_position: int):
        current_pos = self.get_current_pos()
        if (new_position - current_pos) > self.SLOT_TOLERANCE:
            return Forward(self.motor, current_pos, new_position, self.sec_per_slot, self.awning)
        elif (current_pos - new_position) > self.SLOT_TOLERANCE:
            return Backward(self.motor, current_pos, new_position, self.sec_per_slot, self.awning)
        else:
            return Idling(self.motor, current_pos, self.sec_per_slot, self.awning)


class Idling(Movement):

    def __init__(self, motor: Motor, start_pos: int, sec_per_slot: float, awning):
        Movement.__init__(self, motor, start_pos, 0, sec_per_slot, True, awning)
        self.motor.stop()
        self.awning.listener.on_extenting_updated(False)
        self.awning.listener.on_retracting_updated(False)

    def get_pause_sec(self):
        pause_sec = int(self.SLOT_TOLERANCE * self.sec_per_slot * 1.4)
        if pause_sec < 3:
            pause_sec = 3
        return pause_sec

    def process(self):
        return self   # do nothing


class Forward(Movement):

    def __init__(self, motor: Motor, start_pos: int, new_position: int, sec_per_slot: float, awning):
        Movement.__init__(self, motor, start_pos, new_position - start_pos, sec_per_slot, True, awning)
        self.motor.forward()
        self.awning.listener.on_extenting_updated(True)
        self.awning.listener.on_retracting_updated(False)


class Backward(Movement):

    def __init__(self, motor: Motor, start_pos: int, new_position: int, sec_per_slot: float, awning):
        Movement.__init__(self, motor, start_pos, start_pos - new_position, sec_per_slot, False, awning)
        self.motor.backward()
        self.awning.listener.on_retracting_updated(True)
        self.awning.listener.on_extenting_updated(False)


class Awning:
    PERIODIC_CALIBRATE_ON_HOUR = 2
    PERIODIC_CALIBRATE_ON_MINUTE = 40

    def __init__(self, motor: Motor):
        self.name = motor.name
        self.sec_per_slot = motor.sec_per_step
        self.logger = logging.getLogger(self.name)
        self.listener = AwningPropertyListener()
        self.motor = motor
        self.movement = Idling(self.motor, 0, self.sec_per_slot, self)
        Thread(name=self.name + "_move", target=self.__process_move, daemon=False).start()
        Thread(target=self.__periodic_calibrate, daemon=True).start()

    def __periodic_calibrate(self):
        time.sleep(10)
        self.calibrate()
        already_scheduled = False
        while True:
            now = datetime.now()
            if self.PERIODIC_CALIBRATE_ON_HOUR <= now.hour < (self.PERIODIC_CALIBRATE_ON_HOUR + 1) and now.minute >= self.PERIODIC_CALIBRATE_ON_MINUTE:
                if not already_scheduled:
                    self.calibrate()
                already_scheduled = True
            else:
                already_scheduled = False
            time.sleep(20 * 60)

    def register_listener(self, listener: AwningPropertyListener):
        self.listener = listener

    def calibrate(self):
        self.logger.info("calibrating")
        self.movement = Idling(self.motor, 100, self.sec_per_slot, self) # set position to 100%
        self.set_target_position(0)   # and backward to position 0. This ensures that the awning is calibrated with position 0

    def get_current_position(self) -> int:
        return self.movement.get_current_pos()

    def get_target_position(self) -> int:
        return self.movement.get_target_pos()

    def set_target_position(self, new_position: int):
        self.movement = self.movement.drive_to(new_position)

    def __process_move(self):
        while True:
            try:
                self.movement = self.movement.process()
            except:
                self.movement = Idling(self.motor, 0, self.sec_per_slot, self)
                self.logger.warning('move operation failed '  + str(sys.exc_info()))
            finally:
                pause_sec = self.movement.get_pause_sec()
                time.sleep(pause_sec)
