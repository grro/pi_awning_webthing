from webthing import (MultipleThings, Property, Thing, Value, WebThingServer)
from pi_awning_webthing.awning import Awning, PiAwning, Awnings
from pi_awning_webthing.switch import Switch
from pi_awning_webthing.motor_tb6612Fng import load_tb6612fng
from time import sleep
import logging
import tornado.ioloop


class AwningWebThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, description: str, awning: Awning):
        Thing.__init__(
            self,
            'urn:dev:ops:anwing-TB6612FNG',
            'Awning_' + awning.name,
            ['MultiLevelSensor'],
            description
        )
        self.awning = awning
        self.awning.add_listener(self.on_value_changed)

        self.position = Value(self.awning.get_position(), self.awning.set_position)
        self.add_property(
            Property(self,
                     'position',
                     self.position,
                     metadata={
                         '@type': 'LevelProperty',
                         'title': 'Awning position',
                         "type": "number",
                         "minimum": 0,
                         "maximum": 100,
                         "unit": "percent",
                         'description': 'awning position',
                         'readOnly': False
                     }))

        self.is_target_reached = Value(self.awning.is_target_reached())
        self.add_property(
            Property(self,
                     'is_target_reached',
                     self.is_target_reached,
                     metadata={
                         'title': 'is_target_reached',
                         "type": "boolean",
                         'description': 'true, if target position is reached',
                         'readOnly': True
                     }))

        self.ioloop = tornado.ioloop.IOLoop.current()

    def on_value_changed(self):
        self.ioloop.add_callback(self._on_value_changed)

    def _on_value_changed(self):
        self.position.notify_of_external_update(self.awning.get_position())
        self.is_target_reached.notify_of_external_update(self.awning.is_target_reached())



def run_server(port: int, filename: str, switch_pin_forward: int, switch_pin_backward: int, description: str):

    while True:
        awnings = [PiAwning(motor) for motor in load_tb6612fng(filename)]
        if len(awnings) > 2:
            awnings = [Awnings("all", awnings)] + awnings
        awning_webthings = [AwningWebThing(description, anwing) for anwing in awnings]
        server = WebThingServer(MultipleThings(awning_webthings, 'Awnings'), port=port, disable_host_validation=True)

        if switch_pin_forward > 0 and switch_pin_backward > 0:
            Switch(switch_pin_forward, switch_pin_backward, awnings= awnings)

        try:
            logging.info('starting the server')
            server.start()
        except KeyboardInterrupt:
            logging.info('stopping the server')
            server.stop()
            logging.info('done')
            return
        except Exception as e:
            logging.error(e)
            sleep(3)
