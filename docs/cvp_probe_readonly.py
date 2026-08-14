#!/usr/bin/env python3

"""
CVP-909 read-only protocol probe.

Objectif :
- interroger uniquement avec des GET Yamaha/CSP ;
- ne jamais envoyer de SET/RESET ;
- tester les propriétés connues de ConPianist sur les indexes logiques connus ;
- distinguer DATA / EMPTY / TIMEOUT ;
- produire un rapport Markdown + JSON ;
- permettre un scan profond 00..7F d'une propriété choisie.

IMPORTANT :
Ce script est volontairement en lecture seule.
"""

import argparse
import json
import queue
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

MIDI_NAME = "ProdipeMIDIlilo MIDI 1"

HEADER = [
    0xF0, 0x43, 0x73, 0x01,
    0x52, 0x25, 0x26
]

ACTION_GET = [0x01, 0x00]
ACTION_INFO = [0x00, 0x00]

midi_queue = queue.Queue()
midi_process = None


# ============================================================
# CANAUX / INDEXES CONNUS
# ============================================================

CHANNELS = {
    0x00: "Main",
    0x01: "Layer",
    0x02: "Left",

    0x10: "Song 1",
    0x11: "Song 2",
    0x12: "Song 3",
    0x13: "Song 4",
    0x14: "Song 5",
    0x15: "Song 6",
    0x16: "Song 7",
    0x17: "Song 8",
    0x18: "Song 9",
    0x19: "Song 10",
    0x1A: "Song 11",
    0x1B: "Song 12",
    0x1C: "Song 13",
    0x1D: "Song 14",
    0x1E: "Song 15",
    0x1F: "Song 16",

    0x40: "Mic",
    0x41: "AuxIn",
    0x44: "Wave",
    0x50: "MidiMaster",
    0x51: "Style",
}

ALL_CHANNEL_INDEXES = list(CHANNELS.keys())
SONG_INDEXES = list(range(0x10, 0x20))
MAIN_LAYER_LEFT = [0x00, 0x01, 0x02]


# ============================================================
# PROPRIETES CONPIANIST
# ============================================================

# type :
# - int       : valeur 7-bit concaténée
# - bool      : 0/1
# - text      : format texte Yamaha/CSP
# - position  : mesure/temps
# - raw       : hex
#
# project :
# - validated : déjà validé dans CVP Access sur au moins l'index ciblé
# - partial   : propriété validée, mais pas tous les indexes testés
# - unexplored: pas encore validé dans notre projet

