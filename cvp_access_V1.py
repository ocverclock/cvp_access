#!/usr/bin/env python3

import array
import glob
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


# ============================================================
# CLAVIER AZERTY
#
# A Z E R T Y U I = 1 à 8
# Q S D F G H J K = 9 à 16
# ============================================================

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
midi_queue = queue.Queue()


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

    process = subprocess.Popen(
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

    message = []
    hex_byte = ""

    while True:

        char = process.stdout.read(1)

        if char == "":
            print("Récepteur MIDI arrêté.")

            err = process.stderr.read().strip()
            if err:
                print("Erreur réception MIDI :", err)

            return

        # amidi écrit les octets sous forme :
        # F0 43 73 ... F7
        #
        # On lit directement les caractères au lieu
        # d'attendre un retour à la ligne.

        if char in "0123456789abcdefABCDEF":

            hex_byte += char

            if len(hex_byte) == 2:

                value = int(hex_byte, 16)
                hex_byte = ""

                # Début SysEx
                if value == 0xF0:
                    message = [0xF0]
                    continue

                if not message:
                    continue

                message.append(value)

                # Fin SysEx
                if value == 0xF7:

                    midi_queue.put(message.copy())
                    message = []

        else:
            hex_byte = ""

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
            (response[16] << 8)
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
        (data[0] << 8)
        | data[1]
    )


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
# AUDIO : volume logiciel
# ============================================================

def create_scaled_wav(source, volume):

    cache_dir = Path("/tmp/cvp_voice_cache")
    cache_dir.mkdir(exist_ok=True)

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
            str(scaled)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


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

    print()
    print("CVP-909 ACCESS V3")
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

    print(
        "Tempo :",
        tempo
    )

    print(
        "Transpose :",
        transpose
    )

    keyboard = find_keyboard()

    print()
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
        "↑  = volume voix +"
    )

    print(
        "↓  = volume voix -"
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

        # Pistes
        track = KEY_TO_TRACK.get(
            event.code
        )

        if track is None:
            continue

        current = tracks[track]

        # Si état inconnu :
        # nouvelle interrogation
        if current is None:

            current = get_track_state(
                port,
                track
            )

            if current is None:

                print(
                    f"Etat piste {track} inconnu."
                )

                continue

        new_state = not current

        if set_track_state(
            port,
            track,
            new_state
        ):

            tracks[track] = new_state

            print(
                f"Piste {track:02d} ->",
                "ON"
                if new_state
                else "OFF"
            )

            announce_track(
                track,
                new_state
            )


if __name__ == "__main__":
    main()
