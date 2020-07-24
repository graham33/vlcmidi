#!/usr/bin/env python3

"""Send VLC commands based on MIDI input messages."""

import collections
import logging
import requests
import sys
import time
import yaml

from rtmidi.midiutil import open_midiinput

# Docs for messages: https://github.com/videolan/vlc/blob/master/share/lua/http/requests/README.txt

class VLC(object):

    def __init__(self, password, host='localhost', port=8080):
        self._session = requests.Session()
        self._session.auth = ('', password)
        self._url = f'http://{host}:{port}'

    def status_cmd(self, cmd, **kwargs):
        params = collections.OrderedDict([('command', cmd)])
        params.update(kwargs)
        return self._vlc_request('requests/status.json', params)

    def _vlc_request(self, path, params):
        # Use string rather than kwargs to prevent escaping per
        # https://stackoverflow.com/questions/23496750/how-to-prevent-python-requests-from-percent-encoding-my-urls
        params_str = '&'.join(f'{k}={v}' for k, v in params.items())
        r = self._session.get(f'{self._url}/{path}', params=params)
        return r.json()




class MIDI(object):

    Message = collections.namedtuple('Message', 'message_type channel data')

    _STATUS_MASK = 240

    '''
    @param port Default None - will prompt
    '''
    def __init__(self, port=None):
        self._port = port

    def __enter__(self):
        self._midi_in, self._port_name = open_midiinput(self._port)
        return self

    def __exit__(self, type, value, tb):
        self._midi_in.close_port()

    def poll_message(self):
        ret = self._midi_in.get_message()
        if ret is None:
            return None

        rtmidi_msg, deltatime = ret
        logging.debug("Received message %s from %s", rtmidi_msg, self._port_name)

        return MIDI.Message(self._get_message_type(rtmidi_msg[0]),
                            self._get_channel(rtmidi_msg[0]),
                            rtmidi_msg[1:])

    @staticmethod
    def _get_message_type(status_byte):
        return (status_byte & MIDI._STATUS_MASK) >> 4

    @staticmethod
    def _get_channel(status_byte):
        return status_byte & ~MIDI._STATUS_MASK


class MIDICommandDispatcher(object):

    # TODO: move?
    _CC_MESSAGE = 11

    # TODO: support different message types
    def __init__(self, channel, controller_number):
        self._channel = channel
        self._controller_number = controller_number
        self._commands = {}

    def register_command(self, controller_value, func):
        self._commands[controller_value] = func

    def process_message(self, message):
        logging.debug("Message type %s, channel %s", message.message_type, message.channel)

        if message.message_type == MIDICommandDispatcher._CC_MESSAGE and message.channel == self._channel:
            controller_number = message.data[0]
            controller_value = message.data[1]

            if controller_number == self._controller_number:
                logging.debug("Processing %s", controller_value)

                if controller_value in self._commands:
                    self._commands[controller_value](controller_value)
                else:
                    logging.error(f"No command registered for controller value {controller_value}")


def _process_message(message, session):
    logging.debug("Message type %s, channel %s", message.message_type, message.channel)

    if message.message_type == _CC_MESSAGE and message.channel == _CHANNEL:
        controller_number = message.data[0]
        controller_value = message.data[1]

        if controller_number == _CONTROLLER_NUMBER:
            logging.debug("Processing %s", controller_value)


            _funcs[controller_value](controller_value)


def main():
    log = logging.getLogger('midiin_poll')
    logging.basicConfig(level=logging.DEBUG)

    # Prompts user for MIDI input port, unless a valid port number or name
    # is given as the first argument on the command line.
    # API backend defaults to ALSA on Linux.
    # TODO: cfg
    port = sys.argv[1] if len(sys.argv) > 1 else None

    # TODO: arg
    with open('config.yaml', 'r') as f:
        cfg = yaml.load(f)

    vlc = VLC(cfg['vlc']['password'])

    dispatch = MIDICommandDispatcher(cfg['channel'], cfg['controller_number'])

    for controller_value, command_info in cfg['commands'].items():
        command = command_info.pop('command')
        dispatch.register_command(controller_value, lambda x: vlc.status_cmd(command, **command_info))

    with MIDI(port) as midi:
        print("Entering main loop. Press Control-C to exit.")

        while True:
            msg = midi.poll_message()

            if msg:
                _process_message(message, vlc)

            time.sleep(0.01)

if __name__ == "__main__":
    main()
