#!/usr/bin/env python3

import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig


MODEL = "/home/pi/piper-voices/fr_FR-siwis-medium.onnx"
VOICE_DIR = Path("/home/pi/cvp_voice")

# Vitesse de la voix
# 1.0 = normale
# 0.85 = légèrement plus rapide
SPEED = 0.85


VOICE_DIR.mkdir(parents=True, exist_ok=True)


print()
print("Génération des voix CVP-909")
print("===========================")
print()
print("Chargement du modèle Piper...")

# Le modèle n'est chargé QU'UNE SEULE FOIS
voice = PiperVoice.load(MODEL)

config = SynthesisConfig(
    length_scale=SPEED
)

print("Modèle chargé.")
print()


def generate(text, filename):

    output = VOICE_DIR / filename

    print(f"{filename:25s} -> {text}")

    with wave.open(str(output), "wb") as wav_file:
        voice.synthesize_wav(
            text,
            wav_file,
            syn_config=config
        )


for piste in range(1, 17):

    generate(
        f"Piste {piste} coupée.",
        f"piste_{piste:02d}_off.wav"
    )

    generate(
        f"Piste {piste} activée.",
        f"piste_{piste:02d}_on.wav"
    )


print()
print("================================")
print("Génération terminée.")
print()
print(f"Dossier : {VOICE_DIR}")
print("32 fichiers WAV générés.")
