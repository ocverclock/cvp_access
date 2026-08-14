# CVP Access

**Accessibility controller for Yamaha CVP digital pianos using Raspberry Pi, MIDI SysEx and spoken feedback.**

> 🇫🇷 **Présentation française**
> CVP Access est un projet d’interface d’accessibilité destiné principalement aux musiciens non-voyants ou malvoyants utilisant un Yamaha Clavinova CVP.
> Le Raspberry Pi permet de contrôler certaines fonctions du piano depuis un simple clavier USB et fournit un retour vocal directement dans les haut-parleurs du CVP.
> Le projet est actuellement développé et testé sur un **Yamaha CVP-909**.

---

## Project goal

Modern Yamaha CVP instruments provide many functions through a touchscreen.

For visually impaired musicians, some of these functions can be difficult or impossible to access efficiently.

CVP Access provides a simple tactile interface using:

* a Raspberry Pi;
* a standard USB computer keyboard;
* MIDI SysEx commands;
* MIDI DIN communication;
* Yamaha CVP USB Audio;
* offline neural text-to-speech using Piper.

The goal is not to replace the Yamaha interface, but to make the most useful functions accessible without relying on the touchscreen.

---

# Current status

The project is currently a **working prototype tested on a Yamaha CVP-909**.

Validated functions:

* MIDI Song channels 1–16 mute/unmute;
* reading the real mute state of all 16 Song channels;
* automatic channel-state synchronization at application startup;
* reading the current Song tempo;
* reading the current transpose value;
* spoken feedback through the CVP's own speakers;
* independent spoken-feedback volume;
* USB keyboard control;
* offline speech generation;
* automatic MIDI interface detection by device name.

Current hardware tested:

* Yamaha CVP-909;
* Raspberry Pi;
* Prodipe MIDI USB interface;
* Apple Extended USB Keyboard;
* Yamaha CVP USB Audio connection.

Other Yamaha models are **not yet confirmed compatible**.

---

# Architecture

```text
                 USB keyboard
                      │
                      ▼
                Raspberry Pi
                 /          \
                /            \
        MIDI SysEx           USB Audio
             │                   │
             ▼                   │
     USB MIDI interface          │
       Prodipe MIDI              │
             │                   │
          MIDI DIN               │
             │                   │
             ▼                   ▼
        Yamaha CVP-909 ─────► CVP speakers
```

The Raspberry Pi therefore uses two independent communication paths.

### MIDI control

```text
Raspberry Pi
    ↓
Prodipe USB MIDI
    ↓
CVP MIDI IN / OUT
```

### Spoken feedback

```text
Raspberry Pi
    ↓
USB Audio
    ↓
CVP-909
    ↓
CVP speakers
```

---

# Important USB MIDI note

During development, the CVP-909 USB MIDI ports were detected correctly by Linux.

Example:

```text
Clavinova MIDI 1
Clavinova MIDI 2
```

However, the Yamaha SysEx control commands used by this project did **not** operate correctly through the CVP USB MIDI connection in our tests.

The same commands work through an external USB MIDI interface connected to the physical MIDI DIN ports.

Current working configuration:

```text
Raspberry Pi
    ↓ USB
Prodipe MIDI interface
    ↓ MIDI DIN
CVP-909
```

The CVP USB connection is still used successfully for audio playback.

---

# Keyboard mapping

The keyboard layout is currently designed for an **AZERTY keyboard**.

The two rows follow the Yamaha Song-channel logic:

```text
A Z E R T Y U I
1 2 3 4 5 6 7 8
```

```text
Q S D F G H J K
9 10 11 12 13 14 15 16
```

Therefore:

| Key | Song channel |
| --- | -----------: |
| A   |            1 |
| Z   |            2 |
| E   |            3 |
| R   |            4 |
| T   |            5 |
| Y   |            6 |
| U   |            7 |
| I   |            8 |
| Q   |            9 |
| S   |           10 |
| D   |           11 |
| F   |           12 |
| G   |           13 |
| H   |           14 |
| J   |           15 |
| K   |           16 |

Each key toggles the corresponding Song channel:

```text
active → muted
muted  → active
```

---

# Additional controls

Current controls:

```text
F1          Read and announce current tempo

F2          Read and announce current transpose

Arrow Up    Increase spoken-feedback volume

Arrow Down  Decrease spoken-feedback volume

ESC         Request application restart
```

Automatic restart with `ESC` requires the application to be installed as a `systemd` service.

---

# Spoken feedback

The Raspberry Pi sends spoken feedback directly to the CVP through USB Audio.

Examples:

```text
Piste 1 coupée.
Piste 1 activée.

Tempo 100.

Transpose zéro.
Transpose plus 7.

Volume de la voix 70 pour cent.
```

The current project uses **French spoken feedback**, but other languages can easily be added by generating another voice bank.

---

# Text-to-speech

Early tests used `espeak-ng`.

