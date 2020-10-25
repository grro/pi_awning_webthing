from webthing import (MultipleThings, Property, Thing, Value, WebThingServer)
from pi_anwing_webthing.anwing import Anwing, AwningPropertyListener
from pi_anwing_webthing.switch import Switch
from pi_anwing_webthing.motor_tb6612Fng import load_tb6612fng
import logging
import tornado.ioloop


class WebThingAwningPropertyListener(AwningPropertyListener):

    def __init__(self, anwing_webthing):
        self.anwing_webthing = anwing_webthing

    def on_current_pos_updated(self, current_position: int):
        self.anwing_webthing.ioloop.add_callback(self.anwing_webthing.set_current_position, current_position)

    def on_retracting_updated(self, retracting: bool):
        self.anwing_webthing.ioloop.add_callback(self.anwing_webthing.set_retracting, retracting)

    def on_extenting_updated(self, extenting: bool):
        self.anwing_webthing.ioloop.add_callback(self.anwing_webthing.set_extending, extenting)


class AnwingWebThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, description: str, awning: Anwing):
        Thing.__init__(
            self,
            'urn:dev:ops:anwing-TB6612FNG',
            'Anwing ' + awning.name,
            ['MultiLevelSensor'],
            description
        )
        self.logger = logging.getLogger(awning.name)
        self.awning = awning
        self.awning.register_listener(WebThingAwningPropertyListener(self))

        self.target_position = Value(0, self.__target_position)
        self.add_property(
            Property(self,
                     'target_position',
                     self.target_position,
                     metadata={
                         '@type': 'LevelProperty',
                         'title': 'awning ' + awning.name + ' target position',
                         "type": "integer",
                         "minimum": 0,
                         "maximum": 100,
                         'description': 'awning ' + awning.name + ' target position'
                     }))

        self.current_position = Value(0)
        self.add_property(
            Property(self,
                     'current_position',
                     self.current_position,
                     metadata={
                         '@type': 'LevelProperty',
                         'title': 'awning ' + awning.name + ' current position',
                         "type": "integer",
                         'minimum': 0,
                         'maximum': 100,
                         'readOnly': True,
                         'description': 'awning ' + awning.name + ' current position'
                     }))

        self.retracting = Value(0)
        self.add_property(
        Property(self,
                 'retracting',
                 self.retracting,
                 metadata={
                     '@type': 'BooleanProperty',
                     'title': awning.name + ' retracting',
                     "type": "boolean",
                     'readOnly': True,
                     'description': awning.name + " is retracting"
                 }))

        self.extending = Value(0)
        self.add_property(
        Property(self,
                 'extending',
                 self.extending,
                 metadata={
                     '@type': 'BooleanProperty',
                     'title': awning.name + ' extending',
                     "type": "boolean",
                     'readOnly': True,
                     'description': awning.name + " is extending"
                 }))

        self.ioloop = tornado.ioloop.IOLoop.current()

    def __target_position(self, new_postion):
        self.awning.set_target_position(new_postion)

    def set_current_position(self, value):
        self.current_position.notify_of_external_update(value)
        self.logger.info("position " + str(value) + " reached (target=" + str(self.target_position.get()) + ")")

    def set_retracting(self, value):
        self.retracting.notify_of_external_update(value)
        self.logger.info("anwing is retracting " + str(value))

    def set_extending(self, value):
        self.extending.notify_of_external_update(value)
        self.logger.info("anwing is extending " + str(value))



def run_server(hostname: str, port: int, filename: str, description: str):

    anwings = [Anwing(motor) for motor in load_tb6612fng(filename)]
    anwing_webthings = [AnwingWebThing(description, anwing) for anwing in anwings]

    server = WebThingServer(MultipleThings(anwing_webthings, 'anwings'), hostname=hostname, port=port)
    Switch(pin_forward=17, pin_backward=27, anwings = anwings)

    try:
        logging.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping the server')
        server.stop()
        logging.info('done')
