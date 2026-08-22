#!/usr/bin/env python3
"""
CVP Access - Fingering Type GET scan 20..7F - V2 SQLite

- Unknown CSP commands: GET only.
- Only validated REG5/REG6 Registration recalls are sent.
- Baseline is stored in SQLite, not retained in RAM.
- Can stream-import the large V1 JSON without json.loads() on the whole file.
- Resume-safe for baseline, B1, A2 and B2 phases.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import os
import queue
import re
import resource
import sqlite3
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

FIRST_RANGE = range(0x00, 0x10)
SECOND_RANGE = range(0x00, 0x10)
THIRD_RANGE = range(0x00, 0x80)
INDEX_RANGE = range(0x20, 0x80)
GETS_PER_BLOCK = len(THIRD_RANGE) * len(INDEX_RANGE)  # 12288
QUERY_BATCH = 1500

REG5 = [0xF0,0x43,0x73,0x01,0x52,0x25,0x11,0x00,0x02,0x00,0x04,0xF7]
REG6 = [0xF0,0x43,0x73,0x01,0x52,0x25,0x11,0x00,0x02,0x00,0x05,0xF7]
REG_NOTIFY = [0xF0,0x43,0x73,0x01,0x52,0x25,0x00,0x01,0x01,0x00,0x01]

KEY_RE = re.compile(
    r"^([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2}) "
    r"([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2})\|([0-9A-Fa-f]{2})$"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS baseline (
    p0 INTEGER NOT NULL,
    p1 INTEGER NOT NULL,
    p2 INTEGER NOT NULL,
    p3 INTEGER NOT NULL,
    idx INTEGER NOT NULL,
    status TEXT NOT NULL,
    data BLOB NOT NULL,
    PRIMARY KEY (p0,p1,p2,p3,idx)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS blocks (
    block_id TEXT PRIMARY KEY,
    p0 INTEGER NOT NULL,
    p1 INTEGER NOT NULL,
    response_count INTEGER NOT NULL,
    completed_at TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    p0 INTEGER NOT NULL,
    p1 INTEGER NOT NULL,
    p2 INTEGER NOT NULL,
    p3 INTEGER NOT NULL,
    idx INTEGER NOT NULL,

    a_status TEXT NOT NULL,
    a_data BLOB NOT NULL,
    b_status TEXT NOT NULL,
    b_data BLOB NOT NULL,

    a2_done INTEGER NOT NULL DEFAULT 0,
    a2_status TEXT,
    a2_data BLOB,
    a2_ok INTEGER NOT NULL DEFAULT 0,

    b2_done INTEGER NOT NULL DEFAULT 0,
    b2_status TEXT,
    b2_data BLOB,
    b2_ok INTEGER NOT NULL DEFAULT 0,

    exact_0c_03 INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (p0,p1,p2,p3,idx)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS progress (
    phase TEXT PRIMARY KEY,
    p0 INTEGER,
    p1 INTEGER,
    p2 INTEGER,
    p3 INTEGER,
    idx INTEGER,
    updated_at TEXT NOT NULL
);
"""


def now():
    return datetime.now().isoformat()


def rss_mib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def hx(data):
    return " ".join(f"{b:02X}" for b in data)


def key_of(prop, index):
    return f"{hx(prop)}|{index:02X}"


def tuple_from_key(key):
    m = KEY_RE.match(key)
    if not m:
        raise ValueError(f"Clé CSP invalide: {key!r}")
    return tuple(int(x, 16) for x in m.groups())


def key_from_tuple(t):
    p0, p1, p2, p3, idx = t
    return f"{p0:02X} {p1:02X} {p2:02X} {p3:02X}|{idx:02X}"


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


def connect_db(path, migration=False):
    conn = sqlite3.connect(path)
    if migration:
        # Temporary import DB: disposable until atomic rename.
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA locking_mode=EXCLUSIVE")
    else:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA wal_autocheckpoint=1000")
        conn.execute("PRAGMA journal_size_limit=67108864")
    conn.execute("PRAGMA cache_size=-8192")
    conn.execute("PRAGMA temp_store=FILE")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA)
    return conn


