import sys
import logging
import tornado.ioloop
from webthing import (MultipleThings, Property, Thing, Value, WebThingServer)
from awning import Awning, PiAwning, Awnings
from switch import Switch
from motor_tb6612Fng import load_tb6612fng
from time import sleep
from awning_web import AwningWebServer
from awning_mcp import AwningMCPServer


class AwningWebThing(Thing):

    # regarding capabilities refer https://iot.mozilla.org/schemas
    # there is also another schema registry http://iotschema.org/docs/full.html not used by webthing

    def __init__(self, awning: Awning):
        Thing.__init__(
            self,
            'urn:dev:ops:anwing-TB6612FNG',
            'awning_' + awning.name,
            ['MultiLevelSensor'],
            "awning control"
        )
        self.awning = awning
        self.awning.add_listener(self.on_value_changed)

        self.name = Value(self.awning.name)
        self.add_property(
            Property(self,
                     'name',
                     self.name,
                     metadata={
                         'title': 'Name',
                         "type": "sting",
                         'description': 'the name',
                         'readOnly': True
                     }))

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



def run_server(port: int, filename: str, switch_pin_forward: int, switch_pin_backward: int):
    logging.info("switch_pin_forward " + str(switch_pin_forward))
    logging.info("switch_pin_backward " + str(switch_pin_backward))

    while True:
        awnings = [PiAwning(motor) for motor in load_tb6612fng(filename)]
        anwing_all= Awnings("all", awnings)
        awnings = [anwing_all] + awnings
        awning_webthings = [AwningWebThing(anwing) for anwing in awnings]

        web_server = AwningWebServer(awnings, port=port+1)
        mcp_server = AwningMCPServer("awning", port+2, awnings)
        server = WebThingServer(MultipleThings(awning_webthings, 'Awnings'), port=port, disable_host_validation=True)

        switch = None
        if switch_pin_forward > 0 and switch_pin_backward > 0:
            switch = Switch(switch_pin_forward, switch_pin_backward, awnings=anwing_all)

        try:
            logging.info('starting the server')
            mcp_server.start()#
            web_server.start()
            server.start()
        except KeyboardInterrupt:
            logging.info('stopping the server')
            if switch is not None:
                switch.terminate()
            for awning in awnings:
                awning.terminate()
            mcp_server.stop()
            web_server.stop()
            server.stop()
            logging.info('done')
            return
        except Exception as e:
            logging.error(e)
            sleep(3)



if __name__ == '__main__':
    try:
        logging.basicConfig(format='%(asctime)s %(name)-20s: %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
        logging.getLogger('tornado.access').setLevel(logging.ERROR)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
        run_server(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    except Exception as e:
        logging.error(str(e))
        raise e
