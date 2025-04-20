import logging
import sys
import time
from datetime import datetime
from typing import List
from abc import ABC, abstractmethod
from threading import Thread, Lock




class Awning(ABC):

    def __init__(self, name: str):
        self.name = name
        self.__listeners = set()

    @abstractmethod
    def is_target_reached(self) -> bool:
        pass

    @abstractmethod
    def get_position(self) -> int:
        pass

    @abstractmethod
    def set_position(self, new_position: int):
        pass

    @abstractmethod
    def is_moving_forward(self) -> bool:
        pass

    @abstractmethod
    def is_moving_backward(self) -> bool:
        pass

    @abstractmethod
    def stop(self):
        pass

    def add_listener(self, listener):
        self.__listeners.add(listener)

    def _notify_listeners(self):
        for listener in self.__listeners:
            listener()


class Motor(ABC):

    @abstractmethod
    def terminate(self):
        pass

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

    def is_moving_forward(self) -> bool:
        return False

    def is_moving_backward(self) -> bool:
        return False

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
            self.awning.on_updated()
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
        self.awning.on_updated()

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
        self.awning.on_updated()

    def is_moving_forward(self) -> bool:
        return True


class Backward(Movement):

    def __init__(self, motor: Motor, start_pos: int, new_position: int, sec_per_slot: float, awning):
        Movement.__init__(self, motor, start_pos, start_pos - new_position, sec_per_slot, False, awning)
        self.motor.backward()
        self.awning.on_updated()

    def is_moving_backward(self) -> bool:
        return True



class PiAwning(Awning):
    PERIODIC_CALIBRATE_ON_HOUR = 3
    PERIODIC_CALIBRATE_ON_MINUTE = 10

    def __init__(self, motor: Motor):
        self.motor = motor
        super().__init__(self.motor.name)
        self.sec_per_slot = motor.sec_per_step
        self.__lock = Lock()
        self.movement = Idling(self.motor, 0, self.sec_per_slot, self)
        self.set_position(0)
        Thread(name=self.name + "_move", target=self.__process_move, daemon=False).start()
        Thread(target=self.__periodic_calibrate, daemon=True).start()

    def terminate(self):
        self.motor.terminate()

    def on_updated(self):
        self._notify_listeners()

    def __periodic_calibrate(self):
        time.sleep(60)
        self.calibrate()
        already_scheduled = False
        while True:
            try:
                now = datetime.now()
                if self.PERIODIC_CALIBRATE_ON_HOUR <= now.hour < (self.PERIODIC_CALIBRATE_ON_HOUR + 1) and now.minute >= self.PERIODIC_CALIBRATE_ON_MINUTE:
                    if not already_scheduled:
                        self.calibrate()
                    already_scheduled = True
                else:
                    already_scheduled = False
            except Exception as e:
                logging.warning("error occurred on calibrating " + str(e))
            time.sleep(10 * 60)

    def calibrate(self):
        saved_target_pos = self.get_position()
        logging.info("calibrating")
        self.movement = Idling(self.motor, 100, self.sec_per_slot, self) # set position to 100%
        self.set_position(0)   # and backward to position 0. This ensures that the awning is calibrated with position 0
        # wait until completed
        for i in range (0, 60):
            if self.is_target_reached():
                break
            else:
                time.sleep(5)
        if self.get_current_position() != saved_target_pos:
            logging.info("move to previous target position " + str(saved_target_pos))
            self.set_position(saved_target_pos)

    def stop(self):
        self.set_position(self.get_current_position())

    def get_current_position(self) -> int:
        return self.movement.get_current_pos()

    def is_target_reached(self) -> bool:
        return self.get_current_position() == self.get_position()

    def is_moving_forward(self) -> bool:
        return self.movement.is_moving_forward()

    def is_moving_backward(self) -> bool:
        return self.movement.is_moving_backward()

    def get_position(self) -> int:
        return self.movement.get_target_pos()

    def set_position(self, new_position: int):
        with self.__lock:
            logging.info(self.name + " set position: " + str(new_position))
            self.movement = self.movement.drive_to(new_position)

    def __process_move(self):
        while True:
            with self.__lock:
                try:
                    self.movement = self.movement.process()
                except:
                    self.movement = Idling(self.motor, 0, self.sec_per_slot, self)
                    logging.warning('move operation failed ' + str(sys.exc_info()))
                finally:
                    pause_sec = self.movement.get_pause_sec()
            time.sleep(pause_sec)



class Awnings(Awning):

    def __init__(self, name: str, awnings: List[Awning]):
        self.__awnings = awnings
        [awning.add_listener(self._notify_listeners) for awning in awnings]
        super().__init__(name)

    def is_target_reached(self) -> bool:
        for awning in self.__awnings:
            if not awning.is_target_reached():
                return False
        return True


    def is_moving_backward(self) -> bool:
        for anwing in self.__awnings:
            if anwing.is_moving_backward():
                return True
        return False


    def is_moving_forward(self) -> bool:
        for anwing in self.__awnings:
            if anwing.is_moving_forward():
                return True
        return False

    def stop(self):
        for anwing in self.__awnings:
            anwing.stop()

    def get_position(self) -> int:
        positions = [awning.get_position() for awning in self.__awnings]
        total = sum(positions)
        if total == 0:
            return 0
        else:
            return int(total/len(positions))

    def set_position(self, new_position: int):
        logging.info(self.name + " set position: " + str(new_position))
        [awning.set_position(new_position) for awning in self.__awnings]


