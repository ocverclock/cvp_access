#!/usr/bin/env python3
"""
CVP Access - observateur READ-ONLY de propriétés Yamaha/CVP.

Le script effectue uniquement des GET et affiche les changements de valeur
brute pendant que l'utilisateur modifie un réglage sur le piano.
"""

from __future__ import annotations

import argparse
import importlib.util
import threading
import time
import tomllib
from pathlib import Path


def die(msg):
    raise SystemExit(f"ERREUR : {msg}")


def parse_byte(value, label):
    if not isinstance(value, str):
        die(f"{label} doit être une chaîne hexadécimale")
    try:
        result = int(value.strip(), 16)
    except ValueError:
        die(f"{label} invalide : {value!r}")
    if not 0 <= result <= 0x7F:
        die(f"{label} hors plage 00..7F")
    return result


def parse_sig(value, name):
    if not isinstance(value, str):
        die(f"{name}: signature manquante")
    parts = value.split()
    if len(parts) != 4:
        die(f"{name}: signature attendue sur 4 octets")
    return [parse_byte(x, f"{name}.signature") for x in parts]


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")
    spec = importlib.util.spec_from_file_location("cvp_probe_engine", path)
    if spec is None or spec.loader is None:
        die("impossible de charger cvp_probe_readonly.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_config(path):
    with path.open("rb") as f:
        data = tomllib.load(f)

    watch = data.get("watch", {})
    if int(watch.get("format_version", 0)) != 1:
        die("watch.format_version doit être 1")

    interval = float(watch.get("interval", 0.20))
    timeout = float(watch.get("timeout", 0.30))

    props = []
    seen = set()

    for item in data.get("property", []):
        name = item.get("name")
        if not isinstance(name, str) or not name:
            die("propriété sans nom")
        if name in seen:
            die(f"propriété dupliquée : {name}")
        seen.add(name)

        props.append({
            "name": name,
            "sig": parse_sig(item.get("signature"), name),
            "index": parse_byte(item.get("index"), f"{name}.index"),
        })

    if not props:
        die("aucune propriété")
    return interval, timeout, props


def hx(data):
    if data is None:
        return "-"
    return " ".join(f"{b:02X}" for b in data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "config"
        / "cvp905_characterization.toml",
    )
    args = ap.parse_args()

    interval, timeout, props = load_config(args.config)
    engine = load_engine()

    if not engine.check_port_free():
        raise SystemExit(1)

    port = engine.find_midi_port()
    if port is None:
        die("interface Prodipe MIDI introuvable")

    print("CVP ACCESS - OBSERVATEUR READ-ONLY")
    print("=" * 50)
    print("MIDI :", port, "-", engine.MIDI_NAME)
    print("GET uniquement. Aucun SET / RESET.")
    print("Modifie un seul réglage à la fois sur le CVP.")
    print("Ctrl+C pour arrêter.")
    print()

    thread = threading.Thread(
        target=engine.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()
    time.sleep(0.35)

    previous = {}

    try:
        while True:
            for prop in props:
                result = engine.get_property(
                    port,
                    prop["sig"],
                    prop["index"],
                    timeout=timeout,
                )

                status = result["status"]
                data = result["data"]
                current = (status, tuple(data) if data is not None else None)

                if prop["name"] not in previous:
                    print(
                        f"[INIT] {prop['name']:<22} "
                        f"{status:<8} {hx(data)}"
                    )
                    previous[prop["name"]] = current

                elif current != previous[prop["name"]]:
                    old_status, old_data = previous[prop["name"]]
                    old_list = list(old_data) if old_data is not None else None
                    print(
                        f"[CHANGE] {prop['name']:<20} "
                        f"{old_status}:{hx(old_list)} "
                        f"-> {status}:{hx(data)}"
                    )
                    previous[prop["name"]] = current

                time.sleep(0.015)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nArrêt.")

    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
