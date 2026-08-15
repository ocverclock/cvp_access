# CVP Access dependencies

The authoritative APT package list is `cvp_access_installer/apt-packages.txt`.

## Core runtime

- `python3`: CVP Access runtime.
- `python3-evdev`: direct USB keyboard events.
- `alsa-utils`: `amidi`, `aplay` and ALSA diagnostics.

## MIDI development / future migration

- `python3-rtmidi`: direct Python MIDI I/O option for future versions.
- `python3-mido`: higher-level MIDI message handling.

The current application still uses ALSA `amidi` for the validated Yamaha SysEx path.

## Piper / voice generation

- `python3-venv`: isolated Piper environment.
- `python3-pip`: installs Piper into that venv.
- `libgomp1`: OpenMP runtime commonly required by ONNX Runtime.
- `sox`: useful WAV inspection/conversion utility.

`piper-tts` itself is installed from `requirements-piper.txt` in the isolated venv.

## Repository / installation

- `git`: clone and update CVP Access.
- `curl`, `wget`: downloads and diagnostics.
- `ca-certificates`: HTTPS certificate verification.
- `rsync`: robust file synchronization.
- `unzip`: archive extraction.
- `jq`: JSON processing for future tooling.

## Network administration

- `samba`: SMB server.
- `samba-common-bin`: Samba administration tools.
- `smbclient`: SMB diagnostics.
- `avahi-daemon`: `.local` discovery.
- `openssh-server`: remote maintenance.

## Diagnostics

- `usbutils`: `lsusb`.
- `lsof`: open-file/device diagnostics.
- `psmisc`: `fuser`, `killall`.
- `nano`, `tree`, `htop`: local maintenance.

## Deliberately not installed

CVP Access does not require a desktop environment, PulseAudio, PipeWire, a JACK server, Docker or a compiler toolchain.

Note: Debian's `python3-rtmidi` package may pull a JACK client library dependency. This is only a runtime library and does not install or run a JACK audio server.
