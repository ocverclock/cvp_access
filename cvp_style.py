#!/usr/bin/env python3
"""Fonctions Style centralisées — CVP Access 1.5.1."""

from __future__ import annotations

from cvp_yamaha import decode_yamaha_text, parse_yamaha_path


PROP_STYLE_PATH = [0x06, 0x00, 0x00, 0x01]
PROP_STYLE_START_STOP = [0x06, 0x00, 0x03, 0x01]
PROP_SYNC_START = [0x06, 0x00, 0x07, 0x01]

STYLE_PART_HEADER = [
    0xF0, 0x43, 0x73, 0x01,
    0x51, 0x05, 0x00, 0x00, 0x08,
]

SECTION_VALUES = {
    "intro1": 0x00,
    "intro2": 0x01,
    "intro3": 0x02,
    "main_a": 0x08,
    "main_b": 0x09,
    "main_c": 0x0A,
    "main_d": 0x0B,
    "fill_a": 0x10,
    "fill_b": 0x11,
    "fill_c": 0x12,
    "fill_d": 0x13,
    "break": 0x18,
    "ending1": 0x20,
    "ending2": 0x21,
    "ending3": 0x22,
}


class StyleController:
    def __init__(self, midi):
        self.midi = midi

    def get_path(self):
        data = self.midi.csp_get(PROP_STYLE_PATH, 0x00)
        return decode_yamaha_text(data)

    def get_info(self):
        return parse_yamaha_path(self.get_path())

    def get_sync_start(self):
        data = self.midi.csp_get(PROP_SYNC_START, 0x00)
        if data is None or len(data) != 1:
            return None
        if data[0] == 0:
            return False
        if data[0] == 1:
            return True
        return None

    def set_sync_start(self, enabled):
        return self.midi.csp_set_u7(
            PROP_SYNC_START,
            0x00,
            0x01 if enabled else 0x00,
        )

    def section(self, section):
        if isinstance(section, str):
            try:
                section = SECTION_VALUES[section.lower()]
            except KeyError:
                raise ValueError(f"Section inconnue : {section}")

        if section not in SECTION_VALUES.values():
            raise ValueError(f"Code Section Control non validé : {section:#x}")

        return self.midi.send(
            [0xF0, 0x43, 0x7E, 0x00, section, 0x7F, 0xF7]
        )

    def set_parts(self, states):
        states = tuple(bool(x) for x in states)
        if len(states) != 8:
            raise ValueError("8 états Style attendus")

        return self.midi.send(
            STYLE_PART_HEADER
            + [0x01 if x else 0x00 for x in states]
            + [0xF7]
        )

    @staticmethod
    def encode_style_number(style_number):
        if not 0 <= style_number <= 0x3FFF:
            raise ValueError("Style Number hors plage 14-bit")
        return style_number // 128, style_number % 128

    def select_style_number_genos(self, style_number, *, allow_unvalidated=False):
        """VALIDÉ Genos 1, NON VALIDÉ CVP-905."""
        if not allow_unvalidated:
            raise RuntimeError(
                "Style select 51/05/00/03 est validé Genos uniquement ; "
                "passer allow_unvalidated=True seulement dans un test ciblé."
            )

        hi, lo = self.encode_style_number(style_number)

        return self.midi.send([
            0xF0, 0x43, 0x73, 0x01,
            0x51, 0x05, 0x00, 0x03,
            0x04, 0x00, 0x00, hi, lo,
            0xF7,
        ])