It was very lightweight and responsive, but the voice quality was too robotic for regular use.

The project now uses **Piper**, an offline neural text-to-speech engine.

Current voice tested:

```text
fr_FR-siwis-medium
```

Piper is used only to **generate audio files in advance**.

It is not used for real-time synthesis during normal operation.

---

# Why pre-generated WAV files?

Generating speech in real time on the Raspberry Pi introduced noticeable latency.

The original chain was:

```text
keyboard press
    ↓
load Piper
    ↓
generate speech
    ↓
create WAV
    ↓
play WAV
```

This was too slow.

The current design uses:

```text
keyboard press
    ↓
send MIDI immediately
    ↓
play pre-generated WAV
```

This provides much faster feedback while retaining the higher-quality Piper voice.

---

# Voice files

Song-channel announcements are generated in advance.

Example:

```text
cvp_voice/
├── piste_01_off.wav
├── piste_01_on.wav
├── piste_02_off.wav
├── piste_02_on.wav
├── ...
├── piste_16_off.wav
└── piste_16_on.wav
```

Examples:

```text
piste_01_off.wav
→ "Piste 1 coupée."

piste_01_on.wav
→ "Piste 1 activée."
```

---

# Tempo voice bank

The supported tempo range discovered in the Yamaha protocol is:

```text
5 – 280 BPM
```

A complete set of audio announcements can therefore be generated:

```text
tempo/
├── tempo_005.wav
├── tempo_006.wav
├── ...
├── tempo_083.wav
├── tempo_100.wav
├── tempo_120.wav
├── ...
└── tempo_280.wav
```

Example:

```text
tempo_083.wav
→ "Tempo 83."
```

---

# Transpose voice bank

The supported transpose range is:

```text
-12 to +12 semitones
```

Files are generated as:

```text
transpose/
├── transpose_m12.wav
├── ...
├── transpose_m01.wav
├── transpose_000.wav
├── transpose_p01.wav
├── ...
└── transpose_p12.wav
```

Examples:

```text
transpose_m03.wav
→ "Transpose moins 3."

transpose_000.wav
→ "Transpose zéro."

transpose_p07.wav
→ "Transpose plus 7."
```

---

# Reading real CVP state

One important design choice is that CVP Access does not need to assume the state of the piano.

The Yamaha protocol allows the Raspberry Pi to query the CVP.

At application startup, CVP Access asks for the state of all 16 Song channels.

Example result:

```text
Active channels:
1, 5, 6, 9, 11, 14, 15, 16

Muted channels:
2, 3, 4, 7, 8, 10, 12, 13
```

The Raspberry therefore starts synchronized with the actual piano state.

---

# Reading tempo

Tempo can also be requested from the CVP.

Example Yamaha response:

```text
00 64
```

Hexadecimal:

```text
0x0064 = 100
```

Result:

```text
Tempo: 100 BPM
```

Tests have also successfully returned changed values such as:

```text
Tempo: 83
```

---

# Reading transpose

Transpose can also be read directly from the CVP.

The value is centered around:

```text
0x40 = transpose 0
```

Examples:

```text
0x34 = -12
0x3F = -1
0x40 = 0
0x41 = +1
0x47 = +7
0x4C = +12
```

Validated examples:

```text
Transpose: 0
Transpose: +7
```

---

# Yamaha SysEx protocol

The protocol used by CVP Access was identified with major help from the open-source **ConPianist** project.

General Yamaha message prefix:

```text
F0 43 73 01 52 25 26
```

The CVP-909 has been experimentally confirmed to respond to several of these commands.

---

## Song channel Active property

Property:

```text
0C 00 01 01
```

Song channel indexes:

```text
Channel 1  = 0x10
Channel 2  = 0x11
...
Channel 16 = 0x1F
```

Values:

```text
00 = inactive / muted
01 = active
```

---

## Example: mute Song channel 1

```text
F0 43 73 01 52 25 26
01 01
0C 00 01 01
10
01 00
00 01
00
F7
```

---

## Example: activate Song channel 1

```text
F0 43 73 01 52 25 26
01 01
0C 00 01 01
10
01 00
00 01
01
F7
```

---

## GET Song channel state

Example request for channel 1:

```text
F0 43 73 01 52 25 26
01 00
0C 00 01 01
10
01 00
F7
```

The CVP returns the real channel state.

---

# Tempo property

Property:

```text
08 00 00 01
```

Validated range:

```text
5 – 280 BPM
```

---

# Transpose property

Property:

```text
0A 00 00 01
```

Validated range:

```text
-12 – +12 semitones
```

---

# MIDI reception

One implementation issue discovered during development involved `amidi -d`.

`amidi` displays incoming SysEx bytes immediately, but the output does not necessarily behave as newline-terminated messages.

A normal Python loop such as:

```python
for line in process.stdout:
```

therefore failed to receive completed messages correctly.

