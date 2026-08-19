#!/usr/bin/env python3
"""
CVP Access - recherche différentielle adaptative du Chord Fingering Type.

Objectif :
    identifier la propriété Yamaha/CSP qui change entre :
        FINGERED
        AI FULL KEYBOARD

Principe :
    - un seul lancement du script ;
    - aucun SET / RESET / EVENTS ;
    - uniquement des GET ;
    - baseline FINGERED ;
    - comparaison AI FULL KEYBOARD ;
    - confirmation retour FINGERED ;
    - les changements ne sont retenus que s'ils sont reproductibles.

Exploration principale :
    propriété = FIRST SECOND THIRD 01
    FIRST  = 00..0F
    SECOND = 00..0F
    THIRD  = 00..3F
    INDEX  = 00

Le script ne relit ensuite que les propriétés qui ont réellement répondu
à la baseline. Les signatures ayant un changement reproductible sont aussi
testées sur les indexes 00..0F.

Le rapport final est enregistré dans :
    fingering_adaptive_report.json
"""

from __future__ import annotations

import importlib.util
import json
import threading
import time
from datetime import datetime
from pathlib import Path


FIRST_MIN = 0x00
FIRST_MAX = 0x0F
SECOND_MIN = 0x00
SECOND_MAX = 0x0F
THIRD_MIN = 0x00
THIRD_MAX = 0x3F

BASE_INDEX = 0x00
INDEX_CONFIRM_MIN = 0x00
INDEX_CONFIRM_MAX = 0x0F

FAST_TIMEOUT = 0.055
CONFIRM_TIMEOUT = 0.18
DELAY = 0.004
STABLE_READS = 2

