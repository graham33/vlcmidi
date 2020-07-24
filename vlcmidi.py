#!/usr/bin/env python3
"""Send VLC commands based on MIDI input messages."""

import click
import collections
import logging
import requests
import time
import yaml

from rtmidi.midiutil import open_midiinput

# Docs for messages: https://github.com/videolan/vlc/blob/master/share/lua/http/requests/README.txt


class VLC(object):
    def __init__(self, host, port, password):
        self._session = requests.Session()
        self._session.auth = ('', password)
        self._url = f'http://{host}:{port}'

    def status_cmd(self, cmd, **kwargs):
        logging.info(f"Sending VLC status command {cmd} {kwargs}")
        params = collections.OrderedDict([('command', cmd)])
        params.update(kwargs)
        return self._vlc_request('requests/status.json', params)

    def _vlc_request(self, path, params):
        r = self._session.get(f'{self._url}/{path}', params=params)
        return r.json()


class MIDI(object):

    # Note channel is 1-based not 0-based
    Message = collections.namedtuple('Message', 'message_type channel data')

    CC_MESSAGE_TYPE = 11
    _STATUS_MASK = 240

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

        return MIDI.Message(self._get_message_type(rtmidi_msg[0]), self._get_channel(rtmidi_msg[0]), rtmidi_msg[1:])

    @staticmethod
    def _get_message_type(status_byte):
        return (status_byte & MIDI._STATUS_MASK) >> 4

    @staticmethod
    def _get_channel(status_byte):
        return (status_byte & ~MIDI._STATUS_MASK) + 1


class MIDICommandDispatcher(object):
    def __init__(self, channel, controller_number):
        self._channel = channel
        self._controller_number = controller_number
        self._commands = {}

    def register_command(self, controller_value, func):
        self._commands[controller_value] = func

    def process_message(self, message):
        logging.debug(f"Processing message {message}")

        if message.message_type == MIDI.CC_MESSAGE_TYPE and message.channel == self._channel:
            controller_number = message.data[0]
            controller_value = message.data[1]

            if controller_number == self._controller_number:
                if controller_value in self._commands:
                    self._commands[controller_value](controller_value)
                else:
                    logging.warning(f"No command registered for controller value {controller_value}")


@click.command()
@click.option('-c', '--config-file', default='config.yaml', help='Config file')
@click.option('--midi-port',
              help='A MIDI port number or name. The user will be prompted if not given and not in config file.')
@click.option('-v', '--verbose/--no-verbose', default=False, help='Enable verbose logging')
def vlcmidi(config_file, midi_port, verbose):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    with open(config_file, 'r') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    vlc = VLC(host=cfg['vlc']['host'], port=cfg['vlc']['port'], password=cfg['vlc']['password'])

    dispatch = MIDICommandDispatcher(cfg['midi']['channel'], cfg['midi']['controller_number'])

    for controller_value, command_info in cfg['commands'].items():
        command = command_info.pop('command')
        logging.debug(f"Registering command {command} {command_info} for controller value {controller_value}")
        dispatch.register_command(
            controller_value,
            lambda x, command=command, command_info=command_info: vlc.status_cmd(command, **command_info))

    if midi_port is None and 'port' in cfg['midi']:
        midi_port = cfg['midi']['port']

    with MIDI(midi_port) as midi:
        logging.info("Entering main loop. Press ctrl-c to exit.")

        while True:
            msg = midi.poll_message()

            if msg:
                dispatch.process_message(msg)

            time.sleep(0.01)
