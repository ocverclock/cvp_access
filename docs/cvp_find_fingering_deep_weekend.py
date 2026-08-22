#!/usr/bin/env python3
"""
CVP Access - Fingering deep weekend scan

Goals
-----
- GET only for unknown CSP properties.
- Only validated Registration recalls are used to switch comparison states.
- Compare REG5 (AI Full Keyboard) vs REG6 (AI Fingered) block-by-block.
- Re-scan the previous 20..7F area as part of a broader 00..7F index sweep.
- Expand p0/p1 search space while keeping the campaign within a weekend budget.
- Probe alternate p3 values at index 00 after the main sweep.
- Use REG7 only as a control to identify Registration-number mirrors (04/05/06).
- SQLite checkpointing; completed blocks survive reboot/restart.
- Liveness GET (Tempo) before/after scans so a powered-off CVP cannot create
  silently-completed empty blocks.

Unknown CSP writes are NEVER sent.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import queue
import resource
import sqlite3
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

P2_RANGE = tuple(range(0x00, 0x80))
FULL_INDEX_RANGE = tuple(range(0x00, 0x80))
ALT_P3_VALUES = tuple(x for x in range(0x00, 0x10) if x != 0x01)
QUERY_BATCH = 1500

REG5 = [0xF0,0x43,0x73,0x01,0x52,0x25,0x11,0x00,0x02,0x00,0x04,0xF7]
REG6 = [0xF0,0x43,0x73,0x01,0x52,0x25,0x11,0x00,0x02,0x00,0x05,0xF7]
REG7 = [0xF0,0x43,0x73,0x01,0x52,0x25,0x11,0x00,0x02,0x00,0x06,0xF7]
REG_NOTIFY = [0xF0,0x43,0x73,0x01,0x52,0x25,0x00,0x01,0x01,0x00,0x01]

TEMPO_PROP = [0x08, 0x00, 0x00, 0x01]
TEMPO_INDEX = 0x00


@dataclass(frozen=True)
class Zone:
    name: str
    p0_values: tuple[int, ...]
    p1_values: tuple[int, ...]
    p3_values: tuple[int, ...]
    indexes: tuple[int, ...]
    priority: int


ZONES = (
    # Repasses the previous domain, but now indexes 00..7F instead of 20..7F.
    Zone(
        "CORE_FULL_INDEX",
        tuple(range(0x00, 0x10)),
        tuple(range(0x00, 0x10)),
        (0x01,),
        FULL_INDEX_RANGE,
        1,
    ),
    # Expand the first property byte while preserving the high-probability p1 range.
    Zone(
        "P0_EXT_10_1F",
        tuple(range(0x10, 0x20)),
        tuple(range(0x00, 0x10)),
        (0x01,),
        FULL_INDEX_RANGE,
        2,
    ),
    # Symmetric expansion of the second property byte.
    Zone(
        "P1_EXT_10_1F",
        tuple(range(0x00, 0x10)),
        tuple(range(0x10, 0x20)),
        (0x01,),
        FULL_INDEX_RANGE,
        3,
    ),
    # Lower-probability structural tail: alternate p3 values, index 00 only.
    # This remains cheap enough to run after the main weekend sweep.
    Zone(
        "ALT_P3_IDX00",
        tuple(range(0x00, 0x10)),
        tuple(range(0x00, 0x10)),
        ALT_P3_VALUES,
        (0x00,),
        4,
    ),
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blocks (
    zone TEXT NOT NULL,
    p0 INTEGER NOT NULL,
    p1 INTEGER NOT NULL,
    key_count INTEGER NOT NULL,
    a_count INTEGER NOT NULL,
    b_count INTEGER NOT NULL,
    diff_count INTEGER NOT NULL,
    completed_at TEXT NOT NULL,
    elapsed_seconds REAL NOT NULL,
    PRIMARY KEY(zone,p0,p1)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS candidates (
    p0 INTEGER NOT NULL,
    p1 INTEGER NOT NULL,
    p2 INTEGER NOT NULL,
    p3 INTEGER NOT NULL,
    idx INTEGER NOT NULL,
    zone TEXT NOT NULL,

    a_status TEXT NOT NULL,
    a_data BLOB NOT NULL,
    b_status TEXT NOT NULL,
    b_data BLOB NOT NULL,

    a2_status TEXT,
    a2_data BLOB,
    a2_ok INTEGER NOT NULL DEFAULT 0,

    b2_status TEXT,
    b2_data BLOB,
    b2_ok INTEGER NOT NULL DEFAULT 0,

    c_status TEXT,
    c_data BLOB,
    reg_mirror_040506 INTEGER NOT NULL DEFAULT 0,
    exact_0c_03 INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY(p0,p1,p2,p3,idx)
) WITHOUT ROWID;
"""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def rss_mib() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def connect_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA wal_autocheckpoint=1000")
    conn.execute("PRAGMA journal_size_limit=67108864")
    conn.execute("PRAGMA cache_size=-8192")
    conn.execute("PRAGMA temp_store=FILE")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA)
    return conn


