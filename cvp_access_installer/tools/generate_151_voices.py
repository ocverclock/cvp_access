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

# Le générateur tourne dans le venv Piper.
# evdev est fourni par Debian au Python système.
SYSTEM_DIST_PACKAGES = Path("/usr/lib/python3/dist-packages")
if (
    SYSTEM_DIST_PACKAGES.is_dir()
    and str(SYSTEM_DIST_PACKAGES) not in sys.path
):
    sys.path.append(str(SYSTEM_DIST_PACKAGES))

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


MAX_PREGENERATED_NUMBER = 150

STYLE_MUTE_PROMPTS = {
    "rhythm_1": "Mute Rythme 1.",
    "rhythm_2": "Mute Rythme 2.",
    "bass": "Mute Basse.",
    "chord_1": "Mute Accord 1.",
    "chord_2": "Mute Accord 2.",
    "pad": "Mute Pad.",
    "phrase_1": "Mute Phrase 1.",
    "phrase_2": "Mute Phrase 2.",
}


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

    def add_raw(path, text):
        # Fragments destinés à être concaténés : ne pas ajouter de point,
        # sinon Piper insère une pause audible au milieu de la phrase.
        prompts[
            base / path
        ] = str(text).strip()

    # Toujours disponible : l'annonce n'est jouée qu'une fois le MIDI,
    # le clavier et le moteur vocal initialisés.
    add(
        "system/startup_ready.wav",
        "Dispositif Melody Music CVP Access opérationnel.",
    )
    add(
        "system/restart_device.wav",
        "Relance du dispositif CVP Access.",
    )

    # Recorder 1.6 — feedback must remain immediate for a blind user.
    for path, text in {
        "recorder/ready.wav": "Enregistrement prêt.",
        "recorder/cancelled.wav": "Enregistrement annulé.",
        "recorder/no_recording.wav": "Aucun enregistrement disponible.",
        "recorder/play.wav": "Lecture.",
        "recorder/play_stopped.wav": "Lecture arrêtée.",
        "recorder/play_finished.wav": "Lecture terminée.",
        "recorder/output_missing.wav": "Sortie MIDI de lecture introuvable.",
        "recorder/save_error.wav": "Erreur pendant la sauvegarde.",
        "recorder/stop.wav": "Stop.",
        "recorder/enregistrement_du.wav": "Enregistrement du",
        "recorder/sauvegarde.wav": "sauvegardé",
    }.items():
        add(path, text)

    song_numeric_actions = {
        "song_position",
        "song_measure_previous",
        "song_measure_next",
        "song_measure_previous_5",
        "song_measure_next_5",
        "song_goto_measure",
        "song_loop_point_a",
        "song_loop_point_b",
        "song_loop_toggle",
        "announce_song_length",
    }
    needs_song_numbers = False

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

        # Annonces d'exécution des Section Control / Registration / Solo.
        name = invocation.name
        parameter = invocation.parameter

        if name in song_numeric_actions:
            needs_song_numbers = True

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
        elif (
            name == "song_track_solo"
            and parameter is not None
            and 1 <= parameter <= 16
        ):
            add(
                f"song_solo/solo_{parameter:02d}.wav",
                f"Solo piste {parameter}.",
            )

    states = {
        "sync_start": "Syncro Start",
        "guide": "Guide",
        "stream_lights": "Stream Lights",
        "metronome": "Métronome",
        "voice_guide": "Guide vocal",
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

    # Les parties Style ont un vocabulaire distinct des pistes Song.
    # Exemple : "Mute Rythme 1" et non "Piste 1".
    for stem, text in STYLE_MUTE_PROMPTS.items():
        add(
            f"style_part/{stem}_mute.wav",
            text,
        )

    # Les nombres 0..150 sont aussi nécessaires au Recorder pour annoncer
    # instantanément le jour et le numéro quotidien sans repasser par Piper.
    for number in range(
        0,
        MAX_PREGENERATED_NUMBER + 1,
    ):
        add_raw(
            f"numbers/number_{number:03d}.wav",
            str(number),
        )

    recorder_fragments = {
        "recorder/numero.wav": "numéro",
        "recorder/month_01.wav": "janvier",
        "recorder/month_02.wav": "février",
        "recorder/month_03.wav": "mars",
        "recorder/month_04.wav": "avril",
        "recorder/month_05.wav": "mai",
        "recorder/month_06.wav": "juin",
        "recorder/month_07.wav": "juillet",
        "recorder/month_08.wav": "août",
        "recorder/month_09.wav": "septembre",
        "recorder/month_10.wav": "octobre",
        "recorder/month_11.wav": "novembre",
        "recorder/month_12.wav": "décembre",
    }
    for path, text in recorder_fragments.items():
        add_raw(path, text)

    # Les annonces Song prévisibles utilisent les mêmes nombres, complétés
    # par leur vocabulaire spécifique.
    if needs_song_numbers:
        fragments = {
            "words/mesure.wav": "mesure",
            "words/temps.wav": "temps",
            "words/point_a_mesure.wav": "Point A mesure",
            "words/point_b_mesure.wav": "Point B mesure",
            "words/boucle_de_mesure.wav": "Boucle activée de la mesure",
            "words/a_mesure.wav": "à la mesure",
            "words/longueur_song.wav": "Longueur du Song",
            "words/mesures.wav": "mesures",
        }

        for path, text in fragments.items():
            add_raw(
                path,
                text,
            )

        add(
            "song/loop_off.wav",
            "Boucle désactivée.",
        )

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
