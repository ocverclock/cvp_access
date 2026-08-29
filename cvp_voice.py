#!/usr/bin/env python3
"""Fonctions Voice centralisées — CVP Access 1.5.1."""

from __future__ import annotations

from dataclasses import dataclass


PROP_VOICE_MIDI = [0x02, 0x00, 0x01, 0x01]
PROP_VOICE_PRESET = [0x02, 0x00, 0x00, 0x01]

# Mapping validé sur GENOS 1 uniquement.
GENOS_KEYBOARD_PARTS = {
    "right1": 0x01,
    "right2": 0x02,
    "right3": 0x03,
    "left": 0x04,
}


@dataclass(frozen=True)
class XGVoice:
    msb: int
    lsb: int
    program_raw: int

    @property
    def program(self):
        return self.program_raw + 1


class VoiceController:
    def __init__(self, midi):
        self.midi = midi

    def get_cvp_midi_raw(self, index):
        return self.midi.csp_get(
            PROP_VOICE_MIDI,
            index,
        )

    def get_cvp_preset_raw(self, index):
        return self.midi.csp_get(
            PROP_VOICE_PRESET,
            index,
        )

    def get_xg_voice(self, part, *, allow_unvalidated=False):
        if not allow_unvalidated:
            raise RuntimeError(
                "XG Voice keyboard mapping validé Genos uniquement."
            )

        if isinstance(part, str):
            try:
                part = GENOS_KEYBOARD_PARTS[part.lower()]
            except KeyError:
                raise ValueError(f"Partie Genos inconnue : {part}")

        values = []
        for param in (0x01, 0x02, 0x03):
            data = self.midi.xg_get(
                (0x08, part, param),
                attempts=3,
            )
            if data is None or len(data) != 1:
                return None
            values.append(data[0])

        return XGVoice(
            msb=values[0],
            lsb=values[1],
            program_raw=values[2],
        )

    def set_xg_voice(self, part, voice, *, allow_unvalidated=False):
        if not allow_unvalidated:
            raise RuntimeError(
                "XG Voice SET validé Genos uniquement."
            )

        if isinstance(part, str):
            try:
                part = GENOS_KEYBOARD_PARTS[part.lower()]
            except KeyError:
                raise ValueError(f"Partie Genos inconnue : {part}")

        if not isinstance(voice, XGVoice):
            voice = XGVoice(*voice)

        return (
            self.midi.xg_set((0x08, part, 0x01), [voice.msb])
            and self.midi.xg_set((0x08, part, 0x02), [voice.lsb])
            and self.midi.xg_set((0x08, part, 0x03), [voice.program_raw])
        )
