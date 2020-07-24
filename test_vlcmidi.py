
import json

import pytest
import re
import requests_mock
import subprocess
from unittest.mock import MagicMock

import rtmidi

import vlcmidi

_TEST_CHANNEL = 4
_TEST_CONTROLLER = 16 # controller number 16 (general purpose controller)
_TEST_CONTROLLER_VALUE = 57
_MIDI_CONTROL_CHANGE_MESSAGE_TYPE = 0b1011
_TEST_MIDI_MSG = [(_MIDI_CONTROL_CHANGE_MESSAGE_TYPE << 4) | _TEST_CHANNEL, # Control Change message
                  _TEST_CONTROLLER,
                  _TEST_CONTROLLER_VALUE
]

def test_midi_mock(monkeypatch):
    midi_in = MagicMock()
    midi_in.get_message.return_value = (_TEST_MIDI_MSG, 0.1)
    mock_open_midiinput = MagicMock(return_value=(midi_in, "TEST PORT"))

    monkeypatch.setattr(vlcmidi, 'open_midiinput', mock_open_midiinput)
    with vlcmidi.MIDI() as midi:
        assert mock_open_midiinput.called
        msg = midi.poll_message()
        assert midi_in.get_message.called

        assert msg.message_type == _MIDI_CONTROL_CHANGE_MESSAGE_TYPE
        assert msg.channel == _TEST_CHANNEL
        assert msg.data == [_TEST_CONTROLLER, _TEST_CONTROLLER_VALUE]

    assert midi_in.close_port.called

def _rtmidi_virtual_ports_available():
    '''Check whether rtimidi virtual ports are available.

    These are not supported on some platforms (e.g. Windows).
    '''
    try:
        rtmidi.midiutil.open_midioutput(use_virtual=True, port_name="vlcmidi virtual test")
        return True
    except rtmidi.UnsupportedOperationError:
        return False

@pytest.mark.skipif(not _rtmidi_virtual_ports_available(), reason="rtmidi virtual ports not available")
@pytest.mark.timeout(5)
def test_midi_virtual():
    midi_out, out_port_name = rtmidi.midiutil.open_midioutput(use_virtual=True, port_name="vlcmidi test_midi_virtual")
    assert midi_out.is_port_open()

    with vlcmidi.MIDI(out_port_name) as midi:
        midi_out.send_message(_TEST_MIDI_MSG)

        while True:
            msg = midi.poll_message()
            if msg is not None:
                assert msg.message_type == _MIDI_CONTROL_CHANGE_MESSAGE_TYPE
                assert msg.channel == _TEST_CHANNEL
                assert msg.data == [_TEST_CONTROLLER, _TEST_CONTROLLER_VALUE]
                break

def test_midi_command_dispatcher():
    dispatch = vlcmidi.MIDICommandDispatcher(_TEST_CHANNEL, _TEST_CONTROLLER)
    test_func = MagicMock()
    dispatch.register_command(_TEST_CONTROLLER_VALUE, test_func)
    test_msg = vlcmidi.MIDI.Message(_MIDI_CONTROL_CHANGE_MESSAGE_TYPE,
                                    _TEST_CHANNEL,
                                    [_TEST_CONTROLLER, _TEST_CONTROLLER_VALUE]
    )
    dispatch.process_message(test_msg)
    assert test_func.called_with(_TEST_CONTROLLER_VALUE)


def test_vlc_status(requests_mock):
    requests_mock.get('http://localhost:8080/requests/status.json?command=pl_play', json={"state": "playing"})
    # TODO: URL
    vlc = vlcmidi.VLC('mysecretpassword')
    assert vlc.status_cmd('pl_play')['state'] == 'playing'


