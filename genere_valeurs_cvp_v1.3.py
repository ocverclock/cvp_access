#!/usr/bin/env python3

import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

MODEL = "/home/pi/piper-voices/fr_FR-siwis-medium.onnx"
BASE = Path("/home/pi/cvp_voice")

TEMPO_DIR = BASE / "tempo"
TRANSPOSE_DIR = BASE / "transpose"
VOLUME_DIR = BASE / "volume"
STYLE_VOLUME_DIR = BASE / "style_volume"
STYLE_PART_DIR = BASE / "style_part"
VOICE_PART_DIR = BASE / "voice_part"

TEMPO_DIR.mkdir(parents=True, exist_ok=True)
TRANSPOSE_DIR.mkdir(parents=True, exist_ok=True)
VOLUME_DIR.mkdir(parents=True, exist_ok=True)
STYLE_VOLUME_DIR.mkdir(parents=True, exist_ok=True)
STYLE_PART_DIR.mkdir(parents=True, exist_ok=True)
VOICE_PART_DIR.mkdir(parents=True, exist_ok=True)

print("Chargement de Piper...")
voice = PiperVoice.load(MODEL)

config = SynthesisConfig(
    length_scale=0.85
)


def generate(text, filename):

    if filename.exists():
        print("Existe :", filename.name)
        return

    print(text)

    with wave.open(str(filename), "wb") as wav:
        voice.synthesize_wav(
            text,
            wav,
            syn_config=config
        )


# Tempo : 5 à 280
for tempo in range(5, 281):

    generate(
        f"Tempo {tempo}.",
        TEMPO_DIR / f"tempo_{tempo:03d}.wav"
    )


# Transpose : -12 à +12
for value in range(-12, 13):

    if value < 0:
        phrase = f"Transpose moins {abs(value)}."
        filename = f"transpose_m{abs(value):02d}.wav"

    elif value > 0:
        phrase = f"Transpose plus {value}."
        filename = f"transpose_p{value:02d}.wav"

    else:
        phrase = "Transpose zéro."
        filename = "transpose_000.wav"

    generate(
        phrase,
        TRANSPOSE_DIR / filename
    )


# Volume voix : 10 à 100 %
for volume in range(10, 101, 10):

    generate(
        f"Volume de la voix {volume} pour cent.",
        VOLUME_DIR / f"volume_{volume:03d}.wav"
    )


# Volume accompagnement Style : 0 à 127
for volume in range(0, 128):

    generate(
        f"Accompagnement {volume}.",
        STYLE_VOLUME_DIR / f"style_volume_{volume:03d}.wav"
    )


# Parties Style : ON / OFF
STYLE_PART_VOICES = [
    ("rhythm_1", "Rythme 1"),
    ("rhythm_2", "Rythme 2"),
    ("bass", "Basse"),
    ("chord_1", "Accord 1"),
    ("chord_2", "Accord 2"),
    ("pad", "Pad"),
    ("phrase_1", "Phrase 1"),
    ("phrase_2", "Phrase 2"),
]

for filename_base, label in STYLE_PART_VOICES:

    generate(
        f"{label} activé.",
        STYLE_PART_DIR / f"{filename_base}_on.wav"
    )

    generate(
        f"{label} désactivé.",
        STYLE_PART_DIR / f"{filename_base}_off.wav"
    )


# Layer / Left : ON / OFF
VOICE_PART_VOICES = [
    ("layer", "Dual"),
    ("left", "Left"),
]

for filename_base, label in VOICE_PART_VOICES:

    generate(
        f"{label} activé.",
        VOICE_PART_DIR / f"{filename_base}_on.wav"
    )

    generate(
        f"{label} désactivé.",
        VOICE_PART_DIR / f"{filename_base}_off.wav"
    )


print()
print("Génération terminée.")