REPORT_FILE = Path("fingering_adaptive_report.json")


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")

    if not path.is_file():
        raise SystemExit(
            f"ERREUR : moteur absent : {path}"
        )

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

    print(
        "MIDI :",
        port,
        "-",
        engine.MIDI_NAME,
    )

    thread = threading.Thread(
        target=engine.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()

    time.sleep(0.35)
    return port


def hx(data):
    if data is None:
        return "-"

    return " ".join(
        f"{value:02X}"
        for value in data
    )


def signature_text(signature):
    return " ".join(
        f"{value:02X}"
        for value in signature
    )


def iter_signatures():
    for first in range(
        FIRST_MIN,
        FIRST_MAX + 1,
    ):
        for second in range(
            SECOND_MIN,
            SECOND_MAX + 1,
        ):
            for third in range(
                THIRD_MIN,
                THIRD_MAX + 1,
            ):
                yield [
                    first,
                    second,
                    third,
                    0x01,
                ]


def get_once(
    engine,
    port,
    signature,
    index,
    timeout,
):
    result = engine.get_property(
        port,
        signature,
        index,
        timeout=timeout,
    )

    status = result["status"]
    data = result["data"]

    return (
        status,
        tuple(data)
        if data is not None
        else None,
    )


def get_stable(
    engine,
    port,
    signature,
    index,
    timeout,
    reads=STABLE_READS,
):
    values = []

    for _ in range(reads):
        values.append(
            get_once(
                engine,
                port,
                signature,
                index,
                timeout,
            )
        )
        time.sleep(0.012)

    first = values[0]

    if all(
        value == first
        for value in values
    ):
        return first

    return (
        "UNSTABLE",
        None,
    )


def state_to_json(state):
    return {
        "status": state[0],
        "data_hex": hx(state[1]),
    }


def scan_baseline(
    engine,
    port,
):
    signatures = list(
        iter_signatures()
    )

    print()
    print(
        "PHASE 1 - BASELINE FINGERED"
    )
    print("=" * 68)
    print(
        "Signatures prévues :",
        len(signatures),
    )
    print(
        "Plage : FIRST 00..0F ; "
        "SECOND 00..0F ; THIRD 00..3F ; idx=00"
    )
    print(
        "Chaque réponse est contrôlée deux fois."
    )
    print()

    responders = {}

    for number, signature in enumerate(
        signatures,
        1,
    ):
        state = get_stable(
            engine,
            port,
            signature,
            BASE_INDEX,
            FAST_TIMEOUT,
        )

        if state[0] in {
            "DATA",
            "EMPTY",
        }:
            key = signature_text(
                signature
            )

            responders[key] = state

            if state[0] == "DATA":
                print(
                    "[DATA]",
                    key,
                    "idx=00 ->",
                    hx(state[1]),
                )

        if number % 256 == 0:
            print(
                "...",
                f"{number}/{len(signatures)}",
                f"(réponses stables : {len(responders)})",
            )

        time.sleep(DELAY)

    print()
    print(
        "Baseline terminée."
    )
    print(
        "Réponses stables conservées :",
        len(responders),
    )

    return responders


def compare_state(
    engine,
    port,
    responders,
    label,
):
    print()
    print(label)
    print("=" * 68)

    current = {}
    changes = []

    for number, (
        sig_text,
        old_state,
    ) in enumerate(
        responders.items(),
        1,
    ):
        signature = [
            int(value, 16)
            for value in sig_text.split()
        ]

        state = get_stable(
            engine,
            port,
            signature,
            BASE_INDEX,
            CONFIRM_TIMEOUT,
        )

        current[sig_text] = state

        if (
            state[0] != "UNSTABLE"
            and state != old_state
        ):
            changes.append(
                (
                    sig_text,
                    old_state,
                    state,
                )
            )

            print(
                "[CHANGE]",
                sig_text,
                "idx=00 :",
                f"{old_state[0]}:{hx(old_state[1])}",
                "->",
                f"{state[0]}:{hx(state[1])}",
            )

        if number % 64 == 0:
            print(
                "...",
                f"{number}/{len(responders)}",
            )

        time.sleep(DELAY)

    print()
    print(
        "Changements observés :",
        len(changes),
    )

    return current, changes


def confirm_return_to_fingered(
    engine,
    port,
    baseline,
    ai_state,
    ai_changes,
):
    print()
    print(
        "PHASE 3 - CONFIRMATION RETOUR FINGERED"
    )
    print("=" * 68)

    confirmed = []

    candidate_names = {
        item[0]
        for item in ai_changes
    }

    for sig_text in sorted(
        candidate_names
    ):
        signature = [
            int(value, 16)
            for value in sig_text.split()
        ]

        state = get_stable(
            engine,
            port,
            signature,
            BASE_INDEX,
            CONFIRM_TIMEOUT,
            reads=3,
        )

        original = baseline[
            sig_text
        ]

        ai = ai_state[
            sig_text
        ]

        print(
            sig_text,
            "idx=00 :",
            "Fingered initial =",
            f"{original[0]}:{hx(original[1])}",
            "| AI =",
            f"{ai[0]}:{hx(ai[1])}",
            "| Fingered retour =",
            f"{state[0]}:{hx(state[1])}",
        )

        if (
            state == original
            and ai != original
            and ai[0] != "UNSTABLE"
        ):
            confirmed.append(
                sig_text
            )

    print()
    print(
        "Candidats reproductibles :",
        len(confirmed),
    )

    return confirmed


def scan_indexes_for_candidates(
    engine,
    port,
    confirmed,
):
    if not confirmed:
        return {}

    print()
    print(
        "PHASE 4 - INDEXES DES CANDIDATS"
    )
    print("=" * 68)
    print(
        "Lecture FINGERED des indexes 00..0F "
        "pour chaque signature confirmée."
    )

    result = {}

    for sig_text in confirmed:
        signature = [
            int(value, 16)
            for value in sig_text.split()
        ]

        per_index = {}

        for index in range(
            INDEX_CONFIRM_MIN,
            INDEX_CONFIRM_MAX + 1,
        ):
            state = get_stable(
                engine,
                port,
                signature,
                index,
                CONFIRM_TIMEOUT,
            )

            if state[0] in {
                "DATA",
                "EMPTY",
            }:
                per_index[
                    f"{index:02X}"
                ] = state_to_json(
                    state
                )

                print(
                    sig_text,
                    f"idx={index:02X}",
                    "->",
                    f"{state[0]}:{hx(state[1])}",
                )

        result[
            sig_text
        ] = per_index

    return result


def save_report(
    baseline,
    ai_state,
    ai_changes,
    confirmed,
    index_data,
):
    payload = {
        "generated_at":
            datetime.now().isoformat(),
        "scan": {
            "first":
                f"{FIRST_MIN:02X}..{FIRST_MAX:02X}",
            "second":
                f"{SECOND_MIN:02X}..{SECOND_MAX:02X}",
            "third":
                f"{THIRD_MIN:02X}..{THIRD_MAX:02X}",
            "base_index":
                f"{BASE_INDEX:02X}",
        },
        "baseline_responses": {
            key: state_to_json(
                value
            )
            for key, value
            in baseline.items()
        },
        "ai_state": {
            key: state_to_json(
                value
            )
            for key, value
            in ai_state.items()
        },
        "ai_changes": [
            {
                "signature": sig,
                "fingered":
                    state_to_json(old),
                "ai_full_keyboard":
                    state_to_json(new),
            }
            for sig, old, new
            in ai_changes
        ],
        "confirmed_candidates":
            confirmed,
        "candidate_indexes":
            index_data,
    }

    REPORT_FILE.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    engine = load_engine()
    port = start_midi(
        engine
    )

    try:
        print()
        print(
            "CVP ACCESS - RECHERCHE ADAPTATIVE FINGERING TYPE"
        )
        print("=" * 68)
        print(
            "GET uniquement : aucun SET / RESET / EVENTS."
        )
        print(
            "Ne change aucun autre réglage pendant le test."
        )
        print()

        input(
            "1) Mets le CVP sur FINGERED, "
            "puis appuie sur Entrée..."
        )

        baseline = scan_baseline(
            engine,
            port,
        )

        input(
            "\n2) Passe UNIQUEMENT sur AI FULL KEYBOARD, "
            "puis appuie sur Entrée..."
        )

        ai_state, ai_changes = compare_state(
            engine,
            port,
            baseline,
            "PHASE 2 - AI FULL KEYBOARD",
        )

        if not ai_changes:
            print()
            print(
                "Aucun changement stable détecté "
                "à l'index 00 dans cette plage."
            )

            save_report(
                baseline,
                ai_state,
                ai_changes,
                [],
                {},
            )

            print(
                "Rapport :",
                REPORT_FILE,
            )
            return

        input(
            "\n3) Reviens UNIQUEMENT sur FINGERED, "
            "puis appuie sur Entrée..."
        )

        confirmed = confirm_return_to_fingered(
            engine,
            port,
            baseline,
            ai_state,
            ai_changes,
        )

        index_data = scan_indexes_for_candidates(
            engine,
            port,
            confirmed,
        )

        save_report(
            baseline,
            ai_state,
            ai_changes,
            confirmed,
            index_data,
        )

        print()
        print(
            "RÉSUMÉ FINAL"
        )
        print("=" * 68)

        if not confirmed:
            print(
                "Aucun candidat reproductible."
            )
        else:
            print(
                "CANDIDATS REPRODUCTIBLES :"
            )

            for sig_text in confirmed:
                old = baseline[
                    sig_text
                ]
                new = ai_state[
                    sig_text
                ]

                print(
                    sig_text,
                    "idx=00 :",
                    f"Fingered={old[0]}:{hx(old[1])}",
                    "->",
                    f"AI={new[0]}:{hx(new[1])}",
                )

        print()
        print(
            "Rapport complet :",
            REPORT_FILE,
        )

    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
