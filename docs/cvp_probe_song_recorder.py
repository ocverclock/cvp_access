#!/usr/bin/env python3
"""CVP-905 Song Recorder probe — GET-only A1/B/A2 differential scan."""

from __future__ import annotations
import argparse, importlib.util, json, threading, time
from datetime import datetime
from pathlib import Path

TIMEOUT = 0.16


def load_engine():
    p = Path(__file__).with_name("cvp_probe_readonly.py")
    spec = importlib.util.spec_from_file_location("cvp_probe_engine", p)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Impossible de charger {p}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def start_midi(e):
    if not e.check_port_free():
        raise SystemExit(1)
    port = e.find_midi_port()
    if port is None:
        raise SystemExit("Interface Prodipe MIDI introuvable")
    t = threading.Thread(target=e.midi_receiver, args=(port,), daemon=True)
    t.start()
    time.sleep(.35)
    print("MIDI :", port, "-", e.MIDI_NAME)
    return port


def stop_midi(e):
    p = getattr(e, "midi_process", None)
    if p is not None and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=1)
        except Exception:
            p.kill()


def parse_hex_csv(text):
    out = [int(x.strip(), 16) for x in text.split(",") if x.strip()]
    if not out or any(x < 0 or x > 0x7F for x in out):
        raise ValueError("valeurs hex attendues entre 00 et 7F")
    return out


def key(sig, idx):
    return f"{' '.join(f'{x:02X}' for x in sig)} | {idx:02X}"


def read_once(e, port, sig, idx):
    r = e.get_property(port, sig, idx, timeout=TIMEOUT)
    data = r.get("data")
    return (r.get("status", "UNKNOWN"), tuple(data) if data is not None else None)


def read_stable(e, port, sig, idx):
    a = read_once(e, port, sig, idx)
    time.sleep(.01)
    b = read_once(e, port, sig, idx)
    return a if a == b else ("UNSTABLE", None)


def scan(e, port, targets, label):
    print("\n" + label)
    print("=" * 72)
    out = {}
    for n, (sig, idx) in enumerate(targets, 1):
        out[key(sig, idx)] = read_stable(e, port, sig, idx)
        if n % 32 == 0 or n == len(targets):
            print(f"... {n}/{len(targets)}")
        time.sleep(.004)
    return out


def hx(data):
    return "-" if data is None else " ".join(f"{x:02X}" for x in data)


def js(state):
    return {"status": state[0], "data_hex": hx(state[1])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--families",
        default="00",
        help="familles après 04, hex CSV; défaut 00",
    )
    ap.add_argument(
        "--indexes",
        default="00",
        help="indexes CSP, hex CSV; défaut 00",
    )
    ap.add_argument("--output-dir", default="docs/research")
    args = ap.parse_args()

    try:
        families = parse_hex_csv(args.families)
        indexes = parse_hex_csv(args.indexes)
    except ValueError as exc:
        raise SystemExit(str(exc))

    targets = [
        ([0x04, family, param, 0x01], idx)
        for family in families
        for param in range(0x80)
        for idx in indexes
    ]

    print("CVP ACCESS — SONG RECORDER PROBE")
    print("GET uniquement. Aucun SET/RESET/Record n'est envoyé.")
    print("Cibles :", len(targets))
    print("Arrêter cvp-access.service avant le test.")

    aname = input("État A [NORMAL] : ").strip() or "NORMAL"
    bname = input("État B [RECORD_READY] : ").strip() or "RECORD_READY"

    e = load_engine()
    port = start_midi(e)
    try:
        input(f"\n1) Mets le CVP en {aname}, puis Entrée...")
        a1 = scan(e, port, targets, f"A1 — {aname}")
        input(f"\n2) Active MANUELLEMENT {bname}, puis Entrée...")
        b = scan(e, port, targets, f"B — {bname}")
        input(f"\n3) Annule et reviens en {aname}, puis Entrée...")
        a2 = scan(e, port, targets, f"A2 — {aname}")
    finally:
        stop_midi(e)

    candidates = []
    a1b = []
    for k in a1:
        if "UNSTABLE" in (a1[k][0], b[k][0], a2[k][0]):
            continue
        if a1[k] != b[k]:
            a1b.append({"key": k, "a": js(a1[k]), "b": js(b[k])})
        if a1[k] == a2[k] and a1[k] != b[k]:
            candidates.append({"key": k, "a": js(a1[k]), "b": js(b[k])})

    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool": "cvp_probe_song_recorder.py",
        "safety": "GET-only",
        "state_a": aname,
        "state_b": bname,
        "families": [f"{x:02X}" for x in families],
        "indexes": [f"{x:02X}" for x in indexes],
        "target_count": len(targets),
        "reproducible_changes": candidates,
        "a1_to_b_changes": a1b,
    }
    jp = outdir / f"song_recorder_{stamp}.json"
    mp = outdir / f"song_recorder_{stamp}.md"
    jp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# CVP-905 — Song Recorder differential probe",
        "",
        "Méthode : **GET-only A1 → B → A2**.",
        "",
        f"- A : `{aname}`",
        f"- B : `{bname}`",
        f"- cibles : `{len(targets)}`",
        "",
        "## Candidats reproductibles",
        "",
    ]
    if candidates:
        lines += ["| Propriété | A | B |", "|---|---|---|"]
        for c in candidates:
            lines.append(
                f"| `{c['key']}` | `{c['a']['status']} {c['a']['data_hex']}` "
                f"| `{c['b']['status']} {c['b']['data_hex']}` |"
            )
    else:
        lines.append("Aucun changement `A1 == A2 != B`.")
    lines += [
        "",
        "Un candidat n'est **pas** une commande validée. Ne faire aucun SET à ce stade.",
        "",
    ]
    mp.write_text("\n".join(lines), encoding="utf-8")

    print("\nCandidats reproductibles :", len(candidates))
    for c in candidates:
        print(" ", c["key"], c["a"]["data_hex"], "->", c["b"]["data_hex"])
    print("JSON :", jp)
    print("MD   :", mp)


if __name__ == "__main__":
    main()
