#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import threading
import time
from pathlib import Path

FIRST = 0x09
SECOND = 0x00
THIRD_MIN = 0x00
THIRD_MAX = 0x7F
INDEX_MIN = 0x00
INDEX_MAX = 0x0F

TIMEOUT = 0.08
DELAY = 0.006
STABILITY_READS = 2


def load_engine():
    engine_path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")
    if not engine_path.is_file():
        raise SystemExit(f"ERREUR : moteur absent : {engine_path}")

    spec = importlib.util.spec_from_file_location(
        "cvp_probe_engine",
        engine_path,
    )
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


def read_once(engine, port, signature, index):
    result = engine.get_property(
        port,
        signature,
        index,
        timeout=TIMEOUT,
    )
    status = result["status"]
    data = result["data"]
    return status, tuple(data) if data is not None else None


def read_stable(engine, port, signature, index):
    values = []

    for _ in range(STABILITY_READS):
        values.append(
            read_once(engine, port, signature, index)
        )
        time.sleep(0.02)

    if all(value == values[0] for value in values):
        return values[0]

    return "UNSTABLE", None


def make_baseline(engine, port):
    print()
    print("BASELINE FINGERED")
    print("=" * 60)
    print("Famille : 09 00 xx 01")
    print("Third   : 00..7F")
    print("Indexes : 00..0F")
    print("Chaque valeur doit être identique sur 2 lectures.")
    print()

    records = {}
    total = 128 * 16
    done = 0

    for third in range(THIRD_MIN, THIRD_MAX + 1):
        signature = [FIRST, SECOND, third, 0x01]

        for index in range(INDEX_MIN, INDEX_MAX + 1):
            done += 1
            state = read_stable(
                engine,
                port,
                signature,
                index,
            )

            if state[0] in ("DATA", "EMPTY"):
                records[(third, index)] = state

                if state[0] == "DATA":
                    print(
                        f"[DATA] 09 00 {third:02X} 01 "
                        f"idx={index:02X} -> {hx(state[1])}"
                    )

            if done % 128 == 0:
                print(
                    f"... {done}/{total} "
                    f"(réponses stables : {len(records)})"
                )

            time.sleep(DELAY)

    print()
    print("Baseline terminée.")
    print("Réponses stables conservées :", len(records))
    return records


def compare(engine, port, records):
    print()
    print("COMPARAISON AI FULL KEYBOARD")
    print("=" * 60)

    changes = []

    for number, ((third, index), old_state) in enumerate(
        records.items(),
        1,
    ):
        signature = [FIRST, SECOND, third, 0x01]
        new_state = read_stable(
            engine,
            port,
            signature,
            index,
        )

        if new_state[0] != "UNSTABLE" and new_state != old_state:
            changes.append(
                (third, index, old_state, new_state)
            )

        if number % 64 == 0:
            print(f"... {number}/{len(records)}")

        time.sleep(DELAY)

    print()
    print("RÉSUMÉ")
    print("=" * 60)

    if not changes:
        print("Aucun changement stable détecté dans la famille 09 00.")
        return

    for third, index, old_state, new_state in changes:
        print(
            f"[CHANGE] 09 00 {third:02X} 01 idx={index:02X} : "
            f"Fingered={old_state[0]}:{hx(old_state[1])} "
            f"-> AI={new_state[0]}:{hx(new_state[1])}"
        )

    print()
    print("Changements stables :", len(changes))


def main():
    engine = load_engine()
    port = start_midi(engine)

    try:
        print()
        print("RECHERCHE CIBLÉE FINGERING TYPE")
        print("=" * 60)
        print("GET uniquement : aucun SET / RESET / EVENTS.")
        print()

        input(
            "1) Mets le CVP sur FINGERED et ne change rien d'autre, "
            "puis appuie sur Entrée..."
        )

        records = make_baseline(engine, port)

        input(
            "\n2) Passe UNIQUEMENT sur AI FULL KEYBOARD, "
            "puis appuie sur Entrée..."
        )

        compare(engine, port, records)

    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
