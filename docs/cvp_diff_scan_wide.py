#!/usr/bin/env python3
"""
CVP Access - recherche différentielle LARGE d'une propriété Yamaha/CSP.

Usage typique pour trouver "Chord Fingering Type" :

1) Mettre le CVP en FINGERED.

   python3 docs/cvp_diff_scan_wide.py \
       --baseline fingering_fingered.json

2) Sur l'écran du CVP, passer en AI FULL KEYBOARD.

   python3 docs/cvp_diff_scan_wide.py \
       --compare fingering_fingered.json \
       --output fingering_ai_full_keyboard.json

Le script n'envoie que des GET.
Aucun SET / RESET / EVENTS.

Par défaut il explore :
  premier octet : 00..0F
  deuxième      : 00..03
  troisième     : 00..1F
  index         : 00

Cela couvre 2048 signatures potentielles, puis la comparaison ne relit
que les propriétés ayant répondu lors de la baseline.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import threading
import time
from datetime import datetime
from pathlib import Path


def die(message):
    raise SystemExit(f"ERREUR : {message}")


def parse_hex_byte(text, label):
    try:
        value = int(text, 16)
    except ValueError:
        die(f"{label} invalide : {text!r}")

    if not 0 <= value <= 0x7F:
        die(f"{label} hors plage 00..7F")

    return value


def hx(values):
    return " ".join(f"{value:02X}" for value in values)


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")

    if not path.is_file():
        die(f"moteur introuvable : {path}")

    spec = importlib.util.spec_from_file_location(
        "cvp_probe_engine",
        path,
    )

    if spec is None or spec.loader is None:
        die("impossible de charger cvp_probe_readonly.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def candidate_signatures(args):
    for first in range(
        args.first_min,
        args.first_max + 1,
    ):
        for second in range(
            args.second_min,
            args.second_max + 1,
        ):
            for third in range(
                args.third_min,
                args.third_max + 1,
            ):
                yield [
                    first,
                    second,
                    third,
                    0x01,
                ]


def start_midi(engine):
    if not engine.check_port_free():
        raise SystemExit(1)

    port = engine.find_midi_port()

    if port is None:
        die("interface Prodipe MIDI introuvable")

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


def do_get(
    engine,
    port,
    signature,
    index,
    timeout,
):
    return engine.get_property(
        port,
        signature,
        index,
        timeout=timeout,
    )


def run_baseline(engine, port, args):
    signatures = list(
        candidate_signatures(args)
    )

    print()
    print(
        "CVP ACCESS - BASELINE DIFFERENTIELLE LARGE READ-ONLY"
    )
    print("=" * 66)

    print(
        "Premier octet : "
        f"{args.first_min:02X}..{args.first_max:02X}"
    )
    print(
        "Deuxième      : "
        f"{args.second_min:02X}..{args.second_max:02X}"
    )
    print(
        "Troisième     : "
        f"{args.third_min:02X}..{args.third_max:02X}"
    )
    print(
        "Index         :",
        f"{args.index:02X}",
    )
    print(
        "GET planifiés :",
        len(signatures),
    )
    print(
        "Aucun SET / RESET / EVENTS."
    )
    print()

    records = []

    data_count = 0
    empty_count = 0

    for number, signature in enumerate(
        signatures,
        1,
    ):
        result = do_get(
            engine,
            port,
            signature,
            args.index,
            args.timeout,
        )

        status = result["status"]

        if status in {
            "DATA",
            "EMPTY",
        }:
            data = result["data"]

            data_hex = (
                hx(data)
                if data is not None
                else None
            )

            record = {
                "signature": hx(signature),
                "index": args.index,
                "status": status,
                "data_hex": data_hex,
            }

            records.append(record)

            if status == "DATA":
                data_count += 1

                print(
                    "[DATA]",
                    record["signature"],
                    f"idx={args.index:02X}",
                    "->",
                    data_hex,
                )

            else:
                empty_count += 1

        if number % 128 == 0:
            print(
                "...",
                f"{number}/{len(signatures)}",
                f"(réponses conservées : {len(records)})",
            )

        time.sleep(args.delay)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "mode": "baseline-wide",
        "first_min": args.first_min,
        "first_max": args.first_max,
        "second_min": args.second_min,
        "second_max": args.second_max,
        "third_min": args.third_min,
        "third_max": args.third_max,
        "index": args.index,
        "timeout": args.timeout,
        "records": records,
    }

    args.baseline.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("BASELINE TERMINÉE")
    print("DATA :", data_count)
    print("EMPTY:", empty_count)
    print(
        "Propriétés à comparer :",
        len(records),
    )
    print(
        "Fichier :",
        args.baseline,
    )


def run_compare(engine, port, args):
    payload = json.loads(
        args.compare.read_text(
            encoding="utf-8"
        )
    )

    records = payload.get(
        "records",
        [],
    )

    if not records:
        die(
            "la baseline ne contient aucune propriété exploitable"
        )

    print()
    print(
        "CVP ACCESS - COMPARAISON DIFFERENTIELLE LARGE"
    )
    print("=" * 66)
    print(
        "Propriétés à relire :",
        len(records),
    )
    print(
        "Aucun SET / RESET / EVENTS."
    )
    print()

    changes = []

    for number, old in enumerate(
        records,
        1,
    ):
        signature = [
            int(value, 16)
            for value in old[
                "signature"
            ].split()
        ]

        index = int(
            old["index"]
        )

        result = do_get(
            engine,
            port,
            signature,
            index,
            args.timeout,
        )

        new_status = result[
            "status"
        ]

        data = result["data"]

        new_hex = (
            hx(data)
            if data is not None
            else None
        )

        if (
            new_status
            != old["status"]
            or new_hex
            != old["data_hex"]
        ):
            change = {
                "signature": old[
                    "signature"
                ],
                "index": index,
                "old_status": old[
                    "status"
                ],
                "old_hex": old[
                    "data_hex"
                ],
                "new_status": new_status,
                "new_hex": new_hex,
            }

            changes.append(change)

            print(
                "[CHANGE]",
                old["signature"],
                f"idx={index:02X}",
                ":",
                f"{old['status']}:{old['data_hex'] or '-'}",
                "->",
                f"{new_status}:{new_hex or '-'}",
            )

        if number % 64 == 0:
            print(
                "...",
                f"{number}/{len(records)}",
            )

        time.sleep(args.delay)

    output = (
        args.output
        if args.output is not None
        else args.compare.with_name(
            args.compare.stem
            + "_compare.json"
        )
    )

    output.write_text(
        json.dumps(
            {
                "generated_at":
                    datetime.now().isoformat(),
                "baseline":
                    str(args.compare),
                "changes":
                    changes,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("COMPARAISON TERMINÉE")
    print(
        "Changements détectés :",
        len(changes),
    )
    print(
        "Rapport :",
        output,
    )

    if changes:
        print()
        print(
            "CANDIDATS À TESTER EN PRIORITÉ"
        )
        print("-" * 42)

        for change in changes:
            print(
                change["signature"],
                f"idx={change['index']:02X}",
                ":",
                change["old_hex"],
                "->",
                change["new_hex"],
            )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Scan différentiel GET-only large "
            "des propriétés Yamaha/CSP."
        )
    )

    mode = parser.add_mutually_exclusive_group(
        required=True
    )

    mode.add_argument(
        "--baseline",
        type=Path,
        help=(
            "Créer la photographie "
            "de l'état A."
        ),
    )

    mode.add_argument(
        "--compare",
        type=Path,
        help=(
            "Comparer l'état actuel "
            "à la baseline."
        ),
    )

    parser.add_argument(
        "--first-min",
        type=lambda value:
            parse_hex_byte(
                value,
                "first-min",
            ),
        default=0x00,
    )

    parser.add_argument(
        "--first-max",
        type=lambda value:
            parse_hex_byte(
                value,
                "first-max",
            ),
        default=0x0F,
    )

    parser.add_argument(
        "--second-min",
        type=lambda value:
            parse_hex_byte(
                value,
                "second-min",
            ),
        default=0x00,
    )

    parser.add_argument(
        "--second-max",
        type=lambda value:
            parse_hex_byte(
                value,
                "second-max",
            ),
        default=0x03,
    )

    parser.add_argument(
        "--third-min",
        type=lambda value:
            parse_hex_byte(
                value,
                "third-min",
            ),
        default=0x00,
    )

    parser.add_argument(
        "--third-max",
        type=lambda value:
            parse_hex_byte(
                value,
                "third-max",
            ),
        default=0x1F,
    )

    parser.add_argument(
        "--index",
        type=lambda value:
            parse_hex_byte(
                value,
                "index",
            ),
        default=0x00,
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=0.08,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.008,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    for low, high, label in (
        (
            args.first_min,
            args.first_max,
            "first",
        ),
        (
            args.second_min,
            args.second_max,
            "second",
        ),
        (
            args.third_min,
            args.third_max,
            "third",
        ),
    ):
        if low > high:
            die(
                f"{label}-min > "
                f"{label}-max"
            )

    if args.timeout <= 0:
        die(
            "timeout doit être > 0"
        )

    engine = load_engine()
    port = start_midi(
        engine
    )

    try:
        if (
            args.baseline
            is not None
        ):
            run_baseline(
                engine,
                port,
                args,
            )
        else:
            run_compare(
                engine,
                port,
                args,
            )
    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
