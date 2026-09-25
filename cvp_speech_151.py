#!/usr/bin/env python3
"""CVP Access 1.5.1 - compléments vocaux.

Réutilise le gestionnaire hybride existant et ajoute :
- aide CTRL pré-générable par hash ;
- annonces booléennes communes ;
- annonces de valeurs/noms dynamiques ;
- annonces Song prévisibles composées depuis des WAV pré-générés ;
- annonces Solo Song pré-générées ;
- lecture audio sérialisée pour éviter les coupures/craquements entre annonces ;
- mute logiciel du guide vocal, indépendant de son volume ;
- annonces explicites des mutes de parties Style ;
- annonce vocale de disponibilité au démarrage.
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
        core._cvp_original_start_audio = original_start_audio
        core._cvp_audio_serialized = True

    # Mute logiciel : le niveau voice_volume reste inchangé. Les annonces sont
    # simplement bloquées pendant le mute, puis reprennent au même volume.
    manager._cvp_voice_guide_muted = False
    original_speak = manager.speak
    original_speak_sequence = manager.speak_sequence
    original_speak_now = manager._speak_now
    original_speak_sequence_now = manager._speak_sequence_now

    def is_voice_guide_muted():
        return bool(manager._cvp_voice_guide_muted)

    def set_voice_guide_muted(muted):
        muted = bool(muted)
        manager._cvp_voice_guide_muted = muted

        if muted:
            current = getattr(core, "audio_process", None)
            if current is not None and current.poll() is None:
                try:
                    current.terminate()
                except Exception:
                    pass

        return muted

    def speak_guarded(
        text,
        wav_path=None,
        replace_key=None,
    ):
        if manager._cvp_voice_guide_muted:
            return False
        return original_speak(
            text,
            wav_path,
            replace_key,
        )

    def speak_sequence_guarded(
        text,
        files,
        replace_key=None,
    ):
        if manager._cvp_voice_guide_muted:
            return False
        return original_speak_sequence(
            text,
            files,
            replace_key,
        )

    def speak_now_guarded(text, wav_path=None):
        if manager._cvp_voice_guide_muted:
            return False
        return original_speak_now(
            text,
            wav_path,
        )

    def speak_sequence_now_guarded(text, files):
        if manager._cvp_voice_guide_muted:
            return False
        return original_speak_sequence_now(
            text,
            files,
        )

    manager.speak = speak_guarded
    manager.speak_sequence = speak_sequence_guarded
    manager._speak_now = speak_now_guarded
    manager._speak_sequence_now = speak_sequence_now_guarded
    core.is_voice_guide_muted = is_voice_guide_muted
    core.set_voice_guide_muted = set_voice_guide_muted

    def announce_startup_ready():
        return manager.speak(
            "Dispositif Melody Music CVP Access opérationnel.",
            voice_dir / "system" / "startup_ready.wav",
            replace_key="system_status",
        )

    def announce_recorder_ready():
        return manager.speak(
            "Enregistrement prêt.",
            voice_dir / "recorder" / "ready.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_cancelled():
        return manager.speak(
            "Enregistrement annulé.",
            voice_dir / "recorder" / "cancelled.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_no_recording():
        return manager.speak(
            "Aucun enregistrement disponible.",
            voice_dir / "recorder" / "no_recording.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_play():
        return manager.speak(
            "Lecture.",
            voice_dir / "recorder" / "play.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_play_stopped():
        return manager.speak(
            "Lecture arrêtée.",
            voice_dir / "recorder" / "play_stopped.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_play_finished():
        return manager.speak(
            "Lecture terminée.",
            voice_dir / "recorder" / "play_finished.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_output_missing():
        return manager.speak(
            "Sortie MIDI de lecture introuvable.",
            voice_dir / "recorder" / "output_missing.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_save_error():
        return manager.speak(
            "Erreur pendant la sauvegarde.",
            voice_dir / "recorder" / "save_error.wav",
            replace_key="recorder_status",
        )

    def announce_recorder_stop_now():
        if manager._cvp_voice_guide_muted:
            return False

        # Feedback critique : lecture directe, hors file d'attente, pour que
        # l'utilisateur sache immédiatement que l'enregistrement est arrêté.
        return original_speak_now(
            "Stop.",
            voice_dir / "recorder" / "stop.wav",
        )

    def play_recorder_navigation_cue(direction):
        if manager._cvp_voice_guide_muted:
            return False

        filename = {
            "previous": "previous.wav",
            "next": "next.wav",
        }.get(str(direction))

        if filename is None:
            return False

        path = voice_dir / "recorder" / filename
        if not path.is_file():
            return False

        # Les repères de navigation doivent être plus rapides que la parole.
        # On coupe l'éventuelle annonce précédente et on lance directement le
        # WAV via le start_audio historique, sans attendre la file vocale.
        current = getattr(core, "audio_process", None)
        if current is not None and current.poll() is None:
            try:
                current.terminate()
            except Exception:
                pass

        scaled = core.create_scaled_wav(
            path,
            core.voice_volume,
        )
        starter = getattr(
            core,
            "_cvp_original_start_audio",
            core.start_audio,
        )
        starter(scaled)
        return True

    def announce_recorder_selection_now(day, month, number):
        if manager._cvp_voice_guide_muted:
            return False

        day = int(day)
        month = int(month)
        number = int(number)

        day_file = number_file(day)
        number_path = number_file(number)
        month_file = voice_dir / "recorder" / f"month_{month:02d}.wav"
        numero_file = voice_dir / "recorder" / "numero.wav"

        month_names = (
            "", "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre",
        )
        if not 1 <= month < len(month_names):
            return manager.speak(
                f"Enregistrement numéro {number}.",
                replace_key="recorder_selection",
            )

        text = (
            f"{day} {month_names[month]}, "
            f"numéro {number}."
        )

        if (
            day_file is not None
            and number_path is not None
            and month_file.is_file()
            and numero_file.is_file()
        ):
            return original_speak_sequence_now(
                text,
                [
                    day_file,
                    month_file,
                    numero_file,
                    number_path,
                ],
            )

        # Cas rare : plus de 150 enregistrements le même jour. Piper reste
        # alors un filet de sécurité, pas le chemin normal de navigation.
        return manager.speak(
            text,
            replace_key="recorder_selection",
        )

    def announce_recorder_saved_now(day, month, number):
        if manager._cvp_voice_guide_muted:
            return False

        day = int(day)
        month = int(month)
        number = int(number)

        day_file = number_file(day)
        number_path = number_file(number)
        month_file = voice_dir / "recorder" / f"month_{month:02d}.wav"
        prefix_file = voice_dir / "recorder" / "enregistrement_du.wav"
        numero_file = voice_dir / "recorder" / "numero.wav"
        saved_file = voice_dir / "recorder" / "sauvegarde.wav"

        month_names = (
            "", "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre",
        )
        if not 1 <= month < len(month_names):
            return manager.speak(
                f"Enregistrement numéro {number}, sauvegardé.",
                replace_key="recorder_saved",
            )

        text = (
            f"Enregistrement du {day} {month_names[month]}, "
            f"numéro {number}, sauvegardé."
        )

        files = [
            prefix_file,
            day_file,
            month_file,
            numero_file,
            number_path,
            saved_file,
        ]
        if all(path is not None and Path(path).is_file() for path in files):
            return original_speak_sequence_now(
                text,
                [Path(path) for path in files],
            )

        return manager.speak(
            text,
            replace_key="recorder_saved",
        )

    def announce_device_restart():
        if manager._cvp_voice_guide_muted:
            return False

        # ESC redémarre le processus. L'annonce doit donc être synchrone :
        # attendre la fin de aplay avant SystemExit, sinon cleanup() la coupe.
        ok = original_speak_now(
            "Relance du dispositif CVP Access.",
            voice_dir / "system" / "restart_device.wav",
        )
        current = getattr(core, "audio_process", None)
        if ok and current is not None and current.poll() is None:
            try:
                current.wait(timeout=10)
            except Exception:
                pass
        return ok

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

    def announce_style_part(part, active):
        label = legacy_speech.STYLE_LABELS[part]
        stem = core.STYLE_PART_NAMES[part]

        if active:
            text = f"{label} activé."
            filename = f"{stem}_on.wav"
        else:
            text = f"Mute {label}."
            filename = f"{stem}_mute.wav"

        return manager.speak(
            text,
            voice_dir / "style_part" / filename,
            replace_key=f"style_part_{stem}",
        )

    def announce_song_solo(track):
        track = int(track)
        return manager.speak(
            f"Solo piste {track}.",
            voice_dir / "song_solo" / f"solo_{track:02d}.wav",
            replace_key="song_solo",
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

    core.announce_startup_ready = announce_startup_ready
    core.announce_recorder_ready = announce_recorder_ready
    core.announce_recorder_cancelled = announce_recorder_cancelled
    core.announce_recorder_no_recording = announce_recorder_no_recording
    core.announce_recorder_play = announce_recorder_play
    core.announce_recorder_play_stopped = announce_recorder_play_stopped
    core.announce_recorder_play_finished = announce_recorder_play_finished
    core.announce_recorder_output_missing = announce_recorder_output_missing
    core.announce_recorder_save_error = announce_recorder_save_error
    core.announce_recorder_stop_now = announce_recorder_stop_now
    core.play_recorder_navigation_cue = play_recorder_navigation_cue
    core.announce_recorder_selection_now = announce_recorder_selection_now
    core.announce_recorder_saved_now = announce_recorder_saved_now
    core.announce_device_restart = announce_device_restart
    core.announce_action_help = announce_action_help
    core.announce_boolean_state = announce_boolean_state
    core.announce_style_part = announce_style_part
    core.announce_song_solo = announce_song_solo
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
