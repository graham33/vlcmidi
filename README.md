# vlcmidi [![graham33](https://circleci.com/gh/graham33/vlcmidi.svg?style=svg)](https://app.circleci.com/pipelines/github/graham33/vlcmidi)
Simple tool to run VLC commands based on MIDI input messages (e.g. from a MIDI
footswitch).

## Installation
You can install vlcmidi like any other python script, e.g. using `pip` directly,
[Nixpkgs] (see the provided [shell.nix](./shell.nix)), or conda (see the
provided [environment.yml](./environment.yml)).

The primary dependency is [python-rtmidi], which can use common MIDI APIs on
Linux and Windows. I've tested the script on Linux (Nixos 20.03) and Windows 10.

To configure VLC, go to `Tools -> Preferences`, enable All settings (not
Simple), then go to `Interface -> Main Interfaces` and enabled `Lua interpreter`
and `Web`. You should set a password under `Lua` -> `Lua HTTP`. The port can be
overridden at the command line (I can't find an option for it in the UI in my
current version of VLC).

## Configuration
vlcmidi takes a YAML config file ([config.yaml](./config.yaml) by default, an
example is provided), which maps MIDI Control Change messages (see the [midi.org
docs] for details) to VLC commands.

### My Configuration
I use this to control songs and backing tracks in VLC while playing guitar,
using my Morningstar MC6. Here's the config I use, in case it's useful. The MC6
is configured as below, the corresponding vlcmidi config is in
[config.yaml](./config.yaml).

I usually have a bank with the three footswitches on the top row controlling VLC
and the three on the bottom row controlling presets on my HX Stomp:

| Play/Pause     | Seek           | Vol            |
| -------------- | -------------- | -------------- |
| **(HX Stomp)** | **(HX Stomp)** | **(HX Stomp)** |

The VLC footswitches are configured as follows (using the [Morningstar Web
Editor]):
* **Play/Pause**:
  * Toggle Mode On
  * Short name: Play
  * Toggle name: Pause
  * Press (Pos: 1): play
  * Press (Pos: 2): pause 
  * Long Press (Pos: Both): 75% playback rate
  * Long Double Tap (Pos: Both): 50% playback rate
  * Double Tap (Pos: Both): 100% playback rate
* **Seek**
  * Toggle Mode Off
  * Press: seek +30s
  * Double Tap: seek -30s
  * Long Press: seek to position 0 (i.e. beginning of track)
* **Vol**
  * Toggle Mode Off
  * Press: volume +5
  * Double Tap: volume +20
  * Long Press: volume -5
  * Long Double Tap: volume -20

As an example, 'Play' is configured to send CC 16 value 0 on channel 1 in my
config.

[midi.org docs]: https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message
[Morningstar Web Editor]: https://www.morningstarfx.com/editor
[Nixpkgs]: https://github.com/NixOS/nixpkgs
[python-rtmidi]: https://pypi.org/project/python-rtmidi/
[VLC http requests README]: https://github.com/videolan/vlc/blob/master/share/lua/http/requests/README.txt
