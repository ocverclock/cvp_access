#!/usr/bin/env python3
"""
CVP Access - scan différentiel READ-ONLY de signatures Yamaha/CSP.

Phase 1:
  état A du réglage -> --baseline FILE.json

Phase 2:
  modifier le réglage sur le CVP -> --compare FILE.json

Aucun SET / RESET / EVENTS n'est envoyé.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import threading
import time
from datetime import datetime
from pathlib import Path


def die(msg):
    raise SystemExit(f"ERREUR : {msg}")


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")
    if not path.is_file():
        die(f"moteur introuvable : {path}")
    spec = importlib.util.spec_from_file_location("cvp_probe_engine", path)
    if spec is None or spec.loader is None:
        die("impossible de charger cvp_probe_readonly.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def hx(values):
    return " ".join(f"{x:02X}" for x in values)


def parse_hex_byte(text, label):
    try:
        value = int(text, 16)
    except ValueError:
        die(f"{label} invalide : {text!r}")
    if not 0 <= value <= 0x7F:
        die(f"{label} hors plage 00..7F")
    return value


def candidate_signatures(family_first, second_min, second_max, third_min, third_max):
    for second in range(second_min, second_max + 1):
        for third in range(third_min, third_max + 1):
            yield [family_first, second, third, 0x01]


def start_midi(engine):
    if not engine.check_port_free():
        raise SystemExit(1)

    port = engine.find_midi_port()
    if port is None:
        die("interface Prodipe MIDI introuvable")

    print("MIDI :", port, "-", engine.MIDI_NAME)

    thread = threading.Thread(
        target=engine.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()
    time.sleep(0.35)
    return port


def do_get(engine, port, sig, index, timeout):
    return engine.get_property(
        port,
        sig,
        index,
        timeout=timeout,
    )


def run_baseline(engine, port, args):
    signatures = list(candidate_signatures(
        args.family,
        args.second_min,
        args.second_max,
        args.third_min,
        args.third_max,
    ))

    print()
    print("CVP ACCESS - BASELINE DIFFERENTIEL READ-ONLY")
    print("=" * 58)
    print(
        f"Famille premier octet : {args.family:02X} ; "
        f"second {args.second_min:02X}..{args.second_max:02X} ; "
        f"third {args.third_min:02X}..{args.third_max:02X}"
    )
    print(f"Index : {args.index:02X}")
    print(f"GET planifiés : {len(signatures)}")
    print("Aucun SET / RESET / EVENTS.")
    print()

    records = []
    data_count = 0
    empty_count = 0

    for n, sig in enumerate(signatures, 1):
        result = do_get(
            engine, port, sig, args.index, args.timeout
        )

        if result["status"] in ("DATA", "EMPTY"):
            rec = {
                "signature": hx(sig),
                "index": args.index,
                "status": result["status"],
                "data_hex": (
                    hx(result["data"])
                    if result["data"] is not None
                    else None
                ),
            }
            records.append(rec)

            if result["status"] == "DATA":
                data_count += 1
                print(
                    f"[DATA]  {rec['signature']} "
                    f"idx={args.index:02X} -> {rec['data_hex']}"
                )
            else:
                empty_count += 1

        if n % 64 == 0:
            print(f"... {n}/{len(signatures)}")

        time.sleep(args.delay)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "mode": "baseline",
        "family": args.family,
        "second_min": args.second_min,
        "second_max": args.second_max,
        "third_min": args.third_min,
        "third_max": args.third_max,
        "index": args.index,
        "timeout": args.timeout,
        "records": records,
    }

    args.baseline.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print()
    print("BASELINE TERMINÉE")
    print("DATA :", data_count)
    print("EMPTY:", empty_count)
    print("Signatures conservées pour comparaison :", len(records))
    print("Fichier :", args.baseline)


def run_compare(engine, port, args):
    payload = json.loads(args.compare.read_text(encoding="utf-8"))
    records = payload.get("records", [])

    print()
    print("CVP ACCESS - COMPARAISON DIFFERENTIELLE READ-ONLY")
    print("=" * 58)
    print(f"Signatures à relire : {len(records)}")
    print("Aucun SET / RESET / EVENTS.")
    print()

    changes = []

    for n, old in enumerate(records, 1):
        sig = [int(x, 16) for x in old["signature"].split()]
        index = int(old["index"])

        result = do_get(
            engine, port, sig, index, args.timeout
        )

        new_status = result["status"]
        new_hex = (
            hx(result["data"])
            if result["data"] is not None
            else None
        )

        if (
            new_status != old["status"]
            or new_hex != old["data_hex"]
        ):
            change = {
                "signature": old["signature"],
                "index": index,
                "old_status": old["status"],
                "old_hex": old["data_hex"],
                "new_status": new_status,
                "new_hex": new_hex,
            }
            changes.append(change)

            print(
                f"[CHANGE] {old['signature']} idx={index:02X} : "
                f"{old['status']}:{old['data_hex'] or '-'} "
                f"-> {new_status}:{new_hex or '-'}"
            )

        if n % 64 == 0:
            print(f"... {n}/{len(records)}")

        time.sleep(args.delay)

    out = args.output or args.compare.with_name(
        args.compare.stem + "_compare.json"
    )
    out.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "baseline": str(args.compare),
                "changes": changes,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print()
    print("COMPARAISON TERMINÉE")
    print("Changements détectés :", len(changes))
    print("Rapport :", out)


def main():
    ap = argparse.ArgumentParser(
        description="Scan différentiel GET-only Yamaha/CVP."
    )

    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--baseline",
        type=Path,
        help="Créer la photographie d'état A dans ce JSON.",
    )
    mode.add_argument(
        "--compare",
        type=Path,
        help="Comparer l'état courant à une baseline JSON.",
    )

    ap.add_argument(
        "--family",
        type=lambda x: parse_hex_byte(x, "family"),
        default=0x00,
        help="Premier octet de propriété en hex (défaut 00).",
    )
    ap.add_argument(
        "--second-min",
        type=lambda x: parse_hex_byte(x, "second-min"),
        default=0x00,
    )
    ap.add_argument(
        "--second-max",
        type=lambda x: parse_hex_byte(x, "second-max"),
        default=0x03,
    )
    ap.add_argument(
        "--third-min",
        type=lambda x: parse_hex_byte(x, "third-min"),
        default=0x00,
    )
    ap.add_argument(
        "--third-max",
        type=lambda x: parse_hex_byte(x, "third-max"),
        default=0x7F,
    )
    ap.add_argument(
        "--index",
        type=lambda x: parse_hex_byte(x, "index"),
        default=0x00,
    )
    ap.add_argument("--timeout", type=float, default=0.08)
    ap.add_argument("--delay", type=float, default=0.008)
    ap.add_argument("--output", type=Path, default=None)

    args = ap.parse_args()

    if args.second_min > args.second_max:
        die("second-min > second-max")
    if args.third_min > args.third_max:
        die("third-min > third-max")
    if args.timeout <= 0:
        die("timeout doit être > 0")

    engine = load_engine()
    port = start_midi(engine)

    try:
        if args.baseline is not None:
            run_baseline(engine, port, args)
        else:
            run_compare(engine, port, args)
    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
