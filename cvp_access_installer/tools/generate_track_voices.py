#!/usr/bin/env python3
import argparse
import os
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig


def main():
    parser = argparse.ArgumentParser(description="Generate CVP Access track voice prompts")
    parser.add_argument("--force", action="store_true", help="overwrite existing WAV files")
    args = parser.parse_args()

    home = Path.home()
    model = Path(os.environ.get("CVP_PIPER_MODEL", home / "piper-voices" / "fr_FR-siwis-medium.onnx"))
    voice_dir = Path(os.environ.get("CVP_VOICE_DIR", home / "cvp_voice"))
    voice_dir.mkdir(parents=True, exist_ok=True)

    if not model.exists():
        raise SystemExit(f"Piper model not found: {model}")

    print(f"Piper model: {model}")
    print(f"Voice directory: {voice_dir}")
    print("Loading Piper model once...")
    voice = PiperVoice.load(str(model))
    config = SynthesisConfig(length_scale=0.85)

    def generate(text: str, filename: str):
        output = voice_dir / filename
        if output.exists() and not args.force:
            print(f"Exists: {output.name}")
            return
        print(f"{output.name:24s} <- {text}")
        with wave.open(str(output), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=config)

    for track in range(1, 17):
        generate(f"Piste {track} coupée.", f"piste_{track:02d}_off.wav")
        generate(f"Piste {track} activée.", f"piste_{track:02d}_on.wav")

    print("Track voice generation complete.")


if __name__ == "__main__":
    main()