def set_meta(conn: sqlite3.Connection, key: str, value) -> None:
    conn.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def get_meta(conn: sqlite3.Connection, key: str, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return default if row is None else row[0]


def state_to_db(state):
    if state is None:
        return "MISSING", b""
    return state[0], bytes(state[1])


def state_from_db(status, data):
    if status == "MISSING":
        return None
    return status, tuple(bytes(data or b""))


def state_to_json(state):
    if state is None:
        return None
    return {"status": state[0], "data": list(state[1])}


def key_tuple_to_text(t) -> str:
    p0,p1,p2,p3,idx = t
    return f"{p0:02X} {p1:02X} {p2:02X} {p3:02X}|{idx:02X}"


def load_engine(path: Path):
    spec = importlib.util.spec_from_file_location("cvp_probe_engine", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Impossible de charger le moteur MIDI: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def start_midi(engine):
    port = engine.find_midi_port()
    if not port:
        raise RuntimeError("Interface Prodipe introuvable")

    print("MIDI :", port, flush=True)
    t = threading.Thread(target=engine.midi_receiver, args=(port,), daemon=True)
    t.start()
    time.sleep(0.8)

    proc = getattr(engine, "midi_process", None)
    if proc is None or proc.poll() is not None:
        err = ""
        if proc is not None and getattr(proc, "stderr", None) is not None:
            try:
                err = proc.stderr.read().strip()
            except Exception:
                pass
        raise RuntimeError("Récepteur amidi impossible à démarrer" + (f": {err}" if err else ""))

    engine.clear_queue()
    return port


def require_liveness(engine, port, label: str):
    r = engine.get_property(port, TEMPO_PROP, TEMPO_INDEX, timeout=1.5)
    if r.get("status") not in ("DATA", "EMPTY"):
        raise RuntimeError(
            f"CVP non joignable pendant {label}: Tempo={r.get('status')}"
        )
    return r


def recall(engine, port, msg, expected: int, label: str) -> None:
    engine.clear_queue()
    if not engine.send_sysex(port, msg):
        raise RuntimeError(f"Erreur envoi rappel {label}")

    seen = False
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            rx = engine.midi_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        if len(rx) >= 13 and rx[:11] == REG_NOTIFY and rx[11] == expected:
            seen = True
            break

    time.sleep(0.35)
    engine.clear_queue()

    if not seen:
        raise RuntimeError(f"Notification de rappel {label} non reçue")


def build_keys(zone: Zone, p0: int, p1: int):
    return [
        (p0,p1,p2,p3,idx)
        for p3 in zone.p3_values
        for p2 in P2_RANGE
        for idx in zone.indexes
    ]


def messages_for_keys(engine, keys) -> bytearray:
    blob = bytearray()
    for p0,p1,p2,p3,idx in keys:
        blob.extend(
            engine.HEADER
            + [0x01,0x00]
            + [p0,p1,p2,p3]
            + [idx,0x01,0x00,0xF7]
        )
    return blob


def parse_infos(engine, expected_keys, silence=0.8, hard=5.0):
    expected = set(expected_keys)
    out = {}
    started = time.monotonic()
    last = started

    while True:
        now_mono = time.monotonic()
        if now_mono - started >= hard:
            break
        if now_mono - last >= silence:
            break

        try:
            rx = engine.midi_queue.get(timeout=0.08)
        except queue.Empty:
            continue

        if not (
            len(rx) >= 18
            and rx[:7] == engine.HEADER
            and rx[7:9] == [0x00,0x00]
        ):
            continue

        kt = (rx[9],rx[10],rx[11],rx[12],rx[13])
        if kt not in expected:
            continue

        length = (rx[16] << 7) | rx[17]
        data = tuple(rx[18:18 + length])
        out[kt] = ("EMPTY", tuple()) if length == 0 else ("DATA", data)
        last = time.monotonic()

    return out


def query_keys(engine, port, tmp_path: Path, keys, label: str):
    if not keys:
        return {}

    tmp_path.write_bytes(messages_for_keys(engine, keys))
    engine.clear_queue()

    r = subprocess.run(
        ["amidi","-p",port,"-s",str(tmp_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"amidi a échoué pendant {label}: {r.stderr.strip()}")

    return parse_infos(engine, keys)


def block_done(conn, zone: Zone, p0: int, p1: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM blocks WHERE zone=? AND p0=? AND p1=?",
        (zone.name,p0,p1),
    ).fetchone()
    return row is not None


def save_block_and_candidates(conn, zone, p0, p1, keys, a_found, b_found, elapsed):
    diffs = []
    for kt in keys:
        a = a_found.get(kt)
        b = b_found.get(kt)
        if a == b:
            continue
        a_status,a_data = state_to_db(a)
        b_status,b_data = state_to_db(b)
        diffs.append((*kt,zone.name,a_status,a_data,b_status,b_data))

    with conn:
        if diffs:
            conn.executemany(
                "INSERT OR REPLACE INTO candidates "
                "(p0,p1,p2,p3,idx,zone,a_status,a_data,b_status,b_data) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                diffs,
            )
        conn.execute(
            "INSERT OR REPLACE INTO blocks "
            "(zone,p0,p1,key_count,a_count,b_count,diff_count,completed_at,elapsed_seconds) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                zone.name,p0,p1,len(keys),len(a_found),len(b_found),len(diffs),
                now_iso(),float(elapsed),
            ),
        )

    return len(diffs)


def campaign_elapsed_hours(conn) -> float:
    started = get_meta(conn, "campaign_started_at")
    if not started:
        started = now_iso()
        with conn:
            set_meta(conn, "campaign_started_at", started)
        return 0.0
    try:
        dt = datetime.fromisoformat(started)
        return (datetime.now() - dt).total_seconds() / 3600.0
    except Exception:
        return 0.0


def sweep(engine, port, tmp_path: Path, conn, max_hours: float):
    total_blocks = sum(len(z.p0_values) * len(z.p1_values) for z in ZONES)
    completed_before = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    print(f"Blocs déjà terminés : {completed_before}/{total_blocks}", flush=True)

    stop_for_budget = False

    for zone in sorted(ZONES, key=lambda z: z.priority):
        zone_total = len(zone.p0_values) * len(zone.p1_values)
        zone_done = conn.execute(
            "SELECT COUNT(*) FROM blocks WHERE zone=?", (zone.name,)
        ).fetchone()[0]
        print("\n======================================================", flush=True)
        print(f"ZONE {zone.priority} - {zone.name}", flush=True)
        print(f"Blocs : {zone_done}/{zone_total} déjà faits", flush=True)
        print(
            f"p3={','.join(f'{x:02X}' for x in zone.p3_values)} ; "
            f"indexes={zone.indexes[0]:02X}..{zone.indexes[-1]:02X} "
            f"({len(zone.indexes)} valeurs)",
            flush=True,
        )
        print("======================================================", flush=True)

        for p0 in zone.p0_values:
            for p1 in zone.p1_values:
                if block_done(conn, zone, p0, p1):
                    continue

                elapsed_campaign = campaign_elapsed_hours(conn)
                if max_hours > 0 and elapsed_campaign >= max_hours:
                    print(
                        f"Budget atteint ({elapsed_campaign:.2f} h / {max_hours:.2f} h).",
                        flush=True,
                    )
                    stop_for_budget = True
                    break

                keys = build_keys(zone, p0, p1)
                block_label = f"{zone.name} {p0:02X}:{p1:02X}"
                start = time.monotonic()

                # A = REG5 / AI Full Keyboard
                recall(engine, port, REG5, 0x04, "REG5 / AI Full Keyboard")
                require_liveness(engine, port, block_label + " avant A")
                a_found = query_keys(engine, port, tmp_path, keys, block_label + " A")
                require_liveness(engine, port, block_label + " après A")

                # B = REG6 / AI Fingered
                recall(engine, port, REG6, 0x05, "REG6 / AI Fingered")
                require_liveness(engine, port, block_label + " avant B")
                b_found = query_keys(engine, port, tmp_path, keys, block_label + " B")
                require_liveness(engine, port, block_label + " après B")

                elapsed = time.monotonic() - start
                diff_count = save_block_and_candidates(
                    conn, zone, p0, p1, keys, a_found, b_found, elapsed
                )

                done_total = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
                cand_total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
                print(
                    f"[{done_total}/{total_blocks}] {block_label} ; "
                    f"keys={len(keys)} A={len(a_found)} B={len(b_found)} "
                    f"diff={diff_count} cand_total={cand_total} "
                    f"bloc={elapsed/60:.2f} min RSS={rss_mib():.0f} MiB",
                    flush=True,
                )

                del keys, a_found, b_found
                gc.collect()

            if stop_for_budget:
                break
        if stop_for_budget:
            break

    with conn:
        set_meta(conn, "sweep_stopped_for_budget", int(stop_for_budget))
        set_meta(conn, "sweep_last_finished_at", now_iso())

    return not stop_for_budget


def candidate_rows(conn, where="1=1"):
    return conn.execute(
        "SELECT p0,p1,p2,p3,idx,a_status,a_data,b_status,b_data "
        f"FROM candidates WHERE {where} ORDER BY p0,p1,p2,p3,idx"
    ).fetchall()


def validate_phase(engine, port, tmp_path, conn, which: str):
    if which == "A2":
        rows = candidate_rows(conn)
        recall(engine, port, REG5, 0x04, "REG5 / A2")
        target = "A"
    elif which == "B2":
        rows = candidate_rows(conn, "a2_ok=1")
        recall(engine, port, REG6, 0x05, "REG6 / B2")
        target = "B"
    elif which == "C":
        rows = candidate_rows(conn, "b2_ok=1")
        recall(engine, port, REG7, 0x06, "REG7 / contrôle Registration")
        target = "C"
    else:
        raise ValueError(which)

    require_liveness(engine, port, f"validation {which}")
    total = len(rows)
    print(f"\nValidation {which} : {total} clés", flush=True)

    processed = 0
    for offset in range(0, total, QUERY_BATCH):
        batch = rows[offset:offset + QUERY_BATCH]
        keys = [tuple(int(x) for x in row[:5]) for row in batch]
        found = query_keys(engine, port, tmp_path, keys, which)

        updates = []
        for row, kt in zip(batch, keys):
            a = state_from_db(row[5],row[6])
            b = state_from_db(row[7],row[8])
            cur = found.get(kt)
            status,data = state_to_db(cur)

            if target == "A":
                ok = int(cur == a)
                updates.append((status,data,ok,*kt))
            elif target == "B":
                ok = int(cur == b and b != a)
                exact = int(
                    ok
                    and a is not None and b is not None
                    and a[0] == "DATA" and b[0] == "DATA"
                    and a[1] == (0x0C,) and b[1] == (0x03,)
                )
                updates.append((status,data,ok,exact,*kt))
            else:
                mirror = int(
                    a is not None and b is not None and cur is not None
                    and a[0] == b[0] == cur[0] == "DATA"
                    and a[1] == (0x04,)
                    and b[1] == (0x05,)
                    and cur[1] == (0x06,)
                )
                updates.append((status,data,mirror,*kt))

        with conn:
            if target == "A":
                conn.executemany(
                    "UPDATE candidates SET a2_status=?,a2_data=?,a2_ok=? "
                    "WHERE p0=? AND p1=? AND p2=? AND p3=? AND idx=?",
                    updates,
                )
            elif target == "B":
                conn.executemany(
                    "UPDATE candidates SET b2_status=?,b2_data=?,b2_ok=?,exact_0c_03=? "
                    "WHERE p0=? AND p1=? AND p2=? AND p3=? AND idx=?",
                    updates,
                )
            else:
                conn.executemany(
                    "UPDATE candidates SET c_status=?,c_data=?,reg_mirror_040506=? "
                    "WHERE p0=? AND p1=? AND p2=? AND p3=? AND idx=?",
                    updates,
                )

        processed += len(batch)
        if processed % 6000 == 0 or processed == total:
            require_liveness(engine, port, f"validation {which} {processed}/{total}")
        print(f"  {which} {processed}/{total}", flush=True)

        del batch, keys, found, updates
        gc.collect()


def validate_candidates(engine, port, tmp_path, conn):
    total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    if total == 0:
        print("\nAucun candidat A/B à revalider.", flush=True)
        return

    # Reset validation columns so a resumed campaign always gets a fresh final verdict.
    with conn:
        conn.execute(
            "UPDATE candidates SET "
            "a2_status=NULL,a2_data=NULL,a2_ok=0," 
            "b2_status=NULL,b2_data=NULL,b2_ok=0," 
            "c_status=NULL,c_data=NULL,reg_mirror_040506=0,exact_0c_03=0"
        )

    validate_phase(engine, port, tmp_path, conn, "A2")
    validate_phase(engine, port, tmp_path, conn, "B2")
    validate_phase(engine, port, tmp_path, conn, "C")


def export_report(conn, report_path: Path, max_hours: float):
    blocks_total = sum(len(z.p0_values) * len(z.p1_values) for z in ZONES)
    blocks_done = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    keys_scanned = conn.execute("SELECT COALESCE(SUM(key_count),0) FROM blocks").fetchone()[0]
    a_responses = conn.execute("SELECT COALESCE(SUM(a_count),0) FROM blocks").fetchone()[0]
    b_responses = conn.execute("SELECT COALESCE(SUM(b_count),0) FROM blocks").fetchone()[0]
    ab = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    aba = conn.execute("SELECT COUNT(*) FROM candidates WHERE a2_ok=1").fetchone()[0]
    abab = conn.execute("SELECT COUNT(*) FROM candidates WHERE b2_ok=1").fetchone()[0]
    mirrors = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE b2_ok=1 AND reg_mirror_040506=1"
    ).fetchone()[0]
    exact = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE b2_ok=1 AND exact_0c_03=1"
    ).fetchone()[0]
    non_mirror = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE b2_ok=1 AND reg_mirror_040506=0"
    ).fetchone()[0]

    confirmed = []
    for row in conn.execute(
        "SELECT p0,p1,p2,p3,idx,zone,"
        "a_status,a_data,b_status,b_data,a2_status,a2_data,b2_status,b2_data,"
        "c_status,c_data,reg_mirror_040506,exact_0c_03 "
        "FROM candidates WHERE b2_ok=1 "
        "ORDER BY exact_0c_03 DESC,reg_mirror_040506 ASC,p0,p1,p2,p3,idx"
    ):
        kt = tuple(int(x) for x in row[:5])
        confirmed.append({
            "key": key_tuple_to_text(kt),
            "zone": row[5],
            "A_REG5_full": state_to_json(state_from_db(row[6],row[7])),
            "B_REG6_ai_fingered": state_to_json(state_from_db(row[8],row[9])),
            "A2_REG5": state_to_json(state_from_db(row[10],row[11])),
            "B2_REG6": state_to_json(state_from_db(row[12],row[13])),
            "C_REG7_control": state_to_json(state_from_db(row[14],row[15])),
            "registration_mirror_04_05_06": bool(row[16]),
            "exact_0C_03": bool(row[17]),
        })

    payload = {
        "generated_at": now_iso(),
        "scanner": "cvp_find_fingering_deep_weekend.py",
        "campaign_started_at": get_meta(conn, "campaign_started_at"),
        "max_hours": max_hours,
        "sweep_stopped_for_budget": bool(int(get_meta(conn, "sweep_stopped_for_budget", "0"))),
        "scope": [
            {
                "name": z.name,
                "p0": f"{z.p0_values[0]:02X}..{z.p0_values[-1]:02X}",
                "p1": f"{z.p1_values[0]:02X}..{z.p1_values[-1]:02X}",
                "p2": "00..7F",
                "p3": [f"{x:02X}" for x in z.p3_values],
                "indexes": f"{z.indexes[0]:02X}..{z.indexes[-1]:02X}",
                "indexes_count": len(z.indexes),
            }
            for z in ZONES
        ],
        "blocks": {"done": blocks_done, "planned": blocks_total},
        "unique_keys_scanned": int(keys_scanned),
        "get_requests_completed": int(keys_scanned) * 2,
        "responses": {"A": int(a_responses), "B": int(b_responses)},
        "candidates": {
            "AB": ab,
            "ABA": aba,
            "ABAB": abab,
            "registration_mirror_04_05_06": mirrors,
            "stable_non_mirror": non_mirror,
            "exact_0C_03": exact,
        },
        "confirmed": confirmed,
    }

    tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(report_path)

    print("\n======================================================", flush=True)
    print("RESULTAT DE CAMPAGNE", flush=True)
    print("======================================================", flush=True)
    print(f"Blocs             : {blocks_done}/{blocks_total}", flush=True)
    print(f"Clés uniques      : {keys_scanned}", flush=True)
    print(f"GET A+B           : {int(keys_scanned) * 2}", flush=True)
    print(f"Candidats A/B     : {ab}", flush=True)
    print(f"Confirmés A/B/A   : {aba}", flush=True)
    print(f"Confirmés A/B/A/B : {abab}", flush=True)
    print(f"Miroirs 04/05/06  : {mirrors}", flush=True)
    print(f"Stables non miroir: {non_mirror}", flush=True)
    print(f"Match exact 0C/03 : {exact}", flush=True)
    print("Rapport            :", report_path, flush=True)

    interesting = [x for x in confirmed if not x["registration_mirror_04_05_06"]]
    for item in interesting[:200]:
        marker = " <<< 0C->03 >>>" if item["exact_0C_03"] else ""
        print(
            f"{item['key']} [{item['zone']}] : "
            f"{item['A_REG5_full']} -> {item['B_REG6_ai_fingered']}{marker}",
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description="CVP-905 deep weekend Fingering GET scan")
    parser.add_argument("--root", type=Path, default=Path.home() / "CVP_access")
    parser.add_argument(
        "--max-hours", type=float, default=48.0,
        help="wall-clock budget across restarts; 0 disables the budget (default: 48)",
    )
    args = parser.parse_args()

    root = args.root
    engine_path = root / "docs" / "cvp_probe_readonly.py"
    db_path = root / "fingering_deep_weekend.sqlite3"
    report_path = root / "fingering_deep_weekend_report.json"
    tmp_path = Path("/tmp/cvp_fingering_deep_weekend.syx")

    print("CVP ACCESS - FINGERING DEEP WEEKEND SCAN", flush=True)
    print("Unknown CSP: GET only. REG5/REG6 comparisons + REG7 control.", flush=True)
    print("No unknown SET. SQLite checkpointing. Tempo liveness guard.", flush=True)

    conn = connect_db(db_path)
    with conn:
        set_meta(conn, "schema_version", 1)
        if get_meta(conn, "campaign_started_at") is None:
            set_meta(conn, "campaign_started_at", now_iso())

    engine = load_engine(engine_path)
    port = start_midi(engine)

    try:
        require_liveness(engine, port, "démarrage")
        sweep(engine, port, tmp_path, conn, args.max_hours)
        validate_candidates(engine, port, tmp_path, conn)
        export_report(conn, report_path, args.max_hours)
    finally:
        try:
            engine.send_sysex(port, REG5)
            print("\nEtat final restauré : REG5", flush=True)
        except Exception:
            pass
        try:
            engine.cleanup()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
