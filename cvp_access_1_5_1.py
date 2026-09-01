#!/usr/bin/env python3
"""CVP Access v1.5.1-RC1-dev.

Consolidation progressive :
- conserve v1.5 + moteur v1.4.1 comme base éprouvée ;
- branche l'API MIDI et les contrôleurs 1.5.1 ;
- corrige le nom Song ;
- expose les informations Style/Song validées ;
- expose Sync Start, Guide, Stream Lights et Métronome ;
- garde les résultats Genos verrouillés hors runtime CVP.
"""

from __future__ import annotations

import importlib.util
import re
import time
from pathlib import Path

import cvp_keyboard
from cvp_keyboard import ActionSpec

from cvp_midi import MidiService
from cvp_registration import RegistrationController
from cvp_song_151 import SongController
from cvp_speech_151 import install_speech_hooks
from cvp_style import StyleController
from cvp_voice import VoiceController
from cvp_yamaha import parse_yamaha_path


VERSION = "1.5.1-RC1-dev"
LEGACY_FILENAME = "cvp_access_v1.5.py"

PROP_GUIDE = [0x04, 0x03, 0x00, 0x01]
PROP_STREAM_LIGHTS = [0x04, 0x02, 0x00, 0x01]


def load_legacy():
    path = Path(__file__).resolve().with_name(
        LEGACY_FILENAME
    )
    if not path.is_file():
        raise SystemExit(
            f"Runtime historique absent : {path}"
        )

    spec = importlib.util.spec_from_file_location(
        "cvp_access_v15_base",
        path,
    )
    if spec is None or spec.loader is None:
        raise SystemExit(
            "Impossible de charger CVP Access v1.5."
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load_legacy()


# ---------------------------------------------------------------------
# Catalogue d'actions 1.5.1
# ---------------------------------------------------------------------

NEW_ACTION_SPECS = {
    "announce_style_name": ActionSpec(
        description="Annonce le Style actuellement sélectionné"
    ),
    "announce_song_name": ActionSpec(
        description="Annonce le Song actuellement chargé"
    ),
    "announce_song_length": ActionSpec(
        description="Annonce la longueur du Song"
    ),
    "sync_start_toggle": ActionSpec(
        description="Active ou désactive Sync Start"
    ),
    "metronome_toggle": ActionSpec(
        description="Active ou désactive le métronome"
    ),
    "guide_toggle": ActionSpec(
        description="Active ou désactive Guide"
    ),
    "stream_lights_toggle": ActionSpec(
        description="Active ou désactive Stream Lights"
    ),
}

cvp_keyboard.ACTION_SPECS.update(
    NEW_ACTION_SPECS
)


def default_config_path() -> Path:
    return Path(__file__).resolve().with_name(
        "default-keyboard-1.5.1.toml"
    )


def clean_yamaha_display_name(value):
    if not value:
        return None

    info = parse_yamaha_path(value)
    if info is None:
        return None

    name = info.name

    # Identifiants techniques Yamaha présents dans certains noms de fichiers :
    # Cool 8Beat.T308 -> Cool 8Beat
    # Shallow.S000 -> Shallow
    name = re.sub(
        r"\.[TS]\d+$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    return name or value


class CVPActions151(legacy.CVPActions):

    def __init__(self, core, port):
        super().__init__(
            core,
            port,
        )

        self.midi = MidiService(
            core,
            port,
        )
        self.song = SongController(
            core,
            port,
        )
        self.style = StyleController(
            self.midi
        )
        self.voice = VoiceController(
            self.midi
        )
        self.registration = RegistrationController(
            self.midi
        )

    # ----------------------------------------------------------
    # Nouveau dispatch ; les actions v1.5 restent intactes.
    # ----------------------------------------------------------

    def dispatch(self, invocation):
        handlers = {
            "announce_style_name": self.announce_style_name,
            "announce_song_name": self.announce_song_name,
            "announce_song_length": self.announce_song_length,
            "sync_start_toggle": self.sync_start_toggle,
            "metronome_toggle": self.metronome_toggle,
            "guide_toggle": self.guide_toggle,
            "stream_lights_toggle": self.stream_lights_toggle,
        }

        handler = handlers.get(
            invocation.name
        )

        if handler is None:
            return super().dispatch(
                invocation
            )

        if invocation.parameter is None:
            return handler()

        return handler(
            invocation.parameter
        )

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def announce_style_name(self):
        raw = self.style.get_path()

        if raw is None:
            print(
                "Impossible de lire le Style courant."
            )
            self.core.announce_action_help(
                "Impossible de lire le Style courant"
            )
            return

        if raw == "":
            print(
                "Aucun Style identifié."
            )
            self.core.announce_action_help(
                "Aucun Style identifié"
            )
            return

        name = clean_yamaha_display_name(
            raw
        )

        print(
            "Style courant :",
            raw,
        )
        self.core.announce_named_value(
            "Style",
            name,
        )

    def announce_song_name(self):
        raw = self.song.get_name()

        if raw is None:
            print(
                "Impossible de lire le Song courant."
            )
            self.core.announce_action_help(
                "Impossible de lire le Song courant"
            )
            return

        if raw == "":
            print(
                "Aucun Song chargé."
            )
            self.core.announce_no_song()
            return

        name = clean_yamaha_display_name(
            raw
        )

        print(
            "Song courant :",
            raw,
        )
        self.core.announce_named_value(
            "Song",
            name,
        )

    def announce_song_length(self):
        length = self.song.get_length()

        if length is None:
            print(
                "Impossible de lire la longueur du Song."
            )
            self.core.announce_action_help(
                "Impossible de lire la longueur du Song"
            )
            return

        measures, _ = length

        print(
            "Longueur Song :",
            measures,
            "mesures",
        )
        self.core.announce_song_length(
            measures
        )

    # ----------------------------------------------------------
    # Booléens CVP validés
    # ----------------------------------------------------------

    def _toggle_bool_property(
        self,
        prop,
        *,
        label,
        stem,
        index=0x00,
    ):
        data = self.midi.csp_get(
            prop,
            index,
        )

        if (
            data is None
            or len(data) != 1
            or data[0] not in (0x00, 0x01)
        ):
            print(
                f"Impossible de lire {label}."
            )
            self.core.announce_action_help(
                f"Impossible de lire {label}"
            )
            return

        target = (
            0x00
            if data[0] == 0x01
            else 0x01
        )

        if not self.midi.csp_set_u7(
            prop,
            index,
            target,
        ):
            print(
                f"Impossible de modifier {label}."
            )
            return

        verified = None
        time.sleep(0.05)

        for attempt in range(3):
            result = self.midi.csp_get(
                prop,
                index,
            )
            if (
                result is not None
                and len(result) == 1
                and result[0] == target
            ):
                verified = target
                break

            if attempt < 2:
                time.sleep(0.05)

        if verified is None:
            print(
                f"{label} modifié, "
                "mais vérification impossible."
            )
            return

        enabled = verified == 0x01

        print(
            f"{label} ->",
            "ON" if enabled else "OFF",
        )
        self.core.announce_boolean_state(
            label,
            enabled,
            stem,
        )

    def sync_start_toggle(self):
        self._toggle_bool_property(
            [0x06, 0x00, 0x07, 0x01],
            label="Sync Start",
            stem="sync_start",
        )

    def guide_toggle(self):
        self._toggle_bool_property(
            PROP_GUIDE,
            label="Guide",
            stem="guide",
        )

    def stream_lights_toggle(self):
        self._toggle_bool_property(
            PROP_STREAM_LIGHTS,
            label="Stream Lights",
            stem="stream_lights",
        )

    def metronome_toggle(self):
        state = self.song.get_metronome()

        if state is None:
            print(
                "Impossible de lire le métronome."
            )
            self.core.announce_action_help(
                "Impossible de lire le métronome"
            )
            return

        target = not state

        if not self.song.set_metronome(
            target
        ):
            print(
                "Impossible de modifier le métronome."
            )
            return

        verified = self.song.verify_metronome(
            target
        )

        if verified is None:
            print(
                "Métronome modifié, "
                "mais vérification impossible."
            )
            return

        print(
            "Métronome ->",
            "ON" if verified else "OFF",
        )
        self.core.announce_boolean_state(
            "Métronome",
            verified,
            "metronome",
        )

    # ----------------------------------------------------------
    # Registration via contrôleur 1.5.1
    # ----------------------------------------------------------

    def registration_recall(self, number):
        try:
            ok = self.registration.recall(
                number,
                verify_notification=False,
            )
        except ValueError:
            print(
                "Numero de Registration invalide :",
                number,
            )
            return

        if not ok:
            print(
                "Impossible de rappeler Registration",
                number,
            )
            return

        print(
            "Registration ->",
            number,
        )
        self.core.announce_action_help(
            f"Registration {number}"
        )


# Monkeypatch volontaire du frontend stable :
# son main(), son initialisation hardware et ses anciennes actions restent la base.
legacy.VERSION = VERSION
legacy.CVPActions = CVPActions151
legacy.SongController = SongController
legacy.install_speech_hooks = install_speech_hooks
legacy.default_config_path = default_config_path


def main():
    return legacy.main()


if __name__ == "__main__":
    main()
