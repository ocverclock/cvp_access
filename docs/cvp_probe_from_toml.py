#!/usr/bin/env python3
"""
CVP Access - lanceur de campagne de recherche pilotée par TOML.

Ce script ne contient aucune commande SET/RESET.
Il charge config/research_validation.toml puis délègue les GET au moteur
docs/cvp_probe_readonly.py existant.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tomllib
from pathlib import Path

ALLOWED_TYPES = {"int", "bool", "text", "position", "raw"}
ALLOWED_STATUS = {"validated", "partial", "unexplored"}


def die(message: str):
    raise SystemExit(f"ERREUR CONFIG : {message}")


def parse_hex_byte(value: str, label: str) -> int:
    if not isinstance(value, str):
        die(f"{label} doit être une chaîne hexadécimale.")
    text = value.strip()
    try:
        result = int(text, 16)
    except ValueError:
        die(f"{label} invalide : {value!r}")
    if not 0 <= result <= 0x7F:
        die(f"{label} hors plage 00..7F : {value!r}")
    return result


def parse_signature(text: str, name: str) -> list[int]:
    if not isinstance(text, str):
        die(f"{name}: signature absente/invalide.")
    parts = text.split()
    if len(parts) != 4:
        die(f"{name}: signature attendue = 4 octets, reçu {text!r}.")
    return [parse_hex_byte(part, f"{name}.signature") for part in parts]


def load_engine():
    engine_path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")
    if not engine_path.is_file():
        raise SystemExit(f"Probe moteur introuvable : {engine_path}")

    spec = importlib.util.spec_from_file_location("cvp_probe_readonly_engine", engine_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Impossible de charger cvp_probe_readonly.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_research_config(path: Path):
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    probe_cfg = data.get("probe", {})
    if probe_cfg.get("read_only") is not True:
        die("read_only doit obligatoirement être true.")

    if int(probe_cfg.get("format_version", 0)) != 1:
        die("format_version doit être 1.")

    wanted_status = probe_cfg.get("statuses", ["unexplored", "partial"])
    if not isinstance(wanted_status, list) or not all(
        isinstance(x, str) and x in ALLOWED_STATUS for x in wanted_status
    ):
        die("probe.statuses contient une valeur invalide.")

    include_validated = bool(probe_cfg.get("include_validated", False))
    if include_validated and "validated" not in wanted_status:
        wanted_status = list(wanted_status) + ["validated"]

    properties = {}
    seen = set()

    for item in data.get("property", []):
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            die("une propriété n'a pas de nom.")
        name = name.strip()

        if name in seen:
            die(f"propriété dupliquée : {name}")
        seen.add(name)

        if item.get("enabled", True) is not True:
            continue

        status = item.get("status", "unexplored")
        if status not in ALLOWED_STATUS:
            die(f"{name}: status invalide {status!r}.")
        if status not in wanted_status:
            continue

        prop_type = item.get("type", "raw")
        if prop_type not in ALLOWED_TYPES:
            die(f"{name}: type invalide {prop_type!r}.")

        indexes_raw = item.get("indexes", [])
        if not isinstance(indexes_raw, list) or not indexes_raw:
            die(f"{name}: indexes doit contenir au moins un index.")

        indexes = [
            parse_hex_byte(value, f"{name}.indexes")
            for value in indexes_raw
        ]

        properties[name] = {
            "sig": parse_signature(item.get("signature"), name),
            "indexes": indexes,
            "type": prop_type,
            "project": status,
        }

    if not properties:
        die("aucune propriété active après filtrage.")

    timeout = float(probe_cfg.get("timeout", 0.30))
    if timeout <= 0:
        die("probe.timeout doit être > 0.")

    report_prefix = probe_cfg.get("report_prefix", "cvp_validation_conpianist")
    if not isinstance(report_prefix, str) or not report_prefix.strip():
        die("probe.report_prefix invalide.")

    return properties, timeout, report_prefix.strip()


def print_plan(properties):
    total = sum(len(spec["indexes"]) for spec in properties.values())
    print("CVP ACCESS - PLAN DE VALIDATION READ-ONLY")
    print("=" * 55)
    print(f"Propriétés actives : {len(properties)}")
    print(f"GET planifiés      : {total}")
    print()
    for name, spec in properties.items():
        indexes = " ".join(f"{x:02X}" for x in spec["indexes"])
        signature = " ".join(f"{x:02X}" for x in spec["sig"])
        print(
            f"{name:<20} {spec['project']:<10} "
            f"sig={signature} idx=[{indexes}]"
        )
    print()
    print("Aucun SET / RESET n'est défini dans ce lanceur.")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config" / "research_validation.toml",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Afficher le plan de GET sans ouvrir le MIDI.",
    )

    args, passthrough = parser.parse_known_args()

    properties, timeout, report_prefix = load_research_config(args.config)

    if args.plan:
        print_plan(properties)
        return 0

    engine = load_engine()
    engine.PROPERTIES = properties

    # On laisse le moteur existant gérer MIDI, rapports, --deep, etc.
    forwarded = list(passthrough)

    if "--timeout" not in forwarded:
        forwarded += ["--timeout", str(timeout)]

    if "--output" not in forwarded:
        forwarded += ["--output", report_prefix]

    sys.argv = [str(Path(__file__).name)] + forwarded
    engine.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