CVP Access instead parses the MIDI dump stream and considers:

```text
F0 = beginning of SysEx message
F7 = end of SysEx message
```

This allowed reliable GET responses for:

* Song-channel state;
* tempo;
* transpose.

---

# Linux / Raspberry Pi requirements

Typical packages:

```bash
sudo apt update

sudo apt install -y \
    python3 \
    python3-venv \
    python3-evdev \
    alsa-utils
```

Python keyboard access uses:

```text
evdev
```

MIDI communication currently uses:

```text
amidi
```

Audio playback currently uses:

```text
aplay
```

---

# Piper installation

Create a Python environment:

```bash
python3 -m venv ~/piper-env
source ~/piper-env/bin/activate
```

Install Piper:

```bash
pip install piper-tts
```

Create a voice directory:

```bash
mkdir -p ~/piper-voices
cd ~/piper-voices
```

Download a compatible French model, for example:

```text
fr_FR-siwis-medium
```

Voice-model licensing must be checked before redistributing any Piper voice model.

CVP Access should therefore distribute **voice-generation scripts**, not the voice model itself.

---

# Repository layout

Planned repository structure:

```text
cvp-access/
├── README.md
├── LICENSE
├── requirements.txt
├── cvp_access.py
│
├── tools/
│   ├── generate_track_voices.py
│   └── generate_value_voices.py
│
├── systemd/
│   └── cvp-access.service
│
├── docs/
│   └── yamaha-protocol.md
│
└── .gitignore
```

Generated files should not be committed:

```text
*.wav
*.onnx
piper-env/
cvp_voice/
__pycache__/
```

---

# Automatic startup

The final installation is intended to run without a monitor, mouse or terminal.

Target behaviour:

```text
Raspberry Pi power on
        ↓
CVP Access starts automatically
        ↓
MIDI interface detected
        ↓
16 Song channel states read
        ↓
tempo read
        ↓
transpose read
        ↓
spoken message:
"Interface prête."
```

The application will eventually be managed using `systemd`.

If the program crashes:

```text
systemd → automatic restart
```

If the user presses `ESC`:

```text
application exits
      ↓
systemd restarts it
      ↓
CVP state is synchronized again
```

---

# Accessibility design philosophy

The objective is not to expose every CVP parameter.

The priority is to expose functions that are difficult to access without vision and which provide real musical value.

The interface should remain:

* predictable;
* tactile;
* fast;
* easy to memorize;
* usable without a screen;
* independent from cloud services;
* able to report the real state of the instrument.

---

# Future development

Possible future functions already identified in the Yamaha protocol include:

* Play;
* Pause;
* Stop;
* Song position;
* individual channel volume;
* pan;
* reverb;
* Voice selection;
* Right Hand part;
* Left Hand part;
* Backing part;
* Guide functions;
* octave;
* split point;
* Local Control;
* Master Tune;
* Touch Curve;
* VRM;
* Damper Resonance;
* String Resonance.

These functions are **not yet confirmed on the CVP-909 unless explicitly documented as tested**.

---

# Compatibility

| Device                     | Status                                  |
| -------------------------- | --------------------------------------- |
| Yamaha CVP-909             | ✅ Tested                                |
| Other Yamaha CVP models    | ⚠️ Not tested                           |
| Yamaha CSP series          | ⚠️ Related protocol, not validated here |
| Raspberry Pi               | ✅ Tested                                |
| Prodipe MIDI USB interface | ✅ Tested                                |

Community testing on other Yamaha models is welcome.

---

# Credits

This project would not have been possible without the work done by the **ConPianist** project and its author, which provided essential information about Yamaha's Smart Pianist / CSP SysEx protocol.

ConPianist:

`https://github.com/hugbug/conpianist`

CVP Access independently tests and implements the required protocol functions on a Yamaha CVP-909 for accessibility purposes.

---

# Disclaimer

CVP Access is an **unofficial community project**.

It is not affiliated with, endorsed by, sponsored by, or supported by Yamaha Corporation.

Yamaha, Clavinova, CVP and Smart Pianist are trademarks of their respective owners.

Use the software at your own risk.

---

# License

The project is intended to be distributed as open-source software.

Before the first stable release, a `LICENSE` file should be added to the repository.

GPL-3.0 is currently the preferred license due to the open-source ecosystem and upstream projects used during development.

---

# Contributing

Contributions are welcome, especially from users able to test:

* other CVP models;
* CSP models;
* different USB MIDI interfaces;
* other keyboard layouts;
* additional languages;
* additional Yamaha SysEx functions.

When reporting compatibility, please include:

```text
Yamaha model
Raspberry Pi model
Linux distribution
MIDI interface
Connection method
Command tested
Result
```

---

# Project status

**Experimental but functional.**

Current development target:

```text
Yamaha CVP-909
+
Raspberry Pi
+
USB keyboard
+
MIDI SysEx
+
spoken accessibility feedback
```
