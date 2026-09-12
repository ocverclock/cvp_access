#!/usr/bin/env python3
"""CVP Access 1.5.1 - compléments vocaux.

Réutilise le gestionnaire hybride existant et ajoute :
- aide CTRL pré-générable par hash ;
- annonces booléennes communes ;
- annonces de valeurs/noms dynamiques ;
- annonces Song prévisibles composées depuis des WAV pré-générés ;
- lecture audio sérialisée pour éviter les coupures/craquements entre annonces.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import cvp_speech as legacy_speech


MAX_PREGENERATED_NUMBER = 150


def canonical_help(text: str) -> str:
    text = " ".join(str(text).strip().split())
    if text and text[-1] not in ".!?":
        text += "."
    return text


def help_filename(text: str) -> str:
    canonical = canonical_help(text)
    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:20]
    return f"help_{digest}.wav"


def install_speech_hooks(core, speech_config):
    manager = legacy_speech.install_speech_hooks(
        core,
        speech_config,
    )

    voice_dir = core.VOICE_DIR

    # Le moteur historique interrompait brutalement aplay lorsqu'une nouvelle
    # annonce arrivait. Cela pouvait produire une voix coupée ou un craquement.
    # Le thread vocal est déjà séquentiel : on laisse donc l'annonce en cours
    # se terminer. Les replace_key continuent de supprimer les annonces
    # obsolètes de la file avant leur lecture.
    if not getattr(core, "_cvp_audio_serialized", False):
        original_start_audio = core.start_audio

        def start_audio_serialized(filename):
            current = getattr(core, "audio_process", None)
            if current is not None and current.poll() is None:
                try:
                    current.wait()
                except Exception:
                    pass
            return original_start_audio(filename)

        core.start_audio = start_audio_serialized
        core._cvp_audio_serialized = True

    def number_file(value):
        value = int(value)
        if 0 <= value <= MAX_PREGENERATED_NUMBER:
            return (
                voice_dir
                / "numbers"
                / f"number_{value:03d}.wav"
            )
        return None

    def speak_number_sequence(text, files, *, replace_key):
        if all(path is not None for path in files):
            return manager.speak_sequence(
                text,
                [Path(path) for path in files],
                replace_key=replace_key,
            )
        return manager.speak(
            text,
            replace_key=replace_key,
        )

    def announce_action_help(text):
        canonical = canonical_help(text)
        return manager.speak(
            canonical,
            voice_dir / "help" / help_filename(canonical),
            replace_key="action_help",
        )

    def announce_boolean_state(label, enabled, stem):
        state = "on" if enabled else "off"
        text = (
            f"{label} activé."
            if enabled
            else f"{label} désactivé."
        )
        return manager.speak(
            text,
            voice_dir / "state" / f"{stem}_{state}.wav",
            replace_key=f"state_{stem}",
        )

    def announce_named_value(label, value):
        # Les noms de Song/Style/Voice sont dynamiques : Piper reste nécessaire
        # la première fois, puis le cache TTS est réutilisé.
        return manager.speak(
            f"{label} {value}.",
            replace_key=f"named_{label}",
        )

    def announce_value(value, *, key="value"):
        return manager.speak(
            f"{value}.",
            replace_key=f"value_{key}",
        )

    def announce_song_state(state):
        mapping = {
            core.SONG_STOP: ("Arrêt", "stop.wav"),
            core.SONG_PLAY: ("Lecture", "lecture.wav"),
            core.SONG_PAUSE: ("Pause", "pause.wav"),
        }
        item = mapping.get(state)
        if item is None:
            return False
        text, filename = item
        return manager.speak(
            text,
            voice_dir / "transport" / filename,
            replace_key="song_state",
        )

    def announce_measure(measure):
        return speak_number_sequence(
            f"Mesure {measure}.",
            [
                voice_dir / "words" / "mesure.wav",
                number_file(measure),
            ],
            replace_key="song_measure",
        )

    def announce_song_position(measure, beat):
        return speak_number_sequence(
            f"Mesure {measure}, temps {beat}.",
            [
                voice_dir / "words" / "mesure.wav",
                number_file(measure),
                voice_dir / "words" / "temps.wav",
                number_file(beat),
            ],
            replace_key="song_position",
        )

    def announce_loop_point_a(measure):
        return speak_number_sequence(
            f"Point A mesure {measure}.",
            [
                voice_dir / "words" / "point_a_mesure.wav",
                number_file(measure),
            ],
            replace_key="loop_point_a",
        )

    def announce_loop_point_b(measure):
        return speak_number_sequence(
            f"Point B mesure {measure}.",
            [
                voice_dir / "words" / "point_b_mesure.wav",
                number_file(measure),
            ],
            replace_key="loop_point_b",
        )

    def announce_loop_state(active, point_a, point_b):
        if not active:
            return manager.speak(
                "Boucle désactivée.",
                voice_dir / "song" / "loop_off.wav",
                replace_key="loop_state",
            )

        return speak_number_sequence(
            (
                f"Boucle activée de la mesure {point_a} "
                f"à la mesure {point_b}."
            ),
            [
                voice_dir / "words" / "boucle_de_mesure.wav",
                number_file(point_a),
                voice_dir / "words" / "a_mesure.wav",
                number_file(point_b),
            ],
            replace_key="loop_state",
        )

    def announce_song_length(measures):
        return speak_number_sequence(
            f"Longueur du Song, {measures} mesures.",
            [
                voice_dir / "words" / "longueur_song.wav",
                number_file(measures),
                voice_dir / "words" / "mesures.wav",
            ],
            replace_key="song_length",
        )

    core.announce_action_help = announce_action_help
    core.announce_boolean_state = announce_boolean_state
    core.announce_named_value = announce_named_value
    core.announce_value = announce_value
    core.announce_song_state = announce_song_state
    core.announce_measure = announce_measure
    core.announce_song_position = announce_song_position
    core.announce_loop_point_a = announce_loop_point_a
    core.announce_loop_point_b = announce_loop_point_b
    core.announce_loop_state = announce_loop_state
    core.announce_song_length = announce_song_length

    return manager