def set_meta(conn, key, value):
    conn.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def get_meta(conn, key, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return default if row is None else row[0]


def set_progress(conn, phase, cursor):
    vals = cursor if cursor is not None else (None, None, None, None, None)
    conn.execute(
        """
        INSERT INTO progress(phase,p0,p1,p2,p3,idx,updated_at)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(phase) DO UPDATE SET
          p0=excluded.p0,p1=excluded.p1,p2=excluded.p2,
          p3=excluded.p3,idx=excluded.idx,updated_at=excluded.updated_at
        """,
        (phase, *vals, now()),
    )


def get_progress(conn, phase):
    row = conn.execute(
        "SELECT p0,p1,p2,p3,idx FROM progress WHERE phase=?",
        (phase,),
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return tuple(int(x) for x in row)


# ----------------------------------------------------------------------
# Streaming migration from V1 JSON
# ----------------------------------------------------------------------

def iter_legacy_completed_blocks(path):
    in_section = False
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not in_section:
                if stripped.startswith('"completed_blocks"') and "[" in stripped:
                    in_section = True
                continue
            if stripped.startswith("]"):
                return
            token = stripped.rstrip(",")
            if not token:
                continue
            try:
                value = json.loads(token)
            except json.JSONDecodeError:
                continue
            if isinstance(value, str) and re.fullmatch(
                r"[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}", value
            ):
                yield value.upper()


def iter_legacy_baseline(path):
    """
    Stream top-level baseline_A produced by json.dumps(..., indent=2).

    Keeps only one baseline state object in memory.
    """
    in_section = False
    current_key = None
    value_lines = []
    brace_depth = 0
    entry_re = re.compile(r'^\s{4}("(?:[^"\\]|\\.)+")\s*:\s*(\{.*)$')

    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if not in_section:
                if re.match(r'^\s{2}"baseline_A"\s*:\s*\{\s*$', line):
                    in_section = True
                continue

            if current_key is None:
                if line.startswith("  }"):
                    return
                m = entry_re.match(line)
                if not m:
                    continue
                current_key = json.loads(m.group(1))
                first = m.group(2)
                value_lines = [first]
                brace_depth = first.count("{") - first.count("}")
            else:
                value_lines.append(line)
                brace_depth += line.count("{") - line.count("}")

            if current_key is not None and brace_depth == 0:
                raw = "".join(value_lines).strip().rstrip(",")
                yield current_key, json.loads(raw)
                current_key = None
                value_lines = []


def migrate_legacy(legacy, db):
    legacy = Path(legacy)
    db = Path(db)

    if db.exists():
        return
    if not legacy.is_file():
        conn = connect_db(db)
        set_meta(conn, "schema_version", 2)
        set_meta(conn, "phase", "baseline")
        conn.commit()
        conn.close()
        return

    tmpdb = Path(str(db) + ".importing")
    for p in (tmpdb, Path(str(tmpdb) + "-wal"), Path(str(tmpdb) + "-shm")):
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    print("\n======================================================", flush=True)
    print("MIGRATION V1 JSON -> SQLITE", flush=True)
    print("======================================================", flush=True)
    print("Source :", legacy, flush=True)
    print("Le JSON source reste intact.", flush=True)

    conn = connect_db(tmpdb, migration=True)
    imported = 0
    batch = []

    try:
        for key, obj in iter_legacy_baseline(legacy):
            p0, p1, p2, p3, idx = tuple_from_key(key)
            status = obj["status"]
            data = bytes(obj.get("data", []))
            batch.append((p0,p1,p2,p3,idx,status,data))

            if len(batch) >= 5000:
                conn.executemany(
                    "INSERT OR REPLACE INTO baseline "
                    "(p0,p1,p2,p3,idx,status,data) VALUES(?,?,?,?,?,?,?)",
                    batch,
                )
                conn.commit()
                imported += len(batch)
                batch.clear()
                if imported % 100000 < 5000:
                    print(
                        f"  {imported:,} réponses importées ; "
                        f"RSS max={rss_mib():.0f} MiB",
                        flush=True,
                    )

        if batch:
            conn.executemany(
                "INSERT OR REPLACE INTO baseline "
                "(p0,p1,p2,p3,idx,status,data) VALUES(?,?,?,?,?,?,?)",
                batch,
            )
            conn.commit()
            imported += len(batch)
            batch.clear()

        completed = list(iter_legacy_completed_blocks(legacy))
        accepted = 0
        rejected = []

        for block_id in completed:
            p0 = int(block_id[:2], 16)
            p1 = int(block_id[3:5], 16)
            count = conn.execute(
                "SELECT COUNT(*) FROM baseline WHERE p0=? AND p1=?",
                (p0,p1),
            ).fetchone()[0]

            # OOM-era V1 could mark a block complete after capturing no replies.
            # Reject only zero-response legacy blocks; V2 can later legitimately
            # mark a true zero-response block complete after rescanning it.
            if count == 0:
                rejected.append(block_id)
                continue

            conn.execute(
                "INSERT OR REPLACE INTO blocks "
                "(block_id,p0,p1,response_count,completed_at,source) "
                "VALUES(?,?,?,?,?,?)",
                (block_id,p0,p1,int(count),now(),"legacy-json"),
            )
            accepted += 1

        set_meta(conn, "schema_version", 2)
        set_meta(conn, "phase", "baseline")
        set_meta(conn, "legacy_source", legacy)
        set_meta(conn, "legacy_source_size", legacy.stat().st_size)
        set_meta(conn, "legacy_imported_at", now())
        set_meta(conn, "baseline_count", imported)
        conn.commit()

        print(f"Migration : {imported:,} réponses baseline.", flush=True)
        print(f"Blocs repris : {accepted}/{len(completed)}", flush=True)
        if rejected:
            print(
                "Blocs legacy sans réponse -> rescannés : "
                + ", ".join(rejected),
                flush=True,
            )
    finally:
        conn.close()

    os.replace(tmpdb, db)
    print("Base SQLite prête :", db, flush=True)


# ----------------------------------------------------------------------
# MIDI
# ----------------------------------------------------------------------

def load_engine(engine_path):
    spec = importlib.util.spec_from_file_location("cvp_probe_engine", engine_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Impossible de charger {engine_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def start_midi(engine):
    port = engine.find_midi_port()
    if not port:
        raise SystemExit("Interface Prodipe introuvable")
    print("MIDI :", port, flush=True)
    t = threading.Thread(
        target=engine.midi_receiver, args=(port,), daemon=True
    )
    t.start()
    time.sleep(0.6)
    engine.clear_queue()
    return port


def recall(engine, port, msg, expected, label):
    engine.clear_queue()
    print(f"\nRappel {label}...", flush=True)
    if not engine.send_sysex(port, msg):
        raise RuntimeError("Erreur rappel Registration")

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
    print(
        "Notification Registration :",
        "OUI" if seen else "non vue",
        flush=True,
    )


def parse_infos(engine, expected=None, first=None, second=None,
                silence=0.7, hard=3.0):
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
            and rx[7:9] == [0x00, 0x00]
        ):
            continue

        prop = tuple(rx[9:13])
        idx = rx[13]

        if first is not None and prop[0] != first:
            continue
        if second is not None and prop[1] != second:
            continue
        if not (0x20 <= idx <= 0x7F):
            continue

        key = key_of(prop, idx)
        if expected is not None and key not in expected:
            continue

        length = (rx[16] << 7) | rx[17]
        data = tuple(rx[18:18 + length])
        out[key] = ("EMPTY", tuple()) if length == 0 else ("DATA", data)
        last = time.monotonic()

    return out


def make_block(engine, tmp_path, first, second):
    blob = bytearray()
    for third in THIRD_RANGE:
        prop = [first, second, third, 0x01]
        for idx in INDEX_RANGE:
            blob.extend(
                engine.HEADER
                + [0x01,0x00]
                + prop
                + [idx,0x01,0x00,0xF7]
            )
    Path(tmp_path).write_bytes(blob)
    return len(blob)


def messages_for_keys(engine, keys):
    blob = bytearray()
    for key in keys:
        p0,p1,p2,p3,idx = tuple_from_key(key)
        blob.extend(
            engine.HEADER
            + [0x01,0x00]
            + [p0,p1,p2,p3]
            + [idx,0x01,0x00,0xF7]
        )
    return blob


def query_keys(engine, port, tmp_path, keys, label):
    if not keys:
        return {}
    expected = set(keys)
    Path(tmp_path).write_bytes(messages_for_keys(engine, keys))
    engine.clear_queue()

    r = subprocess.run(
        ["amidi","-p",port,"-s",str(tmp_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"amidi a échoué pendant {label}: {r.stderr.strip()}"
        )

    return parse_infos(
        engine, expected=expected, silence=0.8, hard=4.0
    )


# ----------------------------------------------------------------------
# PHASE 1 baseline A
# ----------------------------------------------------------------------

def baseline_scan(engine, port, tmp_path, conn):
    done = {
        row[0]
        for row in conn.execute("SELECT block_id FROM blocks")
    }
    total = conn.execute("SELECT COUNT(*) FROM baseline").fetchone()[0]

    print("\n======================================================", flush=True)
    print("PHASE 1 - BASELINE REG5 / INDEXES 20..7F", flush=True)
    print("======================================================", flush=True)
    print("256 blocs ; SQLite ; RAM bornée.", flush=True)

    block_no = 0
    for first in FIRST_RANGE:
        for second in SECOND_RANGE:
            block_no += 1
            block_id = f"{first:02X}:{second:02X}"

            if block_id in done:
                count = conn.execute(
                    "SELECT response_count FROM blocks WHERE block_id=?",
                    (block_id,),
                ).fetchone()[0]
                print(
                    f"[{block_no:3}/256] {block_id} déjà fait - skip "
                    f"({count} réponses)",
                    flush=True,
                )
                continue

            size = make_block(engine, tmp_path, first, second)
            engine.clear_queue()
            start = time.monotonic()

            print(
                f"[{block_no:3}/256] scan {block_id} "
                f"({size} octets, {GETS_PER_BLOCK} GET)...",
                flush=True,
            )

            r = subprocess.run(
                ["amidi","-p",port,"-s",str(tmp_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            if r.returncode != 0:
                raise RuntimeError(
                    f"amidi a échoué sur {block_id}: {r.stderr.strip()}"
                )

            found = parse_infos(
                engine, first=first, second=second,
                silence=0.8, hard=4.0
            )

            before = conn.execute(
                "SELECT COUNT(*) FROM baseline WHERE p0=? AND p1=?",
                (first,second),
            ).fetchone()[0]

            rows = []
            for key, state in found.items():
                p0,p1,p2,p3,idx = tuple_from_key(key)
                status,data = state_to_db(state)
                rows.append((p0,p1,p2,p3,idx,status,data))

            with conn:
                if rows:
                    conn.executemany(
                        "INSERT OR REPLACE INTO baseline "
                        "(p0,p1,p2,p3,idx,status,data) "
                        "VALUES(?,?,?,?,?,?,?)",
                        rows,
                    )
                after = conn.execute(
                    "SELECT COUNT(*) FROM baseline WHERE p0=? AND p1=?",
                    (first,second),
                ).fetchone()[0]
                conn.execute(
                    "INSERT OR REPLACE INTO blocks "
                    "(block_id,p0,p1,response_count,completed_at,source) "
                    "VALUES(?,?,?,?,?,?)",
                    (block_id,first,second,int(after),now(),"v2-scan"),
                )
                total += int(after) - int(before)
                set_meta(conn, "baseline_count", total)
                set_meta(conn, "phase", "baseline")

            elapsed = time.monotonic() - start
            print(
                f"    capturées={len(found)} ; nouvelles={after-before} ; "
                f"total={total} ; bloc={elapsed/60:.1f} min ; "
                f"RSS max={rss_mib():.0f} MiB",
                flush=True,
            )

            del found, rows
            gc.collect()

    with conn:
        set_meta(conn, "phase", "B1")


# ----------------------------------------------------------------------
# Streaming B1/A2/B2
# ----------------------------------------------------------------------

def baseline_rows_after(conn, cursor, limit):
    if cursor is None:
        return conn.execute(
            "SELECT p0,p1,p2,p3,idx,status,data FROM baseline "
            "ORDER BY p0,p1,p2,p3,idx LIMIT ?",
            (limit,),
        ).fetchall()
    return conn.execute(
        "SELECT p0,p1,p2,p3,idx,status,data FROM baseline "
        "WHERE (p0,p1,p2,p3,idx) > (?,?,?,?,?) "
        "ORDER BY p0,p1,p2,p3,idx LIMIT ?",
        (*cursor,limit),
    ).fetchall()


def phase_b1(engine, port, tmp_path, conn):
    print("\n======================================================", flush=True)
    print("PHASE 2 - B1 / REG6 AI Fingered", flush=True)
    print("======================================================", flush=True)

    cursor = get_progress(conn, "B1")
    processed_this_run = 0

    while True:
        rows = baseline_rows_after(conn, cursor, QUERY_BATCH)
        if not rows:
            break

        keys = [key_from_tuple(tuple(r[:5])) for r in rows]
        found = query_keys(engine, port, tmp_path, keys, "B1")
        inserts = []

        for row, key in zip(rows, keys):
            kt = tuple(int(x) for x in row[:5])
            a = state_from_db(row[5], row[6])
            b = found.get(key)
            if b != a:
                a_status,a_data = state_to_db(a)
                b_status,b_data = state_to_db(b)
                inserts.append((*kt,a_status,a_data,b_status,b_data))

        cursor = tuple(int(x) for x in rows[-1][:5])

        with conn:
            if inserts:
                conn.executemany(
                    "INSERT OR REPLACE INTO candidates "
                    "(p0,p1,p2,p3,idx,a_status,a_data,b_status,b_data) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    inserts,
                )
            set_progress(conn, "B1", cursor)
            set_meta(conn, "phase", "B1")

        processed_this_run += len(rows)
        cand = conn.execute(
            "SELECT COUNT(*) FROM candidates"
        ).fetchone()[0]
        print(
            f"  B1 +{processed_this_run} ; candidats={cand} ; "
            f"RSS max={rss_mib():.0f} MiB",
            flush=True,
        )

        del rows, keys, found, inserts
        gc.collect()

    with conn:
        set_meta(conn, "phase", "A2")

    print(
        "Candidats provisoires A/B :",
        conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
        flush=True,
    )


def get_candidate_ab(conn, kt):
    row = conn.execute(
        "SELECT a_status,a_data,b_status,b_data FROM candidates "
        "WHERE p0=? AND p1=? AND p2=? AND p3=? AND idx=?",
        kt,
    ).fetchone()
    return (
        state_from_db(row[0],row[1]),
        state_from_db(row[2],row[3]),
    )


def phase_a2(engine, port, tmp_path, conn):
    print("\n======================================================", flush=True)
    print("PHASE 3 - A2 / REG5", flush=True)
    print("======================================================", flush=True)

    processed = 0
    while True:
        rows = conn.execute(
            "SELECT p0,p1,p2,p3,idx FROM candidates "
            "WHERE a2_done=0 "
            "ORDER BY p0,p1,p2,p3,idx LIMIT ?",
            (QUERY_BATCH,),
        ).fetchall()
        if not rows:
            break

        keys = [key_from_tuple(tuple(r)) for r in rows]
        found = query_keys(engine, port, tmp_path, keys, "A2")
        updates = []

        for row,key in zip(rows,keys):
            kt = tuple(int(x) for x in row)
            a,_b = get_candidate_ab(conn, kt)
            a2 = found.get(key)
            status,data = state_to_db(a2)
            updates.append((status,data,1 if a2 == a else 0,*kt))

        with conn:
            conn.executemany(
                "UPDATE candidates SET "
                "a2_done=1,a2_status=?,a2_data=?,a2_ok=? "
                "WHERE p0=? AND p1=? AND p2=? AND p3=? AND idx=?",
                updates,
            )
            set_meta(conn, "phase", "A2")

        processed += len(rows)
        ok = conn.execute(
            "SELECT COUNT(*) FROM candidates WHERE a2_ok=1"
        ).fetchone()[0]
        print(
            f"  A2 +{processed} ; A/B/A confirmés={ok} ; "
            f"RSS max={rss_mib():.0f} MiB",
            flush=True,
        )

        del rows,keys,found,updates
        gc.collect()

    with conn:
        set_meta(conn, "phase", "B2")


def phase_b2(engine, port, tmp_path, conn):
    print("\n======================================================", flush=True)
    print("PHASE 4 - B2 / REG6", flush=True)
    print("======================================================", flush=True)

    processed = 0
    while True:
        rows = conn.execute(
            "SELECT p0,p1,p2,p3,idx FROM candidates "
            "WHERE a2_ok=1 AND b2_done=0 "
            "ORDER BY p0,p1,p2,p3,idx LIMIT ?",
            (QUERY_BATCH,),
        ).fetchall()
        if not rows:
            break

        keys = [key_from_tuple(tuple(r)) for r in rows]
        found = query_keys(engine, port, tmp_path, keys, "B2")
        updates = []

        for row,key in zip(rows,keys):
            kt = tuple(int(x) for x in row)
            a,b = get_candidate_ab(conn, kt)
            b2 = found.get(key)
            status,data = state_to_db(b2)
            confirmed = (b2 == b and b != a)
            exact = (
                confirmed
                and a is not None and b is not None
                and a[0] == "DATA" and b[0] == "DATA"
                and a[1] == (0x0C,) and b[1] == (0x03,)
            )
            updates.append(
                (status,data,1 if confirmed else 0,1 if exact else 0,*kt)
            )

        with conn:
            conn.executemany(
                "UPDATE candidates SET "
                "b2_done=1,b2_status=?,b2_data=?,b2_ok=?,exact_0c_03=? "
                "WHERE p0=? AND p1=? AND p2=? AND p3=? AND idx=?",
                updates,
            )
            set_meta(conn, "phase", "B2")

        processed += len(rows)
        confirmed_count = conn.execute(
            "SELECT COUNT(*) FROM candidates WHERE b2_ok=1"
        ).fetchone()[0]
        print(
            f"  B2 +{processed} ; A/B/A/B confirmés={confirmed_count} ; "
            f"RSS max={rss_mib():.0f} MiB",
            flush=True,
        )

        del rows,keys,found,updates
        gc.collect()

    with conn:
        set_meta(conn, "phase", "done")
        set_meta(conn, "finished_at", now())


def export_report(conn, final_report):
    baseline = conn.execute("SELECT COUNT(*) FROM baseline").fetchone()[0]
    blocks = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    ab = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    aba = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE a2_ok=1"
    ).fetchone()[0]
    abab = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE b2_ok=1"
    ).fetchone()[0]
    exact = conn.execute(
        "SELECT COUNT(*) FROM candidates "
        "WHERE b2_ok=1 AND exact_0c_03=1"
    ).fetchone()[0]

    confirmed = []
    for row in conn.execute(
        "SELECT p0,p1,p2,p3,idx,"
        "a_status,a_data,b_status,b_data,"
        "a2_status,a2_data,b2_status,b2_data,exact_0c_03 "
        "FROM candidates WHERE b2_ok=1 "
        "ORDER BY exact_0c_03 DESC,p0,p1,p2,p3,idx"
    ):
        kt = tuple(int(x) for x in row[:5])
        confirmed.append({
            "key": key_from_tuple(kt),
            "A_full": state_to_json(state_from_db(row[5],row[6])),
            "B_ai_fingered": state_to_json(state_from_db(row[7],row[8])),
            "A2_full": state_to_json(state_from_db(row[9],row[10])),
            "B2_ai_fingered": state_to_json(state_from_db(row[11],row[12])),
            "exact_0C_03": bool(row[13]),
        })

    payload = {
        "generated_at": now(),
        "scanner": "cvp_find_fingering_indexes_20_7f_v2.py",
        "scope": {
            "property": "00..0F 00..0F 00..7F 01",
            "indexes": "20..7F",
            "blocks": 256,
            "gets_per_block": GETS_PER_BLOCK,
        },
        "states": {
            "A": "REG5 / AI Full Keyboard",
            "B": "REG6 / AI Fingered",
        },
        "baseline_responses": baseline,
        "completed_blocks": blocks,
        "preliminary_candidates_AB": ab,
        "confirmed_ABA": aba,
        "confirmed_ABAB": abab,
        "exact_0C_03_count": exact,
        "confirmed": confirmed,
    }

    final_report = Path(final_report)
    tmp = final_report.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(payload,indent=2,ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(final_report)

    print("\n======================================================", flush=True)
    print("RESULTAT FINAL", flush=True)
    print("======================================================", flush=True)
    print("Réponses baseline :", baseline, flush=True)
    print("Blocs baseline    :", f"{blocks}/256", flush=True)
    print("Candidats A/B     :", ab, flush=True)
    print("Candidats A/B/A   :", aba, flush=True)
    print("Confirmés A/B/A/B :", abab, flush=True)
    print("Match exact 0C/03 :", exact, flush=True)
    print("Rapport compact   :", final_report, flush=True)

    for item in confirmed:
        marker = "  <<< MATCH 0C -> 03 >>>" if item["exact_0C_03"] else ""
        print(
            item["key"], ":", item["A_full"], "->",
            item["B_ai_fingered"], marker, flush=True
        )


def main():
    parser = argparse.ArgumentParser(
        description="CVP-905 Fingering broad GET scan - SQLite V2"
    )
    parser.add_argument(
        "--root", type=Path, default=Path.home() / "CVP_access"
    )
    parser.add_argument(
        "--migrate-only", action="store_true",
        help="import legacy JSON to SQLite and exit without MIDI"
    )
    args = parser.parse_args()

    root = args.root
    engine_path = root / "docs" / "cvp_probe_readonly.py"
    legacy = root / "fingering_idx20_7f_report.json"
    db = root / "fingering_idx20_7f.sqlite3"
    final_report = root / "fingering_idx20_7f_v2_report.json"
    tmp_path = Path("/tmp/cvp_idx20_7f_block_v2.syx")

    print("CVP ACCESS - FINGERING GET INDEXES 20..7F - V2 SQLITE")
    print("GET uniquement + rappels REG5/REG6 déjà validés.")
    print("Aucun SET CSP inconnu.")
    print("Stockage SQLite ; baseline non conservée en RAM.")

    migrate_legacy(legacy, db)

    if args.migrate_only:
        conn = connect_db(db)
        print(
            "Baseline SQLite :",
            conn.execute("SELECT COUNT(*) FROM baseline").fetchone()[0],
        )
        print(
            "Blocs repris    :",
            conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0],
        )
        conn.close()
        return

    conn = connect_db(db)
    set_meta(conn, "schema_version", 2)
    conn.commit()

    engine = load_engine(engine_path)
    port = start_midi(engine)

    try:
        phase = get_meta(conn, "phase", "baseline")

        if phase == "baseline":
            recall(engine, port, REG5, 0x04, "REG5 / AI Full Keyboard")
            baseline_scan(engine, port, tmp_path, conn)
            phase = get_meta(conn, "phase")

        if phase == "B1":
            recall(engine, port, REG6, 0x05, "REG6 / AI Fingered")
            phase_b1(engine, port, tmp_path, conn)
            phase = get_meta(conn, "phase")

        if phase == "A2":
            recall(engine, port, REG5, 0x04, "REG5 / AI Full Keyboard")
            phase_a2(engine, port, tmp_path, conn)
            phase = get_meta(conn, "phase")

        if phase == "B2":
            recall(engine, port, REG6, 0x05, "REG6 / AI Fingered")
            phase_b2(engine, port, tmp_path, conn)
            phase = get_meta(conn, "phase")

        if phase == "done":
            export_report(conn, final_report)

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
