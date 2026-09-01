#!/usr/bin/env python3
"""Décodage et résolution des Voices CVP-905."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CVPVoiceId:
    msb: int
    lsb: int
    program: int  # 1..128, comme la Data List Yamaha


def decode_cvp_voice(raw):
    """Décode le format Yamaha 4 x 7 bits en MSB/LSB/PC#."""
    if raw is None:
        return None

    data = bytes(raw)

    if len(data) != 4:
        return None

    if any(value > 0x7F for value in data):
        return None

    b0, b1, b2, b3 = data

    packed = (
        (b0 << 21)
        | (b1 << 14)
        | (b2 << 7)
        | b3
    )

    return CVPVoiceId(
        msb=(packed >> 16) & 0xFF,
        lsb=(packed >> 8) & 0xFF,
        program=(packed & 0xFF) + 1,
    )


# Première validation matérielle CVP-905 firmware 1.03.
# Source des noms / numéros :
# Yamaha CVP-909/CVP-905 Data List.
VOICE_NAMES = {
    CVPVoiceId(108, 0, 1): "CFX Concert Grand",
    CVPVoiceId(8, 33, 50): "Seattle Strings",
    CVPVoiceId(104, 7, 5): "Suitcase Soft",
}


def resolve_voice_name(identifier):
    if identifier is None:
        return None
    return VOICE_NAMES.get(identifier)
