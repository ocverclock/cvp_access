#!/usr/bin/env python3
"""
CVP Access - validation fonctionnelle réversible pilotée par TOML.

Sécurité :
- sans --execute : aucun SET n'est envoyé ;
- chaque test fait GET -> SET -> GET -> RESTORE -> GET ;
- si la restauration n'est pas confirmée, la campagne s'arrête ;
- seules les données 1 octet bool/u7 sont acceptées dans cette version.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import threading
import time
import tomllib
from datetime import datetime
from pathlib import Path


ALLOWED_KINDS = {"bool", "u7"}


def fail(message: str):
    raise SystemExit(f"ERREUR : {message}")


def parse_hex_byte(text, label):
    if not isinstance(text, str):
        fail(f"{label} doit être une chaîne hexadécimale.")
    try:
        value = int(text.strip(), 16)
    except ValueError:
        fail(f"{label} invalide : {text!r}")
    if not 0 <= value <= 0x7F:
        fail(f"{label} hors plage 00..7F : {text!r}")
    return value


def parse_signature(text, name):
    if not isinstance(text, str):
        fail(f"{name}: signature manquante.")
    parts = text.split()
    if len(parts) != 4:
        fail(f"{name}: signature attendue sur 4 octets.")
    return [parse_hex_byte(x, f"{name}.signature") for x in parts]


def load_engine():
    path = Path(__file__).resolve().with_name("cvp_probe_readonly.py")
    if not path.is_file():
        fail(f"moteur read-only introuvable : {path}")

    spec = importlib.util.spec_from_file_location("cvp_probe_engine", path)
    if spec is None or spec.loader is None:
        fail("impossible de charger cvp_probe_readonly.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config(path: Path, wave: int):
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    cfg = data.get("validation", {})
    if int(cfg.get("format_version", 0)) != 1:
        fail("validation.format_version doit être 1.")

    if cfg.get("require_execute_flag") is not True:
        fail("require_execute_flag doit rester à true.")

    tests = []
    seen = set()

    for item in data.get("test", []):
        name = item.get("name")
        if not isinstance(name, str) or not name:
            fail("un test n'a pas de nom.")
        if name in seen:
            fail(f"test dupliqué : {name}")
        seen.add(name)

        if item.get("enabled", True) is not True:
            continue
        if int(item.get("wave", 1)) != wave:
            continue

        kind = item.get("kind")
        if kind not in ALLOWED_KINDS:
            fail(
                f"{name}: kind={kind!r} n'est pas automatisable "
                "par cette version."
            )

        mutation = item.get("mutation")
        if kind == "bool" and mutation != "toggle":
            fail(f"{name}: un bool doit utiliser mutation='toggle'.")
        if kind == "u7" and mutation != "step":
            fail(f"{name}: un u7 doit utiliser mutation='step'.")

        test = {
            "name": name,
            "signature": parse_signature(item.get("signature"), name),
            "index": parse_hex_byte(item.get("index"), f"{name}.index"),
            "kind": kind,
            "mutation": mutation,
            "comment": item.get("comment", ""),
        }

        if kind == "u7":
            test["step"] = int(item.get("step", 1))
            test["min"] = int(item.get("min", 0))
            test["max"] = int(item.get("max", 127))

            if not 0 <= test["min"] <= test["max"] <= 127:
                fail(f"{name}: plage min/max invalide.")
            if test["step"] <= 0:
                fail(f"{name}: step doit être > 0.")

        tests.append(test)

    if not tests:
        fail(f"aucun test actif pour wave={wave}.")

    settings = {
        "timeout": float(cfg.get("timeout", 0.40)),
        "apply_delay": float(cfg.get("apply_delay", 0.15)),
        "between_tests": float(cfg.get("between_tests", 0.10)),
        "verify_attempts": int(cfg.get("verify_attempts", 4)),
    }

    return settings, tests


def hex_bytes(values):
    return " ".join(f"{x:02X}" for x in values)


def get_data(engine, port, test, timeout):
    result = engine.get_property(
        port,
        test["signature"],
        test["index"],
        timeout=timeout,
    )

    if result["status"] != "DATA":
        return result["status"], None

    return "DATA", result["data"]


def set_property(engine, port, test, data):
    if not data or len(data) > 0x7F:
        return False

    message = (
        engine.HEADER
        + [0x01, 0x01]
        + test["signature"]
        + [test["index"], 0x01, 0x00]
        + [0x00, len(data)]
        + data
        + [0xF7]
    )

    return engine.send_sysex(port, message)


def choose_test_value(test, initial):
    if len(initial) != 1:
        return None, "DATA_LEN_NOT_1"

    value = initial[0]

    if test["kind"] == "bool":
        if value not in (0, 1):
            return None, f"BOOL_RAW_{value:02X}"
        return [0 if value else 1], None

    minimum = test["min"]
    maximum = test["max"]
    step = test["step"]

    if not minimum <= value <= maximum:
        return None, f"OUT_OF_CONFIG_RANGE_{value}"

    if value + step <= maximum:
        candidate = value + step
    elif value - step >= minimum:
        candidate = value - step
    else:
        return None, "NO_SAFE_STEP"

    return [candidate], None


def verify(engine, port, test, expected, settings):
    last_status = None
    last_data = None

    time.sleep(settings["apply_delay"])

    for attempt in range(settings["verify_attempts"]):
        status, data = get_data(
            engine,
            port,
            test,
            settings["timeout"],
        )
        last_status = status
        last_data = data

        if status == "DATA" and data == expected:
            return True, status, data

        if attempt < settings["verify_attempts"] - 1:
            time.sleep(0.08)

    return False, last_status, last_data


def plan_line(test):
    sig = hex_bytes(test["signature"])
    suffix = ""
    if test["kind"] == "u7":
        suffix = (
            f" step={test['step']} "
            f"range={test['min']}..{test['max']}"
        )
    return (
        f"{test['name']:<22} "
        f"sig={sig} idx={test['index']:02X} "
        f"{test['kind']}/{test['mutation']}{suffix}"
    )


def run_one(engine, port, test, settings):
    record = {
        "name": test["name"],
        "signature": hex_bytes(test["signature"]),
        "index": test["index"],
        "index_hex": f"{test['index']:02X}",
        "kind": test["kind"],
        "status": None,
        "initial_hex": None,
        "test_hex": None,
        "observed_hex": None,
        "restored_hex": None,
    }

    status, initial = get_data(
        engine, port, test, settings["timeout"]
    )

    if status != "DATA" or initial is None:
        record["status"] = f"SKIP_INITIAL_{status}"
        return record, False

    record["initial_hex"] = hex_bytes(initial)

    candidate, reason = choose_test_value(test, initial)
    if candidate is None:
        record["status"] = f"SKIP_{reason}"
        return record, False

    record["test_hex"] = hex_bytes(candidate)

    print(
        f"[TEST] {test['name']}: "
        f"{record['initial_hex']} -> {record['test_hex']}"
    )

    set_sent = False

    try:
        if not set_property(engine, port, test, candidate):
            record["status"] = "SET_SEND_ERROR"
            return record, False

        set_sent = True

        ok, observed_status, observed = verify(
            engine, port, test, candidate, settings
        )

        if observed is not None:
            record["observed_hex"] = hex_bytes(observed)

        if ok:
            print("       SET confirmé.")
        else:
            print(
                "       SET non confirmé ; "
                f"lu={observed_status} "
                f"{record['observed_hex'] or ''}"
            )

        # Même si le SET ne semble pas appliqué, on restaure par sécurité.
        if not set_property(engine, port, test, initial):
            record["status"] = "RESTORE_SEND_ERROR"
            return record, True

        restore_ok, restore_status, restored = verify(
            engine, port, test, initial, settings
        )

        if restored is not None:
            record["restored_hex"] = hex_bytes(restored)

        if not restore_ok:
            record["status"] = "RESTORE_VERIFY_FAILED"
            print(
                "       !!! RESTAURATION NON CONFIRMÉE !!! "
                f"lu={restore_status} "
                f"{record['restored_hex'] or ''}"
            )
            return record, True

        print("       Restauration confirmée.")

        record["status"] = (
            "PASS"
            if ok
            else "SET_NOT_APPLIED_RESTORED"
        )
        return record, False

    except BaseException:
        # Dernière tentative de restauration si un SET avait été envoyé.
        if set_sent:
            try:
                set_property(engine, port, test, initial)
                verify(engine, port, test, initial, settings)
            except Exception:
                pass
        raise


def write_reports(records, prefix, wave):
    payload = {
        "generated_at": datetime.now().isoformat(),
        "wave": wave,
        "records": records,
    }

    counts = {}
    for rec in records:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    payload["summary"] = counts

    json_path = Path(f"{prefix}.json")
    md_path = Path(f"{prefix}.md")

    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        f"# CVP functional validation - wave {wave}",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "## Résumé",
        "",
    ]

    for status in sorted(counts):
        lines.append(f"- {status}: {counts[status]}")

    lines += [
        "",
        "## Tests",
        "",
        "| Test | Signature | Index | Initial | Test | Observé | Restauré | Statut |",
        "|---|---|---:|---|---|---|---|---|",
    ]

    for rec in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    rec["name"],
                    f"`{rec['signature']}`",
                    f"`0x{rec['index_hex']}`",
                    f"`{rec['initial_hex'] or ''}`",
                    f"`{rec['test_hex'] or ''}`",
                    f"`{rec['observed_hex'] or ''}`",
                    f"`{rec['restored_hex'] or ''}`",
                    rec["status"],
                ]
            )
            + " |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path, counts


def main():
    parser = argparse.ArgumentParser(
        description="Validation fonctionnelle réversible Yamaha/CVP."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "config"
        / "functional_validation.toml",
    )
    parser.add_argument("--wave", type=int, default=1)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Autoriser les SET réversibles. Sans cette option : plan uniquement.",
    )
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    settings, tests = load_config(args.config, args.wave)

    print(f"CVP ACCESS - VALIDATION FONCTIONNELLE WAVE {args.wave}")
    print("=" * 62)
    print(f"Tests actifs : {len(tests)}")
    print()
    for test in tests:
        print(plan_line(test))
    print()

    if not args.execute:
        print("MODE PLAN : aucun SET envoyé.")
        print("Ajoute --execute pour lancer la validation réversible.")
        return 0

    engine = load_engine()

    if not engine.check_port_free():
        fail("port MIDI occupé.")

    port = engine.find_midi_port()
    if port is None:
        fail("interface Prodipe MIDI introuvable.")

    print(f"MIDI : {port} - {engine.MIDI_NAME}")
    print(
        "MODE EXECUTION : GET -> SET -> GET -> RESTORE -> GET\n"
        "Arrêt immédiat si une restauration n'est pas confirmée."
    )
    print()

    thread = threading.Thread(
        target=engine.midi_receiver,
        args=(port,),
        daemon=True,
    )
    thread.start()
    time.sleep(0.35)

    records = []

    try:
        for number, test in enumerate(tests, 1):
            print(f"{number:02d}/{len(tests):02d} ", end="")
            record, fatal_restore = run_one(
                engine, port, test, settings
            )
            records.append(record)

            if fatal_restore:
                print()
                print(
                    "CAMPAGNE ARRÊTÉE : une restauration "
                    "n'a pas été confirmée."
                )
                break

            time.sleep(settings["between_tests"])

    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")

    finally:
        engine.cleanup()

    prefix = (
        args.output
        if args.output
        else datetime.now().strftime(
            f"cvp_functional_wave{args.wave}_%Y%m%d_%H%M%S"
        )
    )

    json_path, md_path, counts = write_reports(
        records, prefix, args.wave
    )

    print()
    print("RÉSUMÉ")
    print("======")
    for status in sorted(counts):
        print(f"{status}: {counts[status]}")

    print()
    print("Rapport JSON :", json_path)
    print("Rapport Markdown :", md_path)


if __name__ == "__main__":
    raise SystemExit(main())
