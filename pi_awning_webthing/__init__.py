import logging
from string import Template
from pi_awning_webthing.app import App
from pi_awning_webthing.awning_webthing import run_server

PACKAGENAME = 'pi_awning_webthing'
ENTRY_POINT = "awning"
DESCRIPTION = "A web connected terrace awning controller on Raspberry Pi"


UNIT_TEMPLATE = Template('''
[Unit]
Description=$packagename
After=syslog.target

[Service]
Type=simple
ExecStart=$entrypoint --command listen --verbose $verbose --port $port --filename $filename --switch_pin_forward $switch_pin_forward --switch_pin_backward $switch_pin_backward
SyslogIdentifier=$packagename
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
''')


class AwningApp(App):

    def do_add_argument(self, parser):
        parser.add_argument('--filename', metavar='filename', required=False, type=str,  help='the config filename')
        parser.add_argument('--switch_pin_forward', metavar='switch_pin_forward', required=False, type=int, default=-1, help='foward pin for switch')
        parser.add_argument('--switch_pin_backward', metavar='switch_pin_backward', required=False, type=int, default=-1, help='backward pin for switch')

    def do_additional_listen_example_params(self):
        return "--filename /etc/awning/tb6612fng_motors.config --switch_pin_forward 17 --switch_pin_backward 27"

    def do_process_command(self, command:str, port: int, verbose: bool, args) -> bool:
        if command == 'listen' and (args.filename is not None):
            logging.info("running " + self.packagename + " on port " + str(port) + " with config " + args.filename)
            run_server(port, args.filename, args.switch_pin_forward, args.switch_pin_backward, self.description)
            return True
        elif args.command == 'register' and (args.filename is not None):
            logging.info("register " + self.packagename + " on port " + str(port) + " with config " + args.filename)
            unit = UNIT_TEMPLATE.substitute(packagename=self.packagename, entrypoint=self.entrypoint, port=port, verbose=verbose, switch_pin_forward=args.switch_pin_forward, switch_pin_backward=args.switch_pin_backward, filename=args.filename)
            self.unit.register(port, unit)
            return True
        else:
            return False


def main():
    AwningApp(PACKAGENAME, ENTRY_POINT, DESCRIPTION).handle_command()


if __name__ == '__main__':
    main()
