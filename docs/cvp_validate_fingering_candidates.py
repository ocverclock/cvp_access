#!/usr/bin/env python3
"""
CVP Access - validation ciblée des 4 candidats Fingering Type.

Le script ne fait que des GET.

Séquence :
1. Mettre le CVP en AI Full Keyboard
2. Valider avec Entrée
3. Le script lit 3 fois les 4 candidats
4. Mettre le CVP en Fingered
5. Valider avec Entrée
6. Le script relit 3 fois les 4 candidats
7. Résumé des changements stables
"""

from __future__ import annotations

import importlib.util
import threading
import time
from pathlib import Path


CANDIDATES = [
    ("00 00 00 01", [0x00, 0x00, 0x00, 0x01]),
    ("00 00 01 01", [0x00, 0x00, 0x01, 0x01]),
    ("00 00 02 01", [0x00, 0x00, 0x02, 0x01]),
    ("00 00 03 01", [0x00, 0x00, 0x03, 0x01]),
]

INDEX = 0x00
READS = 3
TIMEOUT = 0.20


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")
    if not path.is_file():
        raise SystemExit(f"ERREUR : moteur absent : {path}")

    spec = importlib.util.spec_from_file_location("cvp_probe_engine", path)
    if spec is None or spec.loader is None:
        raise SystemExit("ERREUR : impossible de charger cvp_probe_readonly.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hx(data):
    if data is None:
        return "-"
    return " ".join(f"{b:02X}" for b in data)


def start_midi(engine):
    if not engine.check_port_free():
        raise SystemExit(1)

    port = engine.find_midi_port()
    if port is None:
        raise SystemExit("ERREUR : interface Prodipe MIDI introuvable")

    print("MIDI :", port, "-", engine.MIDI_NAME)

    thread = threading.Thread(
        target=engine.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()
    time.sleep(0.35)

    return port


def snapshot(engine, port, label):
    print()
    print(label)
    print("=" * len(label))

    result = {}

    for text, signature in CANDIDATES:
        values = []

        for attempt in range(READS):
            response = engine.get_property(
                port,
                signature,
                INDEX,
                timeout=TIMEOUT,
            )

            status = response["status"]
            data = response["data"]

            values.append((status, tuple(data) if data is not None else None))

            print(
                f"{text} idx=00 lecture {attempt + 1} : "
                f"{status} {hx(data)}"
            )

            time.sleep(0.08)

        result[text] = values
        print()

    return result


def stable_value(readings):
    if not readings:
        return None

    first = readings[0]

    if all(item == first for item in readings):
        return first

    return None


def show_summary(ai, fingered):
    print()
    print("RÉSUMÉ")
    print("=" * 60)

    changes = 0

    for text, _ in CANDIDATES:
        ai_value = stable_value(ai[text])
        fingered_value = stable_value(fingered[text])

        if ai_value is None:
            print(text, ": lectures AI instables")
            continue

        if fingered_value is None:
            print(text, ": lectures Fingered instables")
            continue

        ai_status, ai_data = ai_value
        fi_status, fi_data = fingered_value

        ai_hex = hx(ai_data)
        fi_hex = hx(fi_data)

        if ai_value != fingered_value:
            changes += 1
            print(
                f"[CHANGE] {text} idx=00 : "
                f"AI={ai_status}:{ai_hex} "
                f"-> Fingered={fi_status}:{fi_hex}"
            )
        else:
            print(
                f"[STABLE] {text} idx=00 : "
                f"{ai_status}:{ai_hex}"
            )

    print()
    print("Changements stables :", changes)


def main():
    engine = load_engine()
    port = start_midi(engine)

    try:
        print()
        print("TEST CIBLÉ FINGERING TYPE")
        print("=" * 60)
        print("Aucun SET n'est envoyé.")
        print()

        input(
            "1) Mets le CVP sur AI Full Keyboard, "
            "puis appuie sur Entrée..."
        )

        ai = snapshot(
            engine,
            port,
            "ÉTAT A : AI FULL KEYBOARD",
        )

        input(
            "2) Change UNIQUEMENT le CVP sur Fingered, "
            "puis appuie sur Entrée..."
        )

        fingered = snapshot(
            engine,
            port,
            "ÉTAT B : FINGERED",
        )

        show_summary(ai, fingered)

    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
