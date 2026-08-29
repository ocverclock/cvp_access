#!/usr/bin/env python3
"""Utilitaires communs Yamaha pour CVP Access 1.5.1.

Le format texte validé sur CVP-905 pour Song/Style est un flux de groupes :
    [masque bits hauts] [jusqu'à 7 octets de données]

Il n'y a PAS de longueur 14-bit au début du payload observé.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


def decode_14bit(high: int, low: int) -> int:
    return ((high & 0x7F) << 7) | (low & 0x7F)


def encode_14bit(value: int) -> list[int]:
    if not 0 <= value <= 0x3FFF:
        raise ValueError("Valeur 14-bit hors plage")
    return [(value >> 7) & 0x7F, value & 0x7F]


def decode_yamaha_text(data) -> str | None:
    """Décode le texte Yamaha validé sur CVP-905."""
    if data is None:
        return None

    payload = bytes(data)
    if not payload:
        return ""

    result = bytearray()
    pos = 0

    while pos < len(payload):
        highbits = payload[pos] & 0x7F
        pos += 1

        chunk = payload[pos:pos + 7]
        pos += len(chunk)

        for index, value in enumerate(chunk):
            mask_bit = 6 - index
            if highbits & (1 << mask_bit):
                value |= 0x80
            result.append(value)

    raw = bytes(result).rstrip(b"\x00")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def encode_yamaha_text(text: str) -> bytes:
    """Encode une chaîne dans le format Yamaha 7-bit packed.

    Cette fonction centralise le format mais ne revendique aucune commande
    SET texte comme validée sur CVP.
    """
    raw = text.encode("utf-8")
    out = bytearray()

    for pos in range(0, len(raw), 7):
        chunk = raw[pos:pos + 7]
        mask = 0
        values = bytearray()

        for index, value in enumerate(chunk):
            if value & 0x80:
                mask |= 1 << (6 - index)
            values.append(value & 0x7F)

        out.append(mask)
        out.extend(values)

    return bytes(out)


@dataclass(frozen=True)
class YamahaPath:
    raw: str
    source: str | None
    path: str
    name: str
    extension: str
    categories: tuple[str, ...]


def parse_yamaha_path(value: str | None) -> YamahaPath | None:
    if value is None:
        return None

    source = None
    path = value

    if ":" in value:
        prefix, rest = value.split(":", 1)
        if prefix in {"PRESET", "USER", "USB1"}:
            source = prefix
            path = rest

    path = path.lstrip("/")
    parts = tuple(p for p in path.split("/") if p)

    filename = parts[-1] if parts else ""
    suffix = PurePosixPath(filename).suffix
    name = filename[:-len(suffix)] if suffix else filename

    return YamahaPath(
        raw=value,
        source=source,
        path=path,
        name=name,
        extension=suffix.lstrip("."),
        categories=parts[:-1],
    )
