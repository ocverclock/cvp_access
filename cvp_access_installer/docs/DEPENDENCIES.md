# CVP Access dependencies

Target platform: Raspberry Pi OS Lite 64-bit based on Debian 13 (Trixie).

## Runtime and MIDI/audio

- `python3` — runs CVP Access and diagnostic tools.
- `python3-evdev` — reads the USB keyboard directly through Linux input events.
- `alsa-utils` — provides `amidi` for RawMIDI/SysEx and `aplay` for spoken WAV playback; also useful for ALSA diagnostics.
- `python3-rtmidi` — optional/future direct Python MIDI backend, useful if CVP Access later replaces `amidi` subprocesses.
- `python3-mido` — optional/future MIDI message abstraction and protocol tooling.
- `sox` — WAV inspection/conversion utility for voice-bank maintenance and debugging.

## Piper voice generation

- `python3-venv` — isolates Piper from the system Python environment.
- `python3-pip` — installs Piper inside that venv.
- `piper-tts` — local neural TTS used to generate the French voice bank. Installed in the private venv, not system-wide.

## Installation and maintenance

- `git` — clone and update CVP Access from GitHub.
- `curl`, `wget` — downloads and troubleshooting.
- `ca-certificates` — HTTPS certificate trust.
- `rsync` — safe file synchronization/backups.
- `unzip` — archive extraction.
- `jq` — JSON processing for maintenance/diagnostics.

## Network access

- `samba` — SMB server for editing/browsing the project from another computer.
- `samba-common-bin` — Samba administration tools such as `smbpasswd` and `testparm`.
- `smbclient` — Samba client/testing tools.
- `avahi-daemon` — mDNS discovery (`hostname.local`).
- `openssh-server` — remote maintenance over SSH.

## Diagnostics

- `usbutils` — `lsusb` for the CVP, Prodipe and USB keyboard.
- `lsof` — find processes holding files/devices open.
- `psmisc` — `fuser`/`killall`, particularly useful for locked MIDI devices.
- `nano` — emergency terminal editing.
- `tree` — project/file layout inspection.
- `htop` — CPU/RAM process diagnosis.

## Deliberately not installed

CVP Access does not need a desktop environment, PulseAudio, PipeWire, JACK, Docker, Node.js, CMake or a compiler toolchain for the current design. ALSA is used directly.
