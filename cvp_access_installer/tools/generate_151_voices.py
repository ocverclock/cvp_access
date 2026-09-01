#!/usr/bin/env python3
"""Génère les WAV supplémentaires de CVP Access 1.5.1."""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

# Runtime 1.5.1 copied beside this tool when installed.
runtime_dir = Path(
    os.environ.get(
        "CVP_RUNTIME_DIR",
        "/opt/cvp-access",
    )
)
if str(runtime_dir) not in sys.path:
    sys.path.insert(
        0,
        str(runtime_dir),
    )

import cvp_access  # noqa: E402  # registers 1.5.1 actions
from cvp_keyboard import (  # noqa: E402
    describe_invocation,
    parse_action,
)
from cvp_speech_151 import (  # noqa: E402
    canonical_help,
    help_filename,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--force",
        action="store_true",
    )
    args = parser.parse_args()

    with args.config.open("rb") as handle:
        config = tomllib.load(handle)

    speech = config.get(
        "speech",
        {},
    )
    keys = config.get(
        "keys",
        {},
    )

    voice_name = speech.get(
        "voice",
        "fr_FR-siwis-medium",
    )
    length_scale = float(
        speech.get(
            "length_scale",
            0.85,
        )
    )

    home = Path.home()
    base = Path(
        os.environ.get(
            "CVP_VOICE_DIR",
            home / "cvp_voice",
        )
    )
    model = Path(
        os.environ.get(
            "CVP_PIPER_MODEL",
            home
            / "piper-voices"
            / f"{voice_name}.onnx",
        )
    )

    prompts = {}

    def add(path, text):
        prompts[
            base / path
        ] = canonical_help(
            text
        )

    # CTRL + touche : toutes les actions configurées.
    for raw in keys.values():
        if not isinstance(
            raw,
            str,
        ):
            continue

        try:
            invocation = parse_action(
                raw
            )
        except Exception:
            continue

        text = describe_invocation(
            invocation
        )
        canonical = canonical_help(
            text
        )
        add(
            "help/"
            + help_filename(
                canonical
            ),
            canonical,
        )

        # Annonces d'exécution des Section Control / Registration.
        name = invocation.name
        parameter = invocation.parameter

        if name == "style_intro":
            add(
                "help/"
                + help_filename(
                    f"Intro {parameter}."
                ),
                f"Intro {parameter}.",
            )
        elif name == "style_main":
            letter = "ABCD"[
                parameter - 1
            ]
            add(
                "help/"
                + help_filename(
                    f"Main {letter}."
                ),
                f"Main {letter}.",
            )
        elif name == "style_fill":
            letter = "ABCD"[
                parameter - 1
            ]
            add(
                "help/"
                + help_filename(
                    f"Fill {letter}."
                ),
                f"Fill {letter}.",
            )
        elif name == "style_break":
            add(
                "help/"
                + help_filename(
                    "Break."
                ),
                "Break.",
            )
        elif name == "style_ending":
            add(
                "help/"
                + help_filename(
                    f"Ending {parameter}."
                ),
                f"Ending {parameter}.",
            )
        elif name == "registration_recall":
            add(
                "help/"
                + help_filename(
                    f"Registration {parameter}."
                ),
                f"Registration {parameter}.",
            )

    states = {
        "sync_start": "Sync Start",
        "guide": "Guide",
        "stream_lights": "Stream Lights",
        "metronome": "Métronome",
    }

    for stem, label in states.items():
        prompts[
            base
            / "state"
            / f"{stem}_on.wav"
        ] = f"{label} activé."
        prompts[
            base
            / "state"
            / f"{stem}_off.wav"
        ] = f"{label} désactivé."

    if not prompts:
        print(
            "Aucun WAV 1.5.1 requis."
        )
        return

    if (
        not model.is_file()
        or not Path(
            str(model) + ".json"
        ).is_file()
    ):
        raise SystemExit(
            f"Modèle Piper absent : {model}"
        )

    print(
        f"WAV supplémentaires requis : {len(prompts)}"
    )
    print(
        "Chargement Piper :",
        model,
    )

    voice = PiperVoice.load(
        str(model)
    )
    syn = SynthesisConfig(
        length_scale=length_scale
    )

    generated = 0
    existing = 0

    for output, text in sorted(
        prompts.items(),
        key=lambda item: str(
            item[0]
        ),
    ):
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            output.is_file()
            and not args.force
        ):
            existing += 1
            continue

        print(
            output.relative_to(
                base
            ),
            "<-",
            text,
        )

        with wave.open(
            str(output),
            "wb",
        ) as wav:
            voice.synthesize_wav(
                text,
                wav,
                syn_config=syn,
            )

        generated += 1

    print(
        f"Generated: {generated}; existing: {existing}"
    )


if __name__ == "__main__":
    main()
