#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

FIRST_COUNT = 0x10
SECOND_COUNT = 0x10
THIRD_COUNT = 0x80
INDEX_COUNT = 0x20
TOTAL = FIRST_COUNT * SECOND_COUNT * THIRD_COUNT * INDEX_COUNT

FAST_TIMEOUT = 0.055
CONFIRM_TIMEOUT = 0.18
DELAY = 0.003
CHECKPOINT_EVERY = 256

CHECKPOINT = Path("fingering_bruteforce_checkpoint.json")
REPORT = Path("fingering_bruteforce_report.json")


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


def start_midi(engine):
    if not engine.check_port_free():
        raise SystemExit(1)
    port = engine.find_midi_port()
    if port is None:
        raise SystemExit("ERREUR : interface Prodipe MIDI introuvable")
    print("MIDI :", port, "-", engine.MIDI_NAME)
    thread = threading.Thread(target=engine.midi_receiver, args=(port,), daemon=True)
    thread.start()
    time.sleep(0.35)
    return port


def hx(data):
    if data is None:
        return "-"
    return " ".join(f"{b:02X}" for b in data)


def address_from_number(n):
    index = n % INDEX_COUNT
    n //= INDEX_COUNT
    third = n % THIRD_COUNT
    n //= THIRD_COUNT
    second = n % SECOND_COUNT
    n //= SECOND_COUNT
    first = n % FIRST_COUNT
    return [first, second, third, 0x01], index


def key_for(sig, index):
    return f"{sig[0]:02X} {sig[1]:02X} {sig[2]:02X} {sig[3]:02X}|{index:02X}"


def parse_key(key):
    sig_text, index_text = key.split("|")
    sig = [int(x, 16) for x in sig_text.split()]
    return sig, int(index_text, 16)


def get_once(engine, port, sig, index, timeout):
    result = engine.get_property(port, sig, index, timeout=timeout)
    data = result["data"]
    return result["status"], tuple(data) if data is not None else None


def confirm_data(engine, port, sig, index, first_data):
    values = [first_data]
    for _ in range(2):
        status, data = get_once(engine, port, sig, index, CONFIRM_TIMEOUT)
        if status != "DATA":
            return None
        values.append(data)
        time.sleep(0.012)
    return values[0] if all(v == values[0] for v in values) else None


def atomic_write_json(path, payload):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def new_state():
    return {
        "version": 3,
        "phase": "discover_fingered",
        "cursor": 0,
        "fingered_data": {},
        "ai_cursor": 0,
        "ai_states": {},
        "changes": [],
        "confirm_cursor": 0,
        "confirmed": [],
        "updated_at": datetime.now().isoformat(),
    }


def load_state():
    if not CHECKPOINT.is_file():
        return new_state()
    state = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    if state.get("version") != 3:
        raise SystemExit(f"ERREUR : checkpoint incompatible : {CHECKPOINT}")
    return state


def save_state(state):
    state["updated_at"] = datetime.now().isoformat()
    atomic_write_json(CHECKPOINT, state)


def discover_fingered(engine, port, state):
    cursor = int(state.get("cursor", 0))
    found = state.setdefault("fingered_data", {})
    print("\nPHASE 1 - CARTOGRAPHIE FINGERED")
    print("=" * 72)
    print("Reprise :", f"{cursor}/{TOTAL}")
    print("DATA déjà confirmées :", len(found))
    print()

    for n in range(cursor, TOTAL):
        sig, index = address_from_number(n)
        status, data = get_once(engine, port, sig, index, FAST_TIMEOUT)
        if status == "DATA":
            stable = confirm_data(engine, port, sig, index, data)
            if stable is not None:
                key = key_for(sig, index)
                found[key] = hx(stable)
                print("[DATA]", key, "->", hx(stable))

        state["cursor"] = n + 1
        if state["cursor"] % CHECKPOINT_EVERY == 0 or state["cursor"] == TOTAL:
            save_state(state)
            print(
                "...",
                f"{state['cursor']}/{TOTAL}",
                f"({state['cursor'] * 100 / TOTAL:.2f} %)",
                f"DATA confirmées : {len(found)}",
            )
        time.sleep(DELAY)

    state["phase"] = "await_ai"
    save_state(state)


