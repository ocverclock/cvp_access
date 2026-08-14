#!/usr/bin/env python3

import array
import atexit
import fcntl
import os
import glob
import hashlib
import io
import queue
import re
import subprocess
import sys
import threading
import time
import wave
from pathlib import Path

from evdev import InputDevice, ecodes


# ============================================================
# CONFIGURATION
# ============================================================

VOICE_DIR = Path("/home/pi/cvp_voice")

AUDIO_DEVICE = "plughw:CARD=Clavinova,DEV=0"
MIDI_NAME = "ProdipeMIDIlilo MIDI 1"

# Volume initial de la voix
voice_volume = 80

HEADER = [
    0xF0, 0x43, 0x73, 0x01,
    0x52, 0x25, 0x26
]

PROP_ACTIVE = [0x0C, 0x00, 0x01, 0x01]
PROP_TEMPO = [0x08, 0x00, 0x00, 0x01]
PROP_TRANSPOSE = [0x0A, 0x00, 0x00, 0x01]
PROP_VOLUME = [0x0C, 0x00, 0x00, 0x01]
PROP_SONG_PLAY = [0x04, 0x00, 0x05, 0x01]
PROP_SONG_POSITION = [0x04, 0x00, 0x0A, 0x01]

SONG_STOP = 0x00
SONG_PLAY = 0x01
SONG_PAUSE = 0x02

STYLE_VOLUME_INDEX = 0x51
STYLE_VOLUME_STEP = 5

# 8 parties d'accompagnement Style Yamaha
# Ordre validé sur CVP-905 :
# RHY1 RHY2 BASS CHD1 CHD2 PAD PHR1 PHR2
STYLE_PART_HEADER = [
    0xF0, 0x43, 0x73, 0x01,
    0x51, 0x05, 0x00, 0x00, 0x08
]

STYLE_PART_NAMES = [
    "rhythm_1",
    "rhythm_2",
    "bass",
    "chord_1",
    "chord_2",
    "pad",
    "phrase_1",
    "phrase_2"
]


VOICE_PART_LAYER_INDEX = 0x01
VOICE_PART_LEFT_INDEX = 0x02

STYLE_PART_LABELS = [
    "Rhythm 1",
    "Rhythm 2",
    "Bass",
    "Chord 1",
    "Chord 2",
    "Pad",
    "Phrase 1",
    "Phrase 2"
]

# Un changement de Style reprogramme les canaux MIDI 9 à 16.
# Quand les 8 Program Change sont observés dans cette fenêtre,
# le cache des parties Style est remis à ON.
STYLE_CHANNELS = set(range(8, 16))
STYLE_CHANGE_WINDOW = 1.5


# ============================================================
# CLAVIER AZERTY
#
# A Z E R T Y U I = 1 à 8
# Q S D F G H J K = 9 à 16
# ============================================================

KEY_TO_STYLE_PART = {
    ecodes.KEY_1: 0,     # &  = Rhythm 1
    ecodes.KEY_2: 1,     # é  = Rhythm 2
    ecodes.KEY_3: 2,     # "  = Bass
    ecodes.KEY_4: 3,     # '  = Chord 1
    ecodes.KEY_5: 4,     # (  = Chord 2
    ecodes.KEY_6: 5,     # -  = Pad
    ecodes.KEY_7: 6,     # è  = Phrase 1
    ecodes.KEY_8: 7,     # _  = Phrase 2
}


KEY_TO_VOICE_PART = {
    ecodes.KEY_9: ("layer", VOICE_PART_LAYER_INDEX),  # ç = Layer / Dual
    ecodes.KEY_0: ("left", VOICE_PART_LEFT_INDEX),    # à = Left
}


KEY_TO_TRACK = {

    ecodes.KEY_Q: 1,     # A
    ecodes.KEY_W: 2,     # Z
    ecodes.KEY_E: 3,     # E
    ecodes.KEY_R: 4,     # R
    ecodes.KEY_T: 5,     # T
    ecodes.KEY_Y: 6,     # Y
    ecodes.KEY_U: 7,     # U
    ecodes.KEY_I: 8,     # I

    ecodes.KEY_A: 9,     # Q
    ecodes.KEY_S: 10,    # S
    ecodes.KEY_D: 11,    # D
    ecodes.KEY_F: 12,    # F
    ecodes.KEY_G: 13,    # G
    ecodes.KEY_H: 14,    # H
    ecodes.KEY_J: 15,    # J
    ecodes.KEY_K: 16,    # K
}


