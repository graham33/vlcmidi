import logging
import pytest
from unittest.mock import MagicMock

import rtmidi

import vlcmidi

_TEST_CHANNEL = 5
_TEST_CONTROLLER = 16  # controller number 16 (general purpose controller)
_TEST_CONTROLLER_VALUE = 57
_MIDI_CONTROL_CHANGE_MESSAGE_TYPE = 0b1011
_TEST_MIDI_MSG = [(_MIDI_CONTROL_CHANGE_MESSAGE_TYPE << 4)
                  | (_TEST_CHANNEL - 1), _TEST_CONTROLLER, _TEST_CONTROLLER_VALUE]


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

    These are not supported for some MIDI APIs (e.g. Windows or 'dummy').
    '''

    compiled_apis = [rtmidi.get_api_name(api) for api in rtmidi.get_compiled_api()]
    env_api = rtmidi.get_api_name(rtmidi.midiutil.get_api_from_environment())
    logging.info(f"rtmidi compiled API: {compiled_apis}, API from env: {env_api}")

    port_name = "vlcmidi virtual test"
    try:
        rtmidi.midiutil.open_midioutput(use_virtual=True, interactive=False, port_name=port_name)
    except (rtmidi.InvalidPortError, rtmidi.NoDevicesError, rtmidi.SystemError) as e:
        logging.warning(f"Virtual ports not available: couldn't open port ({e})")
        return False

    # make sure we can see the port
    midi_in = rtmidi.MidiIn()
    available_ports = midi_in.get_ports()
    if len(available_ports) == 0 or not any(port_name in port for port in available_ports):
        logging.warning(f"Virtual ports not available: port not in {available_ports}")
        return False
    return True


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
    test_msg = vlcmidi.MIDI.Message(_MIDI_CONTROL_CHANGE_MESSAGE_TYPE, _TEST_CHANNEL,
                                    [_TEST_CONTROLLER, _TEST_CONTROLLER_VALUE])
    dispatch.process_message(test_msg)
    assert test_func.called_with(_TEST_CONTROLLER_VALUE)


def test_vlc_status(requests_mock):
    requests_mock.get('http://myhostdoesnotexist:31337/requests/status.json?command=pl_stop', json={"state": "stopped"})
    vlc = vlcmidi.VLC(host='myhostdoesnotexist', port=31337, password='mysecretpassword')
    assert vlc.status_cmd('pl_stop')['state'] == 'stopped'