def compare_ai(engine, port, state):
    keys = sorted(state["fingered_data"].keys())
    if not keys:
        print("Aucune DATA découverte.")
        state["phase"] = "done"
        save_state(state)
        return

    cursor = int(state.get("ai_cursor", 0))
    ai_states = state.setdefault("ai_states", {})
    changes = state.setdefault("changes", [])

    print("\nPHASE 2 - COMPARAISON AI FULL KEYBOARD")
    print("=" * 72)
    print("DATA à relire :", len(keys))
    print("Reprise :", f"{cursor}/{len(keys)}")
    print()

    for n in range(cursor, len(keys)):
        key = keys[n]
        sig, index = parse_key(key)
        status, data = get_once(engine, port, sig, index, CONFIRM_TIMEOUT)
        stable = confirm_data(engine, port, sig, index, data) if status == "DATA" else None
        ai_hex = hx(stable) if stable is not None else f"<{status}>"
        ai_states[key] = ai_hex
        fingered_hex = state["fingered_data"][key]

        if stable is not None and ai_hex != fingered_hex:
            if key not in changes:
                changes.append(key)
            print("[CHANGE]", key, ": Fingered=", fingered_hex, "-> AI=", ai_hex)

        state["ai_cursor"] = n + 1
        if state["ai_cursor"] % 64 == 0 or state["ai_cursor"] == len(keys):
            save_state(state)
            print("...", f"{state['ai_cursor']}/{len(keys)}", f"changements : {len(changes)}")
        time.sleep(DELAY)

    state["phase"] = "await_fingered_confirm"
    save_state(state)


def confirm_return(engine, port, state):
    changes = list(state.get("changes", []))
    cursor = int(state.get("confirm_cursor", 0))
    confirmed = state.setdefault("confirmed", [])

    print("\nPHASE 3 - CONFIRMATION RETOUR FINGERED")
    print("=" * 72)
    print("Candidats :", len(changes))
    print()

    for n in range(cursor, len(changes)):
        key = changes[n]
        sig, index = parse_key(key)
        status, data = get_once(engine, port, sig, index, CONFIRM_TIMEOUT)
        stable = confirm_data(engine, port, sig, index, data) if status == "DATA" else None
        returned_hex = hx(stable) if stable is not None else f"<{status}>"
        fingered_hex = state["fingered_data"][key]
        ai_hex = state["ai_states"].get(key, "?")
        print(key, ": F1=", fingered_hex, "| AI=", ai_hex, "| F2=", returned_hex)

        if stable is not None and returned_hex == fingered_hex and ai_hex != fingered_hex:
            if key not in confirmed:
                confirmed.append(key)

        state["confirm_cursor"] = n + 1
        save_state(state)

    state["phase"] = "done"
    save_state(state)


def write_report(state):
    payload = {
        "generated_at": datetime.now().isoformat(),
        "search_space": {
            "first": "00..0F",
            "second": "00..0F",
            "third": "00..7F",
            "index": "00..1F",
            "total_pairs": TOTAL,
        },
        "fingered_data": state.get("fingered_data", {}),
        "ai_states": state.get("ai_states", {}),
        "changes": state.get("changes", []),
        "confirmed": state.get("confirmed", []),
    }
    atomic_write_json(REPORT, payload)


def main():
    state = load_state()

    print("\nCVP ACCESS - FINGERING BRUTE-FORCE RÉSILIENT V3")
    print("=" * 72)
    print("Checkpoint :", CHECKPOINT)
    print("Phase      :", state["phase"])
    print("GET uniquement.")
    print()

    engine = load_engine()
    port = start_midi(engine)

    try:
        if state["phase"] == "discover_fingered":
            input("Mets le CVP sur FINGERED, puis appuie sur Entrée...")
            discover_fingered(engine, port, state)

        if state["phase"] == "await_ai":
            input("\nPasse UNIQUEMENT sur AI FULL KEYBOARD, puis appuie sur Entrée...")
            state["phase"] = "compare_ai"
            save_state(state)

        if state["phase"] == "compare_ai":
            compare_ai(engine, port, state)

        if state["phase"] == "await_fingered_confirm":
            input("\nReviens UNIQUEMENT sur FINGERED, puis appuie sur Entrée...")
            state["phase"] = "confirm_fingered"
            save_state(state)

        if state["phase"] == "confirm_fingered":
            confirm_return(engine, port, state)

        if state["phase"] == "done":
            write_report(state)
            print("\nRÉSUMÉ FINAL")
            print("=" * 72)
            confirmed = state.get("confirmed", [])
            if not confirmed:
                print("Aucun candidat reproductible.")
            else:
                print("CANDIDATS REPRODUCTIBLES :")
                for key in confirmed:
                    print(key, "Fingered=", state["fingered_data"][key], "AI=", state["ai_states"][key])
            print("\nRapport :", REPORT)
            print("Checkpoint conservé :", CHECKPOINT)

    except KeyboardInterrupt:
        print("\nInterruption demandée.")
        print("Enregistrement du checkpoint...")
        save_state(state)
        print("Tu peux relancer exactement la même commande pour reprendre.")

    finally:
        engine.cleanup()


if __name__ == "__main__":
    main()
