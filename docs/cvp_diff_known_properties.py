#!/usr/bin/env python3
"""
CVP Access - Property Differential Scanner

Réutilise la cartographie issue de :
    fingering_bruteforce_report.json

Au lieu de refaire 1 048 576 GET, ce script relit uniquement les couples
signature/index qui ont déjà retourné une vraie DATA.

Usage :
    python3 docs/cvp_diff_known_properties.py

Le script demande :
    - un nom de test
    - état A (baseline)
    - état B (réglage modifié)
    - retour à l'état A

Il ne retient que les changements reproductibles :
    A1 == A2 != B

GET uniquement.
Aucun SET / RESET / EVENTS.

Sortie :
    diff_<nom_du_test>.json
"""

from __future__ import annotations

import importlib.util
import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path


MAP_REPORT = Path("fingering_bruteforce_report.json")
TIMEOUT = 0.18
DELAY = 0.006


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")

    if not path.is_file():
        raise SystemExit(f"ERREUR : moteur absent : {path}")

    spec = importlib.util.spec_from_file_location(
        "cvp_probe_engine",
        path,
    )

    if spec is None or spec.loader is None:
        raise SystemExit(
            "ERREUR : impossible de charger cvp_probe_readonly.py"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def start_midi(engine):
    if not engine.check_port_free():
        raise SystemExit(1)

    port = engine.find_midi_port()

    if port is None:
        raise SystemExit(
            "ERREUR : interface Prodipe MIDI introuvable"
        )

    print("MIDI :", port, "-", engine.MIDI_NAME)

    thread = threading.Thread(
        target=engine.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()

    time.sleep(0.35)
    return port


def parse_key(key):
    sig_text, index_text = key.split("|")
    signature = [int(x, 16) for x in sig_text.split()]
    index = int(index_text, 16)
    return signature, index


def hx(data):
    if data is None:
        return "-"
    return " ".join(f"{b:02X}" for b in data)


def get_once(engine, port, signature, index):
    result = engine.get_property(
        port,
        signature,
        index,
        timeout=TIMEOUT,
    )

    data = result["data"]

    return (
        result["status"],
        tuple(data) if data is not None else None,
    )


def get_stable(engine, port, signature, index, reads=2):
    states = []

    for _ in range(reads):
        states.append(
            get_once(
                engine,
                port,
                signature,
                index,
            )
        )
        time.sleep(0.012)

    first = states[0]

    if all(state == first for state in states):
        return first

    return "UNSTABLE", None


def load_known_keys():
    if not MAP_REPORT.is_file():
        raise SystemExit(
            f"ERREUR : rapport absent : {MAP_REPORT}\n"
            "Place le script dans ~/CVP_access/docs/ "
            "et lance-le depuis ~/CVP_access."
        )

    payload = json.loads(
        MAP_REPORT.read_text(encoding="utf-8")
    )

    data = payload.get("fingered_data", {})

    if not data:
        raise SystemExit(
            "ERREUR : aucune propriété DATA dans le rapport."
        )

    return sorted(data.keys())


def read_state(engine, port, keys, label):
    print()
    print(label)
    print("=" * 72)

    result = {}

    for n, key in enumerate(keys, 1):
        signature, index = parse_key(key)

        state = get_stable(
            engine,
            port,
            signature,
            index,
        )

        result[key] = state

        if n % 64 == 0 or n == len(keys):
            print("...", f"{n}/{len(keys)}")

        time.sleep(DELAY)

    return result


def slugify(text):
    slug = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text.strip(),
    ).strip("_").lower()

    return slug or "test"


def state_json(state):
    return {
        "status": state[0],
        "data_hex": hx(state[1]),
    }


def main():
    keys = load_known_keys()

    print()
    print("CVP ACCESS - DIFF DES PROPRIÉTÉS CONNUES")
    print("=" * 72)
    print("Propriétés/indexes DATA connus :", len(keys))
    print("GET uniquement.")
    print()

    test_name = input(
        "Nom du test (ex: metronome) : "
    ).strip()

    state_a_name = input(
        "Nom état A (ex: OFF) : "
    ).strip() or "A"

    state_b_name = input(
        "Nom état B (ex: ON) : "
    ).strip() or "B"

    engine = load_engine()
    port = start_midi(engine)

    try:
        input(
            f"\n1) Mets le CVP dans l'état {state_a_name}, "
            "puis Entrée..."
        )

        a1 = read_state(
            engine,
            port,
            keys,
            f"ÉTAT A1 - {state_a_name}",
        )

        input(
            f"\n2) Change UNIQUEMENT le réglage vers {state_b_name}, "
            "puis Entrée..."
        )

        b = read_state(
            engine,
            port,
            keys,
            f"ÉTAT B - {state_b_name}",
        )

        first_changes = []

        for key in keys:
            if (
                a1[key][0] != "UNSTABLE"
                and b[key][0] != "UNSTABLE"
                and a1[key] != b[key]
            ):
                first_changes.append(key)

        print()
        print(
            "Changements A -> B observés :",
            len(first_changes),
        )

        for key in first_changes:
            print(
                "[CHANGE]",
                key,
                ":",
                f"{a1[key][0]}:{hx(a1[key][1])}",
                "->",
                f"{b[key][0]}:{hx(b[key][1])}",
            )

        if not first_changes:
            print()
            print(
                "Aucun changement détecté dans les propriétés connues."
            )
            return

        input(
            f"\n3) Reviens UNIQUEMENT à l'état {state_a_name}, "
            "puis Entrée..."
        )

        print()
        print("CONFIRMATION RETOUR A")
        print("=" * 72)

        confirmed = []
        a2 = {}

        for key in first_changes:
            signature, index = parse_key(key)

            state = get_stable(
                engine,
                port,
                signature,
                index,
                reads=3,
            )

            a2[key] = state

            print(
                key,
                ": A1=",
                f"{a1[key][0]}:{hx(a1[key][1])}",
                "| B=",
                f"{b[key][0]}:{hx(b[key][1])}",
                "| A2=",
                f"{state[0]}:{hx(state[1])}",
            )

            if (
                state == a1[key]
                and b[key] != a1[key]
            ):
                confirmed.append(key)

        print()
        print("RÉSUMÉ FINAL")
        print("=" * 72)

        if not confirmed:
            print("Aucun candidat reproductible.")
        else:
            print("CANDIDATS REPRODUCTIBLES :")

            for key in confirmed:
                print(
                    key,
                    ":",
                    state_a_name,
                    "=",
                    hx(a1[key][1]),
                    "->",
                    state_b_name,
                    "=",
                    hx(b[key][1]),
                )

        output = Path(
            f"diff_{slugify(test_name)}.json"
        )

        payload = {
            "generated_at": datetime.now().isoformat(),
            "test_name": test_name,
            "state_a": state_a_name,
            "state_b": state_b_name,
            "known_pairs": len(keys),
            "changes": [
                {
                    "key": key,
                    "a1": state_json(a1[key]),
                    "b": state_json(b[key]),
                    "a2": state_json(a2[key]),
                    "confirmed": key in confirmed,
                }
                for key in first_changes
            ],
            "confirmed": confirmed,
        }

        output.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        print()
        print("Rapport :", output)

    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