tracks = {
    n: None
    for n in range(1, 17)
}


audio_process = None
midi_process = None
midi_queue = queue.Queue()
style_volume = None

# Le protocole Style ne fournit pas de GET validé pour ces 8 états.
# On maintient donc un cache déterministe :
# - forcé à tout ON au démarrage
# - remis à tout ON à chaque changement de Style détecté.
style_parts = [True] * 8
style_parts_lock = threading.Lock()

style_change_channels = set()
style_change_started = None

instance_lock = None


# ============================================================
# PROTECTION MONO-INSTANCE / NETTOYAGE
# ============================================================

def acquire_single_instance():

    global instance_lock

    lock_dir = Path.home() / ".cache"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "cvp_access.lock"
    instance_lock = open(lock_path, "a+")

    try:
        fcntl.flock(
            instance_lock.fileno(),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

    except BlockingIOError:
        instance_lock.close()
        instance_lock = None

        print(
            "CVP Access est déjà lancé."
        )
        sys.exit(1)

    instance_lock.seek(0)
    instance_lock.truncate()
    instance_lock.write(
        str(os.getpid())
    )
    instance_lock.flush()


def cleanup():

    global audio_process
    global midi_process
    global instance_lock

    if (
        audio_process is not None
        and audio_process.poll() is None
    ):
        audio_process.terminate()

        try:
            audio_process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            audio_process.kill()

    if (
        midi_process is not None
        and midi_process.poll() is None
    ):
        midi_process.terminate()

        try:
            midi_process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            midi_process.kill()

    if instance_lock is not None:

        try:
            fcntl.flock(
                instance_lock.fileno(),
                fcntl.LOCK_UN
            )
        except OSError:
            pass

        instance_lock.close()
        instance_lock = None


atexit.register(cleanup)


# ============================================================
# MIDI : recherche interface
# ============================================================

def find_midi_port():

    result = subprocess.run(
        ["amidi", "-l"],
        capture_output=True,
        text=True
    )

    for line in result.stdout.splitlines():

        if MIDI_NAME in line:

            match = re.search(
                r"(hw:\d+,\d+,\d+)",
                line
            )

            if match:
                return match.group(1)

    return None


# ============================================================
# RECEPTION MIDI PERMANENTE
# ============================================================

def midi_receiver(port):

    global midi_process
    global style_change_started

    midi_process = subprocess.Popen(
        [
            "amidi",
            "-p", port,
            "-d"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )

    # Parser SysEx
    message = []

    # Parser MIDI canal / running status
    running_status = None
    data_needed = 0
    channel_data = []

    hex_byte = ""

    while True:

        char = midi_process.stdout.read(1)

        if char == "":
            print("Récepteur MIDI arrêté.")

            err = midi_process.stderr.read().strip()
            if err:
                print("Erreur réception MIDI :", err)

            return

        if char not in "0123456789abcdefABCDEF":
            hex_byte = ""
            continue

        hex_byte += char

        if len(hex_byte) < 2:
            continue

        value = int(hex_byte, 16)
        hex_byte = ""

        now = time.monotonic()

        # Expiration d'un burst de changement de Style incomplet.
        if (
            style_change_started is not None
            and now - style_change_started > STYLE_CHANGE_WINDOW
        ):
            style_change_channels.clear()
            style_change_started = None

        # Début SysEx : priorité au parser SysEx.
        if value == 0xF0:
            message = [0xF0]
            running_status = None
            channel_data.clear()
            continue

        # Si un SysEx est en cours, ne surtout pas interpréter
        # ses octets comme des messages MIDI canal.
        if message:

            message.append(value)

            if value == 0xF7:
                midi_queue.put(message.copy())
                message = []

            continue

        # MIDI temps réel : peut apparaître entre d'autres octets.
        if value >= 0xF8:
            continue

        # Nouveau status MIDI.
        if value & 0x80:

            # Les status système hors SysEx annulent le running status.
            if value >= 0xF0:
                running_status = None
                channel_data.clear()
                data_needed = 0
                continue

            running_status = value
            channel_data.clear()

            command = value & 0xF0

            if command in (0xC0, 0xD0):
                data_needed = 1
            else:
                data_needed = 2

            continue

        # Octet de données sans running status connu.
        if running_status is None:
            continue

        channel_data.append(value)

        if len(channel_data) < data_needed:
            continue

        command = running_status & 0xF0
        channel = running_status & 0x0F

        # Changement de Style :
        # les 8 parties Style (canaux MIDI 9 à 16) reçoivent
        # chacune un Program Change C8..CF.
        if (
            command == 0xC0
            and channel in STYLE_CHANNELS
        ):

            if style_change_started is None:
                style_change_started = now

            style_change_channels.add(channel)

            if style_change_channels == STYLE_CHANNELS:

                with style_parts_lock:
                    style_parts[:] = [True] * 8

                elapsed = now - style_change_started

                print(
                    "Changement de Style détecté "
                    f"({elapsed:.3f} s) "
                    "-> 8 parties Style = ON"
                )

                style_change_channels.clear()
                style_change_started = None

        # Running status reste valide.
        channel_data.clear()

# ============================================================
# ENVOI SYSEX
# ============================================================

def send_sysex(port, message):

    text = " ".join(
        f"{x:02X}"
        for x in message
    )

    result = subprocess.run(
        [
            "amidi",
            "-p", port,
            "-S", text
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return result.returncode == 0


def set_style_parts(port, states):

    message = (
        STYLE_PART_HEADER
        + [
            0x01 if state else 0x00
            for state in states
        ]
        + [0xF7]
    )

    return send_sysex(
        port,
        message
    )


# ============================================================
# GET YAMAHA
# ============================================================

def get_property(port, prop, index, timeout=0.5):

    # Vide les anciennes réponses
    while True:
        try:
            midi_queue.get_nowait()
        except queue.Empty:
            break

    message = (
        HEADER
        + [0x01, 0x00]
        + prop
        + [index, 0x01, 0x00]
        + [0xF7]
    )

    if not send_sysex(port, message):
        return None

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        remaining = deadline - time.monotonic()

        try:
            response = midi_queue.get(
                timeout=remaining
            )

        except queue.Empty:
            return None

        if len(response) < 19:
            continue

        if response[:7] != HEADER:
            continue

        # Réponse Yamaha GET
        if response[7:9] != [0x00, 0x00]:
            continue

        if response[9:13] != prop:
            continue

        if response[13] != index:
            continue

        length = (
            (response[16] << 7)
            | response[17]
        )

        data = response[
            18:18 + length
        ]

        return data

    return None


# ============================================================
# ACTIVE / MUTE
# ============================================================

def get_track_state(port, track):

    index = 0x0F + track

    data = get_property(
        port,
        PROP_ACTIVE,
        index
    )

    if not data:
        return None

    return data[0] != 0


def set_track_state(port, track, active):

    index = 0x0F + track
    value = 0x01 if active else 0x00

    message = (
        HEADER
        + [0x01, 0x01]
        + PROP_ACTIVE
        + [index, 0x01, 0x00]
        + [0x00, 0x01]
        + [value]
        + [0xF7]
    )

    return send_sysex(
        port,
        message
    )


def get_voice_part_state(port, index):

    data = get_property(
        port,
        PROP_ACTIVE,
        index
    )

    if not data:
        return None

    return data[0] != 0


def set_voice_part_state(port, index, active):

    value = 0x01 if active else 0x00

    message = (
        HEADER
        + [0x01, 0x01]
        + PROP_ACTIVE
        + [index, 0x01, 0x00]
        + [0x00, 0x01]
        + [value]
        + [0xF7]
    )

    return send_sysex(
        port,
        message
    )


# ============================================================
# TEMPO
# ============================================================

def get_tempo(port):

    data = get_property(
        port,
        PROP_TEMPO,
        0x00
    )

    if not data or len(data) != 2:
        return None

    return (
        (data[0] << 7)
        | data[1]
    )



# ============================================================
# SONG : TRANSPORT / POSITION
# ============================================================

def get_song_play_state(port):

    data = get_property(
        port,
        PROP_SONG_PLAY,
        0x00
    )

    if not data or len(data) != 1:
        return None

    if data[0] not in (
        SONG_STOP,
        SONG_PLAY,
        SONG_PAUSE
    ):
        return None

    return data[0]


def set_song_play_state(port, state):

    if state not in (
        SONG_STOP,
        SONG_PLAY,
        SONG_PAUSE
    ):
        return False

    message = (
        HEADER
        + [0x01, 0x01]
        + PROP_SONG_PLAY
        + [0x00, 0x01, 0x00]
        + [0x00, 0x01]
        + [state]
        + [0xF7]
    )

    return send_sysex(
        port,
        message
    )


def verify_song_play_state(
    port,
    expected,
    attempts=5
):

    time.sleep(0.10)

    last_state = None

    for attempt in range(attempts):

        state = get_song_play_state(port)

        if state is not None:
            last_state = state

            if state == expected:
                return state

        if attempt < attempts - 1:
            time.sleep(0.05)

    print(
        "Vérification transport Song : "
        f"attendu {expected}, "
        f"lu "
        + (
            "inconnu"
            if last_state is None
            else str(last_state)
        )
    )

    return None


def get_song_position(port):

    data = get_property(
        port,
        PROP_SONG_POSITION,
        0x00
    )

    if not data or len(data) != 4:
        return None

    # Yamaha SysEx transporte les valeurs sur des octets 7 bits.
    measure = (
        (data[0] << 7)
        | data[1]
    )

    beat = (
        (data[2] << 7)
        | data[3]
    )

    return measure, beat


# ============================================================
# TRANSPOSE
# ============================================================

def get_transpose(port):

    data = get_property(
        port,
        PROP_TRANSPOSE,
        0x02
    )

    if not data:
        return None

    return data[0] - 0x40


# ============================================================
# VOLUME ACCOMPAGNEMENT STYLE
# ============================================================

def get_style_volume(port):

    data = get_property(
        port,
        PROP_VOLUME,
        STYLE_VOLUME_INDEX
    )

    if not data:
        return None

    return data[0]


def set_style_volume(port, value):

    value = max(
        0,
        min(127, value)
    )

    message = (
        HEADER
        + [0x01, 0x01]
        + PROP_VOLUME
        + [STYLE_VOLUME_INDEX, 0x01, 0x00]
        + [0x00, 0x01]
        + [value]
        + [0xF7]
    )

    return send_sysex(
        port,
        message
    )


def verify_track_state(
    port,
    track,
    expected,
    attempts=5
):

    # Laisse au CVP le temps d'appliquer le SET
    # et d'émettre d'éventuelles réponses spontanées.
    time.sleep(0.10)

    last_state = None

    for attempt in range(attempts):

        state = get_track_state(
            port,
            track
        )

        if state is not None:
            last_state = state

            if state == expected:
                return state

        if attempt < attempts - 1:
            time.sleep(0.05)

    print(
        f"Vérification piste {track:02d} : "
        f"attendu {'ON' if expected else 'OFF'}, "
        f"lu "
        + (
            "inconnu"
            if last_state is None
            else ("ON" if last_state else "OFF")
        )
    )

    return None


def verify_voice_part_state(
    port,
    index,
    expected,
    attempts=5
):

    time.sleep(0.10)

    last_state = None

    for attempt in range(attempts):

        state = get_voice_part_state(
            port,
            index
        )

        if state is not None:
            last_state = state

            if state == expected:
                return state

        if attempt < attempts - 1:
            time.sleep(0.05)

    print(
        "Vérification partie clavier : "
        f"attendu {'ON' if expected else 'OFF'}, "
        f"lu "
        + (
            "inconnu"
            if last_state is None
            else ("ON" if last_state else "OFF")
        )
    )

    return None


def verify_style_volume(
    port,
    expected,
    attempts=5
):

    # Important : juste après un SET, le CVP peut encore
    # répondre brièvement avec l'ancienne valeur.
    # On attend donc avant le premier GET de contrôle.
    time.sleep(0.10)

    last_value = None

    for attempt in range(attempts):

        value = get_style_volume(port)

        if value is not None:
            last_value = value

            # Une réponse n'est validée que si elle correspond
            # réellement à la valeur que nous venons d'envoyer.
            if value == expected:
                return value

        if attempt < attempts - 1:
            time.sleep(0.05)

    print(
        "Vérification volume Style : "
        f"attendu {expected}, "
        f"lu "
        + (
            "inconnu"
            if last_value is None
            else str(last_value)
        )
    )

    return None


# ============================================================
# AUDIO : volume logiciel
# ============================================================

def create_scaled_wav(source, volume):

    cache_dir = Path.home() / ".cache" / "cvp_voice_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    destination = (
        cache_dir
        / f"{source.stem}_v{volume}.wav"
    )

    if destination.exists():
        return destination

    gain = volume / 100.0

    with wave.open(
        str(source),
        "rb"
    ) as src:

        params = src.getparams()
        frames = src.readframes(
            src.getnframes()
        )

    # Piper génère du PCM 16 bits.
    if params.sampwidth != 2:
        return source

    samples = array.array("h")
    samples.frombytes(frames)

    if sys.byteorder == "big":
        samples.byteswap()

    for i in range(len(samples)):

        value = int(
            samples[i] * gain
        )

        value = max(
            -32768,
            min(32767, value)
        )

        samples[i] = value

    if sys.byteorder == "big":
        samples.byteswap()

    with wave.open(
        str(destination),
        "wb"
    ) as dst:

        dst.setparams(params)
        dst.writeframes(
            samples.tobytes()
        )

    return destination


def play_voice(filename):

    global audio_process
    global voice_volume

    if not filename.exists():

        print(
            "WAV absent :",
            filename
        )

        return

    scaled = create_scaled_wav(
        filename,
        voice_volume
    )

    start_audio(scaled)



def start_audio(filename):

    global audio_process

    if (
        audio_process
        and audio_process.poll() is None
    ):
        audio_process.terminate()

    audio_process = subprocess.Popen(
        [
            "aplay",
            "-q",
            "-D", AUDIO_DEVICE,
            str(filename)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def play_voice_sequence(files):

    global voice_volume

    files = [
        Path(filename)
        for filename in files
    ]

    missing = [
        filename
        for filename in files
        if not filename.exists()
    ]

    if missing:

        for filename in missing:
            print(
                "WAV absent :",
                filename
            )

        return

    # On applique d'abord le volume logiciel à chaque fragment.
    scaled_files = [
        create_scaled_wav(
            filename,
            voice_volume
        )
        for filename in files
    ]

    cache_dir = (
        Path.home()
        / ".cache"
        / "cvp_voice_sequences"
    )
    cache_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    key = "|".join(
        str(filename)
        for filename in scaled_files
    )

    digest = hashlib.sha1(
        key.encode("utf-8")
    ).hexdigest()[:16]

    destination = (
        cache_dir
        / f"sequence_{digest}.wav"
    )

    if not destination.exists():

        params = None
        frames = []

        for filename in scaled_files:

            with wave.open(
                str(filename),
                "rb"
            ) as wav:

                current_params = wav.getparams()

                if params is None:
                    params = current_params

                else:

                    if (
                        current_params.nchannels
                        != params.nchannels
                        or current_params.sampwidth
                        != params.sampwidth
                        or current_params.framerate
                        != params.framerate
                        or current_params.comptype
                        != params.comptype
                    ):
                        print(
                            "Formats WAV incompatibles :",
                            filename
                        )
                        return

                frames.append(
                    wav.readframes(
                        wav.getnframes()
                    )
                )

        with wave.open(
            str(destination),
            "wb"
        ) as out:

            out.setparams(params)

            for block in frames:
                out.writeframes(block)

    start_audio(destination)


def number_voice_files(value):

    # Pour l'annonce de position, on limite volontairement
    # la banque vocale aux mesures 0 à 100.
    if value < 0 or value > 100:
        return []

    return [
        VOICE_DIR
        / "numbers"
        / f"number_{value:03d}.wav"
    ]


# ============================================================
# ANNONCES
# ============================================================

def announce_track(track, active):

    state = (
        "on"
        if active
        else "off"
    )

    play_voice(
        VOICE_DIR
        / f"piste_{track:02d}_{state}.wav"
    )


def announce_tempo(tempo):

    play_voice(
        VOICE_DIR
        / "tempo"
        / f"tempo_{tempo:03d}.wav"
    )


def announce_transpose(value):

    if value < 0:

        name = (
            f"transpose_m{abs(value):02d}.wav"
        )

    elif value > 0:

        name = (
            f"transpose_p{value:02d}.wav"
        )

    else:

        name = "transpose_000.wav"

    play_voice(
        VOICE_DIR
        / "transpose"
        / name
    )


def announce_volume():

    play_voice(
        VOICE_DIR
        / "volume"
        / f"volume_{voice_volume:03d}.wav"
    )


def announce_style_volume(value):

    play_voice(
        VOICE_DIR
        / "style_volume"
        / f"style_volume_{value:03d}.wav"
    )


def announce_style_part(part, active):

    state = (
        "on"
        if active
        else "off"
    )

    play_voice(
        VOICE_DIR
        / "style_part"
        / f"{STYLE_PART_NAMES[part]}_{state}.wav"
    )


def announce_voice_part(name, active):

    state = (
        "on"
        if active
        else "off"
    )

    play_voice(
        VOICE_DIR
        / "voice_part"
        / f"{name}_{state}.wav"
    )



def announce_song_state(state):

    names = {
        SONG_STOP: "stop.wav",
        SONG_PLAY: "lecture.wav",
        SONG_PAUSE: "pause.wav",
    }

    filename = names.get(state)

    if filename is None:
        return

    play_voice(
        VOICE_DIR
        / "transport"
        / filename
    )


def announce_song_position(measure, beat):

    if measure > 100:
        print(
            "Annonce vocale limitée à 100 mesures."
        )
        return

    files = [
        VOICE_DIR
        / "words"
        / "mesure.wav"
    ]

    files.extend(
        number_voice_files(measure)
    )

    files.append(
        VOICE_DIR
        / "words"
        / "temps.wav"
    )

    files.extend(
        number_voice_files(beat)
    )

    play_voice_sequence(files)


# ============================================================
# SYNCHRONISATION AU DEMARRAGE
# ============================================================

def sync_tracks(port):

    print()
    print("Lecture état des 16 pistes...")

    active_tracks = []
    muted_tracks = []

    for track in range(1, 17):

        state = get_track_state(
            port,
            track
        )

        tracks[track] = state

        if state is True:
            active_tracks.append(track)

        elif state is False:
            muted_tracks.append(track)

        else:
            print(
                f"Piste {track:02d} : pas de réponse"
            )

    print(
        "Actives :",
        active_tracks
    )

    print(
        "Coupées :",
        muted_tracks
    )


# ============================================================
# CLAVIER
# ============================================================

def find_keyboard():

    keyboards = sorted(
        glob.glob(
            "/dev/input/by-id/*-event-kbd"
        )
    )

    if not keyboards:

        print(
            "Aucun clavier trouvé."
        )

        sys.exit(1)

    print(
        "Clavier :",
        keyboards[0]
    )

    return InputDevice(
        keyboards[0]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    global voice_volume
    global style_volume

    acquire_single_instance()

    print()
    print("CVP-905 ACCESS V3.4.1")
    print("=================")

    port = find_midi_port()

    if port is None:

        print(
            "Prodipe MIDI introuvable."
        )

        sys.exit(1)

    print(
        "MIDI :",
        port,
        "-",
        MIDI_NAME
    )

    print(
        "Audio :",
        AUDIO_DEVICE
    )

    # Démarre le récepteur MIDI
    thread = threading.Thread(
        target=midi_receiver,
        args=(port,),
        daemon=True
    )

    thread.start()

    # Laisse ALSA ouvrir le port
    time.sleep(0.3)

    # Synchronisation réelle
    sync_tracks(port)

    tempo = get_tempo(port)
    transpose = get_transpose(port)
    style_volume = get_style_volume(port)

    # Comme aucun GET des 8 mutes Style n'est validé,
    # on impose un état connu au démarrage.
    with style_parts_lock:
        style_parts[:] = [True] * 8
        startup_style_parts = style_parts.copy()

    if set_style_parts(
        port,
        startup_style_parts
    ):
        print(
            "Pistes Style : toutes actives"
        )
    else:
        print(
            "Impossible d'initialiser les pistes Style."
        )

    print(
        "Tempo :",
        tempo
    )

    print(
        "Transpose :",
        transpose
    )

    print(
        "Volume Style :",
        style_volume
    )

    keyboard = find_keyboard()

    print()
    print(
        '& É " \' ( - È _ Ç À = '
        "RHY1 RHY2 BASS CHD1 CHD2 PAD PHR1 PHR2 LAYER LEFT"
    )

    print(
        "A Z E R T Y U I = pistes 1 à 8"
    )

    print(
        "Q S D F G H J K = pistes 9 à 16"
    )

    print()
    print(
        "F1 = annoncer tempo"
    )

    print(
        "F2 = annoncer transpose"
    )

    print(
        "Espace = lecture / pause Song"
    )

    print(
        "Entrée = stop Song"
    )

    print(
        "P = annoncer mesure / temps"
    )

    print(
        "↑  = volume voix +"
    )

    print(
        "↓  = volume voix -"
    )

    print(
        "Page Up   = volume Style +5"
    )

    print(
        "Page Down = volume Style -5"
    )

    print(
        "ESC = quitter"
    )

    print()
    print("Prêt.")
    print()

    for event in keyboard.read_loop():

        if event.type != ecodes.EV_KEY:
            continue

        if event.value != 1:
            continue

        # Relancer
        if event.code == ecodes.KEY_ESC:
            print("Redémarrage demandé...")
            sys.exit(0)

        # Volume +
        if event.code == ecodes.KEY_UP:

            voice_volume = min(
                100,
                voice_volume + 10
            )

            print(
                "Volume voix :",
                voice_volume
            )

            announce_volume()
            continue

        # Volume -
        if event.code == ecodes.KEY_DOWN:

            voice_volume = max(
                10,
                voice_volume - 10
            )

            print(
                "Volume voix :",
                voice_volume
            )

            announce_volume()
            continue

        # Volume Style +
        # Toujours relire le CVP avant de modifier.
        if event.code == ecodes.KEY_PAGEUP:

            current_volume = get_style_volume(port)

            if current_volume is None:
                style_volume = None
                print("Impossible de lire le volume Style.")
                continue

            new_volume = min(
                127,
                current_volume + STYLE_VOLUME_STEP
            )

            # Déjà à la limite haute : aucune supposition,
            # on annonce simplement la valeur réellement lue.
            if new_volume == current_volume:
                style_volume = current_volume

                print(
                    "Volume Style :",
                    style_volume
                )

                announce_style_volume(
                    style_volume
                )
                continue

            if not set_style_volume(
                port,
                new_volume
            ):
                style_volume = None
                print("Impossible de modifier le volume Style.")
                continue

            # Relire après le SET : seule la réponse du CVP
            # est considérée comme valeur réelle.
            verified_volume = verify_style_volume(
                port,
                new_volume
            )

            if verified_volume is None:
                style_volume = None
                print(
                    "Volume Style modifié, "
                    "mais vérification impossible."
                )
                continue

            style_volume = verified_volume

            print(
                "Volume Style :",
                style_volume
            )

            announce_style_volume(
                style_volume
            )

            continue

        # Volume Style -
        # Toujours relire le CVP avant de modifier.
        if event.code == ecodes.KEY_PAGEDOWN:

            current_volume = get_style_volume(port)

            if current_volume is None:
                style_volume = None
                print("Impossible de lire le volume Style.")
                continue

            new_volume = max(
                0,
                current_volume - STYLE_VOLUME_STEP
            )

            # Déjà à la limite basse.
            if new_volume == current_volume:
                style_volume = current_volume

                print(
                    "Volume Style :",
                    style_volume
                )

                announce_style_volume(
                    style_volume
                )
                continue

            if not set_style_volume(
                port,
                new_volume
            ):
                style_volume = None
                print("Impossible de modifier le volume Style.")
                continue

            verified_volume = verify_style_volume(
                port,
                new_volume
            )

            if verified_volume is None:
                style_volume = None
                print(
                    "Volume Style modifié, "
                    "mais vérification impossible."
                )
                continue

            style_volume = verified_volume

            print(
                "Volume Style :",
                style_volume
            )

            announce_style_volume(
                style_volume
            )

            continue

        # Song : lecture / pause
        if event.code == ecodes.KEY_SPACE:

            current_state = get_song_play_state(
                port
            )

            if current_state is None:
                print(
                    "Impossible de lire l'état du Song."
                )
                continue

            # Stop ou Pause -> Lecture
            # Lecture -> Pause
            if current_state == SONG_PLAY:
                target_state = SONG_PAUSE
            else:
                target_state = SONG_PLAY

            if not set_song_play_state(
                port,
                target_state
            ):
                print(
                    "Impossible de modifier "
                    "l'état du Song."
                )
                continue

            verified_state = verify_song_play_state(
                port,
                target_state
            )

            if verified_state is None:
                print(
                    "Transport Song modifié, "
                    "mais vérification impossible."
                )
                continue

            print(
                "Song ->",
                {
                    SONG_STOP: "STOP",
                    SONG_PLAY: "PLAY",
                    SONG_PAUSE: "PAUSE",
                }[verified_state]
            )

            announce_song_state(
                verified_state
            )

            continue

        # Song : stop
        if event.code in (
            ecodes.KEY_ENTER,
            ecodes.KEY_KPENTER
        ):

            current_state = get_song_play_state(
                port
            )

            if current_state is None:
                print(
                    "Impossible de lire l'état du Song."
                )
                continue

            if current_state == SONG_STOP:
                print("Song -> STOP")
                announce_song_state(
                    SONG_STOP
                )
                continue

            if not set_song_play_state(
                port,
                SONG_STOP
            ):
                print(
                    "Impossible d'arrêter le Song."
                )
                continue

            verified_state = verify_song_play_state(
                port,
                SONG_STOP
            )

            if verified_state is None:
                print(
                    "Stop envoyé, "
                    "mais vérification impossible."
                )
                continue

            print("Song -> STOP")

            announce_song_state(
                verified_state
            )

            continue

        # Position Song
        if event.code == ecodes.KEY_P:

            position = get_song_position(
                port
            )

            if position is None:
                print(
                    "Impossible de lire "
                    "la position du Song."
                )
                continue

            measure, beat = position

            print(
                f"Position : mesure {measure}, "
                f"temps {beat}"
            )

            announce_song_position(
                measure,
                beat
            )

            continue

        # Tempo
        if event.code == ecodes.KEY_F1:

            tempo = get_tempo(port)

            if tempo is not None:

                print(
                    "Tempo :",
                    tempo
                )

                announce_tempo(
                    tempo
                )

            else:

                print(
                    "Impossible de lire le tempo."
                )

            continue

        # Transpose
        if event.code == ecodes.KEY_F2:

            transpose = get_transpose(
                port
            )

            if transpose is not None:

                print(
                    "Transpose :",
                    transpose
                )

                announce_transpose(
                    transpose
                )

            else:

                print(
                    "Impossible de lire le transpose."
                )

            continue

        # Layer / Left
        voice_part = KEY_TO_VOICE_PART.get(
            event.code
        )

        if voice_part is not None:

            voice_name, voice_index = voice_part

            current = get_voice_part_state(
                port,
                voice_index
            )

            if current is None:
                print(
                    f"Etat {voice_name} inconnu."
                )
                continue

            new_state = not current

            if not set_voice_part_state(
                port,
                voice_index,
                new_state
            ):
                print(
                    f"Impossible de modifier {voice_name}."
                )
                continue

            verified_state = verify_voice_part_state(
                port,
                voice_index,
                new_state
            )

            if verified_state is None:
                print(
                    f"{voice_name} modifié, "
                    "mais vérification impossible."
                )
                continue

            print(
                f"{voice_name.capitalize()} ->",
                "ON"
                if verified_state
                else "OFF"
            )

            announce_voice_part(
                voice_name,
                verified_state
            )

            continue

        # Parties Style
        style_part = KEY_TO_STYLE_PART.get(
            event.code
        )

        if style_part is not None:

            with style_parts_lock:
                new_style_parts = style_parts.copy()

            new_style_parts[style_part] = (
                not new_style_parts[style_part]
            )

            if not set_style_parts(
                port,
                new_style_parts
            ):
                print(
                    "Impossible de modifier "
                    f"{STYLE_PART_LABELS[style_part]}."
                )
                continue

            with style_parts_lock:
                style_parts[:] = new_style_parts
                verified_state = style_parts[style_part]

            print(
                f"Style {STYLE_PART_LABELS[style_part]} ->",
                "ON"
                if verified_state
                else "OFF"
            )

            announce_style_part(
                style_part,
                verified_state
            )

            continue

        # Pistes Song
        track = KEY_TO_TRACK.get(
            event.code
        )

        if track is None:
            continue

        # Toujours demander l'état réel au CVP avant le toggle.
        current = get_track_state(
            port,
            track
        )

        if current is None:
            tracks[track] = None

            print(
                f"Etat piste {track} inconnu."
            )

            continue

        new_state = not current

        if not set_track_state(
            port,
            track,
            new_state
        ):
            tracks[track] = None

            print(
                f"Impossible de modifier la piste {track}."
            )

            continue

        # Vérification après SET : l'annonce correspond
        # à l'état réellement retourné par le CVP.
        verified_state = verify_track_state(
            port,
            track,
            new_state
        )

        if verified_state is None:
            tracks[track] = None

            print(
                f"Piste {track:02d} modifiée, "
                "mais vérification impossible."
            )

            continue

        tracks[track] = verified_state

        print(
            f"Piste {track:02d} ->",
            "ON"
            if verified_state
            else "OFF"
        )

        announce_track(
            track,
            verified_state
        )


if __name__ == "__main__":
    main()
