#!/usr/bin/env python3
"""Generate only the CVP Access WAV prompts required by keyboard.toml."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

STYLE_PARTS = [
    ("rhythm_1", "Rythme 1"),
    ("rhythm_2", "Rythme 2"),
    ("bass", "Basse"),
    ("chord_1", "Accord 1"),
    ("chord_2", "Accord 2"),
    ("pad", "Pad"),
    ("phrase_1", "Phrase 1"),
    ("phrase_2", "Phrase 2"),
]


def parse_action(value: str):
    if not isinstance(value, str):
        return None, None
    if ":" in value:
        name, raw = value.split(":", 1)
        try:
            return name.strip().lower(), int(raw.strip())
        except ValueError:
            return name.strip().lower(), None
    return value.strip().lower(), None


def main():
    parser = argparse.ArgumentParser(
        description="Generate CVP Access prompts required by keyboard.toml"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    with args.config.open("rb") as handle:
        data = tomllib.load(handle)

    speech = data.get("speech", {})
    keys = data.get("keys", {})

    mode = speech.get("mode", "hybrid")
    generation = speech.get("generation", "configured")
    voice_name = speech.get("voice", "fr_FR-siwis-medium")
    length_scale = float(speech.get("length_scale", 0.85))

    home = Path.home()
    model = Path(
        os.environ.get(
            "CVP_PIPER_MODEL",
            home / "piper-voices" / f"{voice_name}.onnx",
        )
    )
    base = Path(os.environ.get("CVP_VOICE_DIR", home / "cvp_voice"))
    base.mkdir(parents=True, exist_ok=True)

    if mode == "runtime":
        print("Speech mode runtime: no pre-generated action WAV required.")
        return

    if not model.exists() or not Path(str(model) + ".json").exists():
        print(f"Piper model missing: {voice_name}; downloading...")
        model.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                sys.executable, "-m", "piper.download_voices",
                voice_name, "--data-dir", str(model.parent),
            ]
        )
        if result.returncode != 0 or not model.exists():
            raise SystemExit(f"Unable to download Piper model: {voice_name}")

    metadata_path = base / ".cvp_voice_generation.json"
    previous_profile = {}
    if metadata_path.is_file():
        try:
            previous_profile = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            previous_profile = {}

    current_profile = {
        "voice": voice_name,
        "length_scale": length_scale,
    }
    profile_changed = any(
        previous_profile.get(key) != value
        for key, value in current_profile.items()
    )
    if profile_changed and previous_profile:
        print("Piper voice profile changed: required WAV files will be regenerated.")

    actions = set()
    if generation == "configured":
        for value in keys.values():
            name, parameter = parse_action(value)
            if name:
                actions.add((name, parameter))
    else:
        # core/all = complete currently stable action catalogue.
        actions.update(("song_track_toggle", n) for n in range(1, 17))
        actions.update(("style_part_toggle", n) for n in range(1, 9))
        actions.update({
            ("layer_toggle", None),
            ("left_toggle", None),
            ("announce_tempo", None),
            ("announce_transpose", None),
            ("song_play_pause", None),
            ("song_stop", None),
            ("song_position", None),
            ("song_measure_previous", None),
            ("song_measure_next", None),
            ("song_measure_previous_5", None),
            ("song_measure_next_5", None),
            ("song_goto_measure", None),
            ("song_loop_point_a", None),
            ("song_loop_point_b", None),
            ("song_loop_toggle", None),
            ("style_start_stop", None),
            ("song_volume_change", 1),
            ("main_volume_change", 1),
            ("voice_volume_up", None),
            ("voice_volume_down", None),
            ("style_volume_up", None),
            ("style_volume_down", None),
        })

    prompts: dict[Path, str] = {}

    def add(relative: str, text: str):
        prompts[base / relative] = text

    for name, parameter in actions:
        if name == "song_track_toggle" and parameter and 1 <= parameter <= 16:
            add(f"piste_{parameter:02d}_off.wav", f"Piste {parameter} coupée.")
            add(f"piste_{parameter:02d}_on.wav", f"Piste {parameter} activée.")

        elif name == "style_part_toggle" and parameter and 1 <= parameter <= 8:
            stem, label = STYLE_PARTS[parameter - 1]
            add(f"style_part/{stem}_on.wav", f"{label} activé.")
            add(f"style_part/{stem}_off.wav", f"{label} désactivé.")

        elif name == "layer_toggle":
            add("voice_part/layer_on.wav", "Dual activé.")
            add("voice_part/layer_off.wav", "Dual désactivé.")

        elif name == "left_toggle":
            add("voice_part/left_on.wav", "Left activé.")
            add("voice_part/left_off.wav", "Left désactivé.")

        elif name == "announce_tempo":
            for tempo in range(5, 281):
                add(f"tempo/tempo_{tempo:03d}.wav", f"Tempo {tempo}.")

        elif name == "announce_transpose":
            for value in range(-12, 13):
                if value < 0:
                    add(
                        f"transpose/transpose_m{abs(value):02d}.wav",
                        f"Transpose moins {abs(value)}.",
                    )
                elif value > 0:
                    add(
                        f"transpose/transpose_p{value:02d}.wav",
                        f"Transpose plus {value}.",
                    )
                else:
                    add("transpose/transpose_000.wav", "Transpose zéro.")

        elif name in {"voice_volume_up", "voice_volume_down"}:
            for volume in range(10, 101, 10):
                add(
                    f"volume/volume_{volume:03d}.wav",
                    f"Volume guide vocal {volume} pour cent.",
                )

        elif name in {"style_volume_up", "style_volume_down"}:
            for volume in range(0, 128):
                add(
                    f"style_volume/style_volume_{volume:03d}.wav",
                    f"Accompagnement {volume}.",
                )

        elif name == "song_volume_change":
            for volume in range(0, 128):
                add(
                    f"song_volume/song_volume_{volume:03d}.wav",
                    f"Volume Song {volume}.",
                )

        elif name == "main_volume_change":
            for volume in range(0, 128):
                add(
                    f"main_volume/main_volume_{volume:03d}.wav",
                    f"Volume Main {volume}.",
                )

        elif name == "style_start_stop":
            add("style_transport/start.wav", "Style démarré.")
            add("style_transport/stop.wav", "Style arrêté.")

        elif name == "song_goto_measure":
            add("song/no_song.wav", "Pas de Song chargé.")
            add("song/detection_error.wav", "Impossible de vérifier le Song.")
            add("song/goto_prompt.wav", "Saisir le numéro de mesure puis Entrée.")
            add("song/goto_cancelled.wav", "Saisie mesure annulée.")
            add("song/invalid_measure.wav", "Mesure invalide.")

        elif name in {"song_loop_point_a", "song_loop_point_b", "song_loop_toggle"}:
            add("song/loop_a_missing.wav", "Point A non défini.")
            add("song/loop_b_invalid.wav", "Point B invalide.")
            add("song/loop_points_missing.wav", "Points A et B non définis.")

        elif name == "song_play_pause":
            add("transport/lecture.wav", "Lecture")
            add("transport/pause.wav", "Pause")

        elif name == "song_stop":
            add("transport/stop.wav", "Arrêt")

        elif name == "song_position":
            add("words/mesure.wav", "mesure")
            add("words/temps.wav", "temps")
            for number in range(0, 101):
                add(f"numbers/number_{number:03d}.wav", str(number))

    print(f"Configuration: {args.config}")
    print(f"Speech mode: {mode}")
    print(f"Generation: {generation}")
    print(f"Unique actions: {len(actions)}")
    print(f"Required WAV files: {len(prompts)}")

    if not prompts:
        print("No WAV prompt required by this configuration.")
        return

    print(f"Piper model: {model}")
    print("Loading Piper model once...")
    voice = PiperVoice.load(str(model))
    syn_config = SynthesisConfig(length_scale=length_scale)

    generated = 0
    existing = 0
    for output, text in sorted(prompts.items(), key=lambda item: str(item[0])):
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not args.force and not profile_changed:
            existing += 1
            continue
        print(f"{output.relative_to(base)} <- {text}")
        with wave.open(str(output), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)
        generated += 1

    metadata_path.write_text(
        json.dumps(
            {
                **current_profile,
                "mode": mode,
                "generation": generation,
                "required_wav": len(prompts),
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"Generated: {generated}; already present: {existing}")


if __name__ == "__main__":
    main()