PROPERTIES = {
    "piano_model": {
        "sig": [0x0F, 0x01, 0x18, 0x01],
        "indexes": [0x00],
        "type": "text",
        "project": "unexplored",
    },
    "firmware_version": {
        "sig": [0x0F, 0x01, 0x0B, 0x01],
        "indexes": [0x00],
        "type": "text",
        "project": "unexplored",
    },

    "guide": {
        "sig": [0x04, 0x03, 0x00, 0x01],
        "indexes": [0x00],
        "type": "bool",
        "project": "unexplored",
    },
    "guide_type": {
        "sig": [0x04, 0x03, 0x01, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "position": {
        "sig": [0x04, 0x00, 0x0A, 0x01],
        "indexes": [0x00],
        "type": "position",
        "project": "unexplored",
    },
    "song_length": {
        "sig": [0x04, 0x00, 0x1B, 0x01],
        "indexes": [0x00],
        "type": "position",
        "project": "unexplored",
    },
    "stream_lights": {
        "sig": [0x04, 0x02, 0x00, 0x01],
        "indexes": [0x00],
        "type": "bool",
        "project": "unexplored",
    },
    "stream_speed": {
        "sig": [0x04, 0x02, 0x02, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "play": {
        "sig": [0x04, 0x00, 0x05, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },

    # ConPianist contient une ambiguïté historique :
    # commentaire Part => backing 3, enum Part => backing 2.
    # On sonde volontairement 0,1,2,3.
    "part": {
        "sig": [0x04, 0x00, 0x0E, 0x01],
        "indexes": [0x00, 0x01, 0x02, 0x03],
        "type": "bool",
        "project": "unexplored",
    },
    "part_channel": {
        "sig": [0x04, 0x00, 0x0F, 0x01],
        "indexes": [0x00, 0x01, 0x02, 0x03],
        "type": "int",
        "project": "unexplored",
    },
    "part_auto": {
        "sig": [0x04, 0x00, 0x10, 0x01],
        "indexes": [0x00],
        "type": "bool",
        "project": "unexplored",
    },
    "song_name": {
        "sig": [0x04, 0x00, 0x01, 0x01],
        "indexes": [0x00],
        "type": "text",
        "project": "unexplored",
    },

    "volume": {
        "sig": [0x0C, 0x00, 0x00, 0x01],
        "indexes": ALL_CHANNEL_INDEXES,
        "type": "int",
        "project": "partial",
    },
    "pan": {
        "sig": [0x0C, 0x00, 0x03, 0x01],
        "indexes": [x for x in ALL_CHANNEL_INDEXES if x != 0x41],
        "type": "int",
        "project": "unexplored",
    },
    "reverb": {
        "sig": [0x0C, 0x00, 0x04, 0x01],
        "indexes": [x for x in ALL_CHANNEL_INDEXES if x != 0x41],
        "type": "int",
        "project": "unexplored",
    },
    "octave": {
        "sig": [0x0C, 0x00, 0x12, 0x01],
        "indexes": MAIN_LAYER_LEFT,
        "type": "int",
        "project": "unexplored",
    },

    "tempo": {
        "sig": [0x08, 0x00, 0x00, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "validated",
    },
    "transpose": {
        "sig": [0x0A, 0x00, 0x00, 0x01],
        "indexes": [0x02],
        "type": "int",
        "project": "validated",
    },

    "reverb_effect": {
        "sig": [0x0C, 0x01, 0x00, 0x01],
        "indexes": [0x00],
        "type": "raw",
        "project": "unexplored",
    },
    "loop": {
        "sig": [0x04, 0x00, 0x0D, 0x01],
        "indexes": [0x00],
        "type": "raw",
        "project": "unexplored",
    },

    "voice_preset": {
        "sig": [0x02, 0x00, 0x00, 0x01],
        "indexes": MAIN_LAYER_LEFT,
        "type": "text",
        "project": "unexplored",
    },
    "voice_midi": {
        "sig": [0x02, 0x00, 0x01, 0x01],
        "indexes": SONG_INDEXES,
        "type": "raw",
        "project": "unexplored",
    },

    "active": {
        "sig": [0x0C, 0x00, 0x01, 0x01],
        "indexes": [x for x in ALL_CHANNEL_INDEXES if x != 0x41],
        "type": "bool",
        "project": "partial",
    },
    "present": {
        "sig": [0x04, 0x01, 0x00, 0x01],
        "indexes": SONG_INDEXES,
        "type": "bool",
        "project": "unexplored",
    },

    "split_point": {
        "sig": [0x09, 0x00, 0x00, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },

    "lid_position": {
        "sig": [0x02, 0x02, 0x07, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "environment": {
        "sig": [0x02, 0x02, 0x03, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "brightness": {
        "sig": [0x0C, 0x00, 0x0B, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "touch_curve": {
        "sig": [0x00, 0x00, 0x00, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "fixed_curve": {
        "sig": [0x00, 0x00, 0x01, 0x01],
        "indexes": MAIN_LAYER_LEFT,
        "type": "bool",
        "project": "unexplored",
    },
    "fixed_velocity": {
        "sig": [0x00, 0x00, 0x02, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "master_tune": {
        "sig": [0x03, 0x00, 0x00, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "vrm": {
        "sig": [0x02, 0x02, 0x00, 0x01],
        "indexes": [0x00],
        "type": "bool",
        "project": "unexplored",
    },
    "damper_resonance": {
        "sig": [0x02, 0x02, 0x01, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "string_resonance": {
        "sig": [0x02, 0x02, 0x02, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
    "key_off_sampling": {
        "sig": [0x02, 0x02, 0x06, 0x01],
        "indexes": [0x00],
        "type": "int",
        "project": "unexplored",
    },
}


# ============================================================
# OUTILS MIDI
# ============================================================

def check_port_free():

    conflicts = []

    for pattern in ("cvp_access", "amidi"):
        result = subprocess.run(
            ["pgrep", "-af", pattern],
            capture_output=True,
            text=True
        )

        for line in result.stdout.splitlines():
            # pgrep peut parfois voir la commande parente ; on ne garde
            # que les lignes qui ressemblent à un vrai processus cible.
            if pattern == "cvp_access" and "python" in line:
                conflicts.append(line)
            elif pattern == "amidi" and "amidi" in line:
                conflicts.append(line)

    if conflicts:
        print("Port MIDI potentiellement occupé :")
        for line in conflicts:
            print("  ", line)

        print()
        print("Arrête CVP Access / amidi avant de lancer le probe.")
        return False

    return True


def find_midi_port():

    result = subprocess.run(
        ["amidi", "-l"],
        capture_output=True,
        text=True
    )

    for line in result.stdout.splitlines():

        if MIDI_NAME in line:

            match = re.search(
                r"(hw:\d+,\d+,\d+)",
                line
            )

            if match:
                return match.group(1)

    return None


def midi_receiver(port):

    global midi_process

    midi_process = subprocess.Popen(
        [
            "amidi",
            "-p", port,
            "-d"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )

    message = []
    hex_byte = ""

    while True:

        char = midi_process.stdout.read(1)

        if char == "":
            return

        if char not in "0123456789abcdefABCDEF":
            hex_byte = ""
            continue

        hex_byte += char

        if len(hex_byte) < 2:
            continue

        value = int(hex_byte, 16)
        hex_byte = ""

        if value == 0xF0:
            message = [0xF0]
            continue

        if not message:
            continue

        message.append(value)

        if value == 0xF7:
            midi_queue.put(message.copy())
            message = []


def clear_queue():

    while True:
        try:
            midi_queue.get_nowait()
        except queue.Empty:
            break


def send_sysex(port, message):

    text = " ".join(
        f"{x:02X}"
        for x in message
    )

    result = subprocess.run(
        [
            "amidi",
            "-p", port,
            "-S", text
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return result.returncode == 0


def get_property(port, prop, index, timeout=0.30):

    clear_queue()

    message = (
        HEADER
        + ACTION_GET
        + prop
        + [index, 0x01, 0x00]
        + [0xF7]
    )

    if not send_sysex(port, message):
        return {
            "status": "SEND_ERROR",
            "data": None,
            "raw_response": None,
        }

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        remaining = deadline - time.monotonic()

        try:
            response = midi_queue.get(timeout=remaining)

        except queue.Empty:
            return {
                "status": "TIMEOUT",
                "data": None,
                "raw_response": None,
            }

        if len(response) < 18:
            continue

        if response[:7] != HEADER:
            continue

        if response[7:9] != ACTION_INFO:
            continue

        if response[9:13] != prop:
            continue

        if response[13] != index:
            continue

        # Taille CSP = deux octets 7-bit.
        length = (
            (response[16] << 7)
            + response[17]
        )

        data = response[
            18:18 + length
        ]

        raw = " ".join(
            f"{x:02X}"
            for x in response
        )

        if length == 0:
            return {
                "status": "EMPTY",
                "data": [],
                "raw_response": raw,
            }

        if len(data) != length:
            return {
                "status": "MALFORMED",
                "data": data,
                "raw_response": raw,
            }

        return {
            "status": "DATA",
            "data": data,
            "raw_response": raw,
        }

    return {
        "status": "TIMEOUT",
        "data": None,
        "raw_response": None,
    }


# ============================================================
# DECODAGE
# ============================================================

def decode_int(data):

    value = 0

    for byte in data:
        value = (value << 7) | byte

    return value


def decode_position(data):

    if len(data) != 4:
        return None

    measure = (data[0] << 7) | data[1]
    beat = (data[2] << 7) | data[3]

    return {
        "measure": measure,
        "beat": beat,
    }


def decode_text(data):

    # Format utilisé par ConPianist :
    # 2 octets de taille 7-bit, puis groupes [highbits + 7 chars].
    if len(data) < 2:
        return None

    text_size = (data[0] << 7) | data[1]

    payload = data[2:]

    if text_size == 0:
        return ""

    if len(payload) < text_size:
        return None

    payload = payload[:text_size]

    out = bytearray()

    pos = 0

    while pos < len(payload):

        highbits = payload[pos]
        pos += 1

        remaining = len(payload) - pos
        chunk_len = min(7, remaining)

        for i in range(chunk_len):

            ch = payload[pos + i]

            bit = (
                highbits
                >> (chunk_len - i - 1)
            ) & 1

            if bit:
                ch |= 0x80

            out.append(ch)

        pos += chunk_len

    try:
        return out.decode("utf-8").rstrip("\x00")
    except UnicodeDecodeError:
        return out.decode("latin-1", errors="replace").rstrip("\x00")


def decoded_value(prop_type, data):

    if data is None:
        return None

    if prop_type == "bool" and len(data) >= 1:
        return bool(decode_int(data))

    if prop_type == "int":
        return decode_int(data)

    if prop_type == "position":
        return decode_position(data)

    if prop_type == "text":
        return decode_text(data)

    return " ".join(
        f"{x:02X}"
        for x in data
    )


def index_label(index):

    return CHANNELS.get(
        index,
        f"index 0x{index:02X}"
    )


# ============================================================
# AUDIT
# ============================================================

def probe_one(port, name, spec, index, timeout):

    result = get_property(
        port,
        spec["sig"],
        index,
        timeout=timeout
    )

    data = result["data"]

    record = {
        "property": name,
        "signature": " ".join(
            f"{x:02X}"
            for x in spec["sig"]
        ),
        "index": index,
        "index_hex": f"{index:02X}",
        "index_label": index_label(index),
        "project_status": spec["project"],
        "response_status": result["status"],
        "data_hex": (
            None
            if data is None
            else " ".join(
                f"{x:02X}"
                for x in data
            )
        ),
        "decoded": (
            decoded_value(
                spec["type"],
                data
            )
            if result["status"] == "DATA"
            else None
        ),
        "raw_response": result["raw_response"],
    }

    return record


def print_record(record):

    status = record["response_status"]

    if status == "DATA":

        decoded = record["decoded"]

        print(
            f"[DATA]  {record['property']:<20} "
            f"{record['signature']}  "
            f"idx {record['index_hex']} "
            f"({record['index_label']})"
        )

        print(
            f"        HEX: {record['data_hex']}"
        )

        print(
            f"        DEC: {decoded}"
        )

    elif status == "EMPTY":

        print(
            f"[EMPTY] {record['property']:<20} "
            f"{record['signature']}  "
            f"idx {record['index_hex']} "
            f"({record['index_label']})"
        )


def run_audit(port, timeout):

    records = []

    total = sum(
        len(spec["indexes"])
        for spec in PROPERTIES.values()
    )

    print()
    print("AUDIT READ-ONLY CVP-909")
    print("=======================")
    print(
        f"{total} GET planifiés. "
        "Aucun SET / RESET ne sera envoyé."
    )
    print()

    current = 0

    for name, spec in PROPERTIES.items():

        for index in spec["indexes"]:

            current += 1

            record = probe_one(
                port,
                name,
                spec,
                index,
                timeout
            )

            records.append(record)

            if record["response_status"] in (
                "DATA",
                "EMPTY"
            ):
                print_record(record)

            if current % 20 == 0:
                print(
                    f"... {current}/{total}"
                )

            time.sleep(0.015)

    return records


def run_deep(port, property_name, timeout):

    if property_name not in PROPERTIES:
        print(
            "Propriété inconnue :",
            property_name
        )
        print(
            "Disponibles :",
            ", ".join(sorted(PROPERTIES))
        )
        raise SystemExit(2)

    spec = PROPERTIES[property_name]

    records = []

    print()
    print(
        f"SCAN PROFOND : {property_name}"
    )
    print("============================")
    print(
        "Indexes 00 -> 7F, GET uniquement."
    )
    print()

    for index in range(0x80):

        record = probe_one(
            port,
            property_name,
            spec,
            index,
            timeout
        )

        records.append(record)

        if record["response_status"] in (
            "DATA",
            "EMPTY"
        ):
            print_record(record)

        time.sleep(0.015)

    return records


# ============================================================
# RAPPORTS
# ============================================================

def summarize(records):

    counts = {}

    for record in records:

        status = record["response_status"]

        counts[status] = (
            counts.get(status, 0)
            + 1
        )

    return counts


def markdown_value(value):

    if isinstance(value, dict):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return str(value)


def write_reports(records, prefix):

    json_path = Path(
        f"{prefix}.json"
    )

    md_path = Path(
        f"{prefix}.md"
    )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "midi_name": MIDI_NAME,
        "read_only": True,
        "summary": summarize(records),
        "records": records,
    }

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    lines = []

    lines.append(
        "# CVP-909 read-only protocol probe"
    )
    lines.append("")
    lines.append(
        f"Generated: `{payload['generated_at']}`"
    )
    lines.append("")
    lines.append(
        "**Mode:** GET uniquement — aucun SET / RESET."
    )
    lines.append("")

    counts = payload["summary"]

    lines.append("## Résumé")
    lines.append("")

    for status in sorted(counts):
        lines.append(
            f"- {status}: {counts[status]}"
        )

    lines.append("")
    lines.append("## Réponses avec données")
    lines.append("")
    lines.append(
        "| Propriété | Signature | Index | Canal/usage | Projet | HEX | Décodé |"
    )
    lines.append(
        "|---|---|---:|---|---|---|---|"
    )

    for record in records:

        if record["response_status"] != "DATA":
            continue

        lines.append(
            "| "
            + " | ".join(
                [
                    record["property"],
                    f"`{record['signature']}`",
                    f"`0x{record['index_hex']}`",
                    record["index_label"],
                    record["project_status"],
                    f"`{record['data_hex']}`",
                    markdown_value(record["decoded"]).replace("|", "\\|"),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Réponses vides")
    lines.append("")
    lines.append(
        "Une réponse `EMPTY` n'est **pas** considérée comme validation de propriété."
    )
    lines.append("")

    for record in records:

        if record["response_status"] == "EMPTY":
            lines.append(
                f"- `{record['property']}` "
                f"`{record['signature']}` "
                f"index `0x{record['index_hex']}` "
                f"({record['index_label']})"
            )

    md_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    return json_path, md_path


# ============================================================
# CLEANUP
# ============================================================

def cleanup():

    global midi_process

    if (
        midi_process is not None
        and midi_process.poll() is None
    ):

        midi_process.terminate()

        try:
            midi_process.wait(
                timeout=1
            )

        except subprocess.TimeoutExpired:
            midi_process.kill()


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Audit read-only des propriétés Yamaha/CSP "
            "sur CVP-909."
        )
    )

    parser.add_argument(
        "--deep",
        metavar="PROPERTY",
        help=(
            "Scanner les indexes 00..7F "
            "pour une propriété connue."
        )
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=0.30,
        help="Timeout par GET (défaut: 0.30 s)."
    )

    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Préfixe des rapports sans extension. "
            "Défaut: cvp_probe_YYYYMMDD_HHMMSS"
        )
    )

    args = parser.parse_args()

    if not check_port_free():
        raise SystemExit(1)

    port = find_midi_port()

    if port is None:
        print(
            "Interface Prodipe MIDI introuvable."
        )
        raise SystemExit(1)

    print(
        "MIDI :",
        port,
        "-",
        MIDI_NAME
    )

    thread = threading.Thread(
        target=midi_receiver,
        args=(port,),
        daemon=True
    )

    thread.start()

    time.sleep(0.35)

    try:

        if args.deep:
            records = run_deep(
                port,
                args.deep,
                args.timeout
            )
        else:
            records = run_audit(
                port,
                args.timeout
            )

        prefix = (
            args.output
            if args.output
            else datetime.now().strftime(
                "cvp_probe_%Y%m%d_%H%M%S"
            )
        )

        json_path, md_path = write_reports(
            records,
            prefix
        )

        counts = summarize(records)

        print()
        print("RÉSUMÉ")
        print("======")

        for status in sorted(counts):
            print(
                f"{status}: {counts[status]}"
            )

        print()
        print(
            "Rapport JSON :",
            json_path
        )
        print(
            "Rapport Markdown :",
            md_path
        )

        print()
        print(
            "Les réponses DATA sont des candidats "
            "à valider fonctionnellement."
        )

    except KeyboardInterrupt:
        print()
        print("Interrompu.")

    finally:
        cleanup()


if __name__ == "__main__":
    main()
