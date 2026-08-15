#!/usr/bin/env python3
import argparse
import os
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig


def main():
    parser = argparse.ArgumentParser(description="Generate CVP Access value/status voice prompts")
    parser.add_argument("--force", action="store_true", help="overwrite existing WAV files")
    args = parser.parse_args()

    home = Path.home()
    model = Path(os.environ.get("CVP_PIPER_MODEL", home / "piper-voices" / "fr_FR-siwis-medium.onnx"))
    base = Path(os.environ.get("CVP_VOICE_DIR", home / "cvp_voice"))

    dirs = {
        "tempo": base / "tempo",
        "transpose": base / "transpose",
        "volume": base / "volume",
        "style_volume": base / "style_volume",
        "style_part": base / "style_part",
        "voice_part": base / "voice_part",
        "numbers": base / "numbers",
        "words": base / "words",
        "transport": base / "transport",
        "status": base / "status",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    if not model.exists():
        raise SystemExit(f"Piper model not found: {model}")

    print(f"Piper model: {model}")
    print("Loading Piper model once...")
    voice = PiperVoice.load(str(model))
    config = SynthesisConfig(length_scale=0.85)

    def generate(text: str, output: Path):
        if output.exists() and not args.force:
            print(f"Exists: {output.relative_to(base)}")
            return
        print(f"{output.relative_to(base)} <- {text}")
        with wave.open(str(output), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=config)

    for tempo in range(5, 281):
        generate(f"Tempo {tempo}.", dirs["tempo"] / f"tempo_{tempo:03d}.wav")

    for value in range(-12, 13):
        if value < 0:
            phrase = f"Transpose moins {abs(value)}."
            name = f"transpose_m{abs(value):02d}.wav"
        elif value > 0:
            phrase = f"Transpose plus {value}."
            name = f"transpose_p{value:02d}.wav"
        else:
            phrase = "Transpose zéro."
            name = "transpose_000.wav"
        generate(phrase, dirs["transpose"] / name)

    for volume in range(10, 101, 10):
        generate(f"Volume de la voix {volume} pour cent.", dirs["volume"] / f"volume_{volume:03d}.wav")

    for volume in range(0, 128):
        generate(f"Accompagnement {volume}.", dirs["style_volume"] / f"style_volume_{volume:03d}.wav")

    style_parts = [
        ("rhythm_1", "Rythme 1"), ("rhythm_2", "Rythme 2"),
        ("bass", "Basse"), ("chord_1", "Accord 1"),
        ("chord_2", "Accord 2"), ("pad", "Pad"),
        ("phrase_1", "Phrase 1"), ("phrase_2", "Phrase 2"),
    ]
    for stem, label in style_parts:
        generate(f"{label} activé.", dirs["style_part"] / f"{stem}_on.wav")
        generate(f"{label} désactivé.", dirs["style_part"] / f"{stem}_off.wav")

    for stem, label in [("layer", "Dual"), ("left", "Left")]:
        generate(f"{label} activé.", dirs["voice_part"] / f"{stem}_on.wav")
        generate(f"{label} désactivé.", dirs["voice_part"] / f"{stem}_off.wav")

    for number in range(0, 101):
        generate(str(number), dirs["numbers"] / f"number_{number:03d}.wav")

    generate("mesure", dirs["words"] / "mesure.wav")
    generate("temps", dirs["words"] / "temps.wav")
    generate("Lecture", dirs["transport"] / "lecture.wav")
    generate("Pause", dirs["transport"] / "pause.wav")
    generate("Arrêt", dirs["transport"] / "stop.wav")
    generate("Interface prête.", dirs["status"] / "interface_prete.wav")
    generate("Interface MIDI introuvable.", dirs["status"] / "midi_introuvable.wav")

    print("Value/status voice generation complete.")


if __name__ == "__main__":
    main()
