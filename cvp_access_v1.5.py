#!/usr/bin/env python3
"""
CVP Access v1.5
Configurable keyboard frontend.

The Yamaha MIDI/SysEx engine remains the validated v1.4.1 implementation.
This version replaces only the hard-coded keyboard routing with a TOML-driven
action catalogue.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import threading
import time
from pathlib import Path

from cvp_keyboard import KeyRouter, load_keyboard_config
from cvp_speech import install_speech_hooks


VERSION = "1.5-RC2"
CORE_FILENAME = "cvp_access_v1.4.1.py"

CONFIG_FILE = Path(
    os.environ.get(
        "CVP_CONFIG_FILE",
        "/etc/cvp-access/keyboard.toml",
    )
)


def load_core():
    core_path = Path(__file__).resolve().with_name(CORE_FILENAME)

    if not core_path.is_file():
        raise SystemExit(
            "Moteur CVP Access absent : "
            f"{core_path}\n"
            "La v1.5 doit être installée avec cvp_access_v1.4.1.py "
            "dans le même dossier."
        )

    spec = importlib.util.spec_from_file_location(
        "cvp_access_core_v1_4_1",
        core_path,
    )
    if spec is None or spec.loader is None:
        raise SystemExit("Impossible de charger le moteur CVP Access v1.4.1.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # v1.4.1 contains the validated protocol engine but historically had a
    # /home/pi voice path.  v1.5 makes it user/configuration independent.
    module.VOICE_DIR = Path(
        os.environ.get(
            "CVP_VOICE_DIR",
            str(Path.home() / "cvp_voice"),
        )
    )

    return module


def default_config_path() -> Path:
    runtime_default = Path(__file__).resolve().with_name(
        "default-keyboard.toml"
    )
    if runtime_default.is_file():
        return runtime_default

    repository_default = (
        Path(__file__).resolve().parent
        / "config"
        / "default.toml"
    )
    return repository_default


class CVPActions:
    """Fixed, validated action catalogue.  TOML can only select these actions."""

    def __init__(self, core, port):
        self.core = core
        self.port = port

    def dispatch(self, invocation):
        name = invocation.name
        parameter = invocation.parameter

        handlers = {
            "song_track_toggle": self.song_track_toggle,
            "style_part_toggle": self.style_part_toggle,
            "layer_toggle": self.layer_toggle,
            "left_toggle": self.left_toggle,
            "announce_tempo": self.announce_tempo,
            "announce_transpose": self.announce_transpose,
            "song_play_pause": self.song_play_pause,
            "song_stop": self.song_stop,
            "song_position": self.song_position,
            "voice_volume_up": self.voice_volume_up,
            "voice_volume_down": self.voice_volume_down,
            "style_volume_up": self.style_volume_up,
            "style_volume_down": self.style_volume_down,
            "restart": self.restart,
        }

        handler = handlers.get(name)
        if handler is None:
            print("Action non implémentée :", name)
            return

        if parameter is None:
            handler()
        else:
            handler(parameter)

    # ------------------------------------------------------------------
    # System / accessibility
    # ------------------------------------------------------------------

    def restart(self):
        print("Redémarrage demandé...")
        raise SystemExit(0)

    def voice_volume_up(self):
        self.core.voice_volume = min(
            100,
            self.core.voice_volume + 10,
        )
        print("Volume voix :", self.core.voice_volume)
        self.core.announce_volume()

    def voice_volume_down(self):
        self.core.voice_volume = max(
            10,
            self.core.voice_volume - 10,
        )
        print("Volume voix :", self.core.voice_volume)
        self.core.announce_volume()

    # ------------------------------------------------------------------
    # Information
    # ------------------------------------------------------------------

    def announce_tempo(self):
        tempo = self.core.get_tempo(self.port)
        if tempo is None:
            print("Impossible de lire le tempo.")
            return

        print("Tempo :", tempo)
        self.core.announce_tempo(tempo)

    def announce_transpose(self):
        transpose = self.core.get_transpose(self.port)
        if transpose is None:
            print("Impossible de lire le transpose.")
            return

        print("Transpose :", transpose)
        self.core.announce_transpose(transpose)

    # ------------------------------------------------------------------
    # Song
    # ------------------------------------------------------------------

    def song_track_toggle(self, track):
        current = self.core.get_track_state(
            self.port,
            track,
        )

        if current is None:
            self.core.tracks[track] = None
            print(f"Etat piste {track} inconnu.")
            return

        new_state = not current

        if not self.core.set_track_state(
            self.port,
            track,
            new_state,
        ):
            self.core.tracks[track] = None
            print(f"Impossible de modifier la piste {track}.")
            return

        verified_state = self.core.verify_track_state(
            self.port,
            track,
            new_state,
        )

        if verified_state is None:
            self.core.tracks[track] = None
            print(
                f"Piste {track:02d} modifiée, "
                "mais vérification impossible."
            )
            return

        self.core.tracks[track] = verified_state

        print(
            f"Piste {track:02d} ->",
            "ON" if verified_state else "OFF",
        )
        self.core.announce_track(
            track,
            verified_state,
        )

    def song_play_pause(self):
        current_state = self.core.get_song_play_state(
            self.port
        )

        if current_state is None:
            print("Impossible de lire l'état du Song.")
            return

        if current_state == self.core.SONG_PLAY:
            target_state = self.core.SONG_PAUSE
        else:
            target_state = self.core.SONG_PLAY

        if not self.core.set_song_play_state(
            self.port,
            target_state,
        ):
            print("Impossible de modifier l'état du Song.")
            return

        verified_state = self.core.verify_song_play_state(
            self.port,
            target_state,
        )

        if verified_state is None:
            print(
                "Transport Song modifié, "
                "mais vérification impossible."
            )
            return

        print(
            "Song ->",
            {
                self.core.SONG_STOP: "STOP",
                self.core.SONG_PLAY: "PLAY",
                self.core.SONG_PAUSE: "PAUSE",
            }[verified_state],
        )
        self.core.announce_song_state(verified_state)

    def song_stop(self):
        current_state = self.core.get_song_play_state(
            self.port
        )

        if current_state is None:
            print("Impossible de lire l'état du Song.")
            return

        if current_state == self.core.SONG_STOP:
            print("Song -> STOP")
            self.core.announce_song_state(
                self.core.SONG_STOP
            )
            return

        if not self.core.set_song_play_state(
            self.port,
            self.core.SONG_STOP,
        ):
            print("Impossible d'arrêter le Song.")
            return

        verified_state = self.core.verify_song_play_state(
            self.port,
            self.core.SONG_STOP,
        )

        if verified_state is None:
            print(
                "Stop envoyé, "
                "mais vérification impossible."
            )
            return

        print("Song -> STOP")
        self.core.announce_song_state(verified_state)

    def song_position(self):
        position = self.core.get_song_position(
            self.port
        )

        if position is None:
            print("Impossible de lire la position du Song.")
            return

        measure, beat = position
        print(
            f"Position : mesure {measure}, "
            f"temps {beat}"
        )
        self.core.announce_song_position(
            measure,
            beat,
        )

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------

    def style_part_toggle(self, part_number):
        part = part_number - 1

        with self.core.style_parts_lock:
            new_style_parts = self.core.style_parts.copy()

        new_style_parts[part] = not new_style_parts[part]

        if not self.core.set_style_parts(
            self.port,
            new_style_parts,
        ):
            print(
                "Impossible de modifier "
                f"{self.core.STYLE_PART_LABELS[part]}."
            )
            return

        with self.core.style_parts_lock:
            self.core.style_parts[:] = new_style_parts
            verified_state = self.core.style_parts[part]

        print(
            f"Style {self.core.STYLE_PART_LABELS[part]} ->",
            "ON" if verified_state else "OFF",
        )
        self.core.announce_style_part(
            part,
            verified_state,
        )

    def _change_style_volume(self, delta):
        current_volume = self.core.get_style_volume(
            self.port
        )

        if current_volume is None:
            self.core.style_volume = None
            print("Impossible de lire le volume Style.")
            return

        new_volume = max(
            0,
            min(
                127,
                current_volume + delta,
            ),
        )

        if new_volume == current_volume:
            self.core.style_volume = current_volume
            print(
                "Volume Style :",
                self.core.style_volume,
            )
            self.core.announce_style_volume(
                self.core.style_volume
            )
            return

        if not self.core.set_style_volume(
            self.port,
            new_volume,
        ):
            self.core.style_volume = None
            print("Impossible de modifier le volume Style.")
            return

        verified_volume = self.core.verify_style_volume(
            self.port,
            new_volume,
        )

        if verified_volume is None:
            self.core.style_volume = None
            print(
                "Volume Style modifié, "
                "mais vérification impossible."
            )
            return

        self.core.style_volume = verified_volume
        print(
            "Volume Style :",
            self.core.style_volume,
        )
        self.core.announce_style_volume(
            self.core.style_volume
        )

    def style_volume_up(self):
        self._change_style_volume(
            self.core.STYLE_VOLUME_STEP
        )

    def style_volume_down(self):
        self._change_style_volume(
            -self.core.STYLE_VOLUME_STEP
        )

    # ------------------------------------------------------------------
    # Keyboard voices
    # ------------------------------------------------------------------

    def _voice_part_toggle(self, voice_name, voice_index):
        current = self.core.get_voice_part_state(
            self.port,
            voice_index,
        )

        if current is None:
            print(f"Etat {voice_name} inconnu.")
            return

        new_state = not current

        if not self.core.set_voice_part_state(
            self.port,
            voice_index,
            new_state,
        ):
            print(f"Impossible de modifier {voice_name}.")
            return

        verified_state = self.core.verify_voice_part_state(
            self.port,
            voice_index,
            new_state,
        )

        if verified_state is None:
            print(
                f"{voice_name} modifié, "
                "mais vérification impossible."
            )
            return

        print(
            f"{voice_name.capitalize()} ->",
            "ON" if verified_state else "OFF",
        )
        self.core.announce_voice_part(
            voice_name,
            verified_state,
        )

    def layer_toggle(self):
        self._voice_part_toggle(
            "layer",
            self.core.VOICE_PART_LAYER_INDEX,
        )

    def left_toggle(self):
        self._voice_part_toggle(
            "left",
            self.core.VOICE_PART_LEFT_INDEX,
        )


def initialise_piano(core, port):
    # Permanent receiver: same validated architecture as v1.4.1.
    thread = threading.Thread(
        target=core.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()

    time.sleep(0.3)

    core.sync_tracks(port)

    tempo = core.get_tempo(port)
    transpose = core.get_transpose(port)
    core.style_volume = core.get_style_volume(port)

    # v1.4.1 behaviour preserved: no validated GET for the 8 Style mutes,
    # therefore start from a deterministic all-ON state.
    with core.style_parts_lock:
        core.style_parts[:] = [True] * 8
        startup_style_parts = core.style_parts.copy()

    if core.set_style_parts(
        port,
        startup_style_parts,
    ):
        print("Pistes Style : toutes actives")
    else:
        print("Impossible d'initialiser les pistes Style.")

    print("Tempo :", tempo)
    print("Transpose :", transpose)
    print("Volume Style :", core.style_volume)


def main():
    core = load_core()

    config = load_keyboard_config(
        CONFIG_FILE,
        default_config_path(),
    )

    print()
    print(f"CVP ACCESS V{VERSION}")
    print("=================")
    print("Configuration clavier :", config.source)
    print("Affectations :", len(config.bindings))

    for issue in config.issues or []:
        print("Configuration :", issue)

    print("Voix Piper :", config.speech.voice)
    print("Mode vocal :", config.speech.mode)
    print("Génération WAV :", config.speech.generation)

    # Only speech announcement functions are replaced. The MIDI/SysEx engine
    # remains the validated v1.4.1 code.
    speech_manager = install_speech_hooks(core, config.speech)

    core.acquire_single_instance()

    port = core.find_midi_port()
    if port is None:
        print("Prodipe MIDI introuvable.")
        raise SystemExit(1)

    print("MIDI :", port, "-", core.MIDI_NAME)
    print("Audio :", core.AUDIO_DEVICE)

    initialise_piano(core, port)

    keyboard = core.find_keyboard()
    router = KeyRouter(
        keyboard,
        config,
    )
    actions = CVPActions(
        core,
        port,
    )

    print()
    print("Clavier configurable prêt.")
    if config.caps_lock_layer:
        print(
            "Caps Lock = couche secondaire "
            "(fallback normal : "
            + ("oui" if config.caps_fallback_to_base else "non")
            + ")"
        )
    print()

    for event in keyboard.read_loop():
        invocation = router.process_event(event)

        if invocation is None:
            continue

        try:
            actions.dispatch(invocation)
        except Exception as exc:
            # One bad command must not stop accessibility for all other keys.
            print(
                "Erreur pendant l'action "
                f"{invocation.text} : {exc}"
            )


if __name__ == "__main__":
    main()
