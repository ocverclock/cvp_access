#!/usr/bin/env python3
"""
CVP Access - validation SET des propriétés Métronome

Candidats découverts par diff OFF -> ON :
    07 00 00 01 : 00       -> 01
    07 00 01 01 : 00 00    -> 00 01
    07 00 02 01 : 00       -> 01
    07 00 03 01 : 00       -> 01
    07 00 04 01 : 08 00    -> 08 01

Test uniquement à idx=00.

Pour chaque candidat :
    - vérifie l'état de départ ;
    - envoie uniquement la valeur ON déjà observée ;
    - relit les 5 propriétés ;
    - demande si le métronome s'est réellement activé ;
    - envoie uniquement la valeur OFF déjà observée ;
    - relit les 5 propriétés ;
    - demande si le métronome s'est réellement arrêté.

Aucune valeur inconnue n'est envoyée.

Rapport :
    metronome_set_validation.json
"""

from __future__ import annotations

import importlib.util
import json
import threading
import time
from datetime import datetime
from pathlib import Path


CORE_FILENAME = "cvp_access_v1.4.1.py"
INDEX = 0x00
REPORT = Path("metronome_set_validation.json")


CANDIDATES = [
    {
        "name": "07 00 00 01",
        "prop": [0x07, 0x00, 0x00, 0x01],
        "off": [0x00],
        "on":  [0x01],
    },
    {
        "name": "07 00 01 01",
        "prop": [0x07, 0x00, 0x01, 0x01],
        "off": [0x00, 0x00],
        "on":  [0x00, 0x01],
    },
    {
        "name": "07 00 02 01",
        "prop": [0x07, 0x00, 0x02, 0x01],
        "off": [0x00],
        "on":  [0x01],
    },
    {
        "name": "07 00 03 01",
        "prop": [0x07, 0x00, 0x03, 0x01],
        "off": [0x00],
        "on":  [0x01],
    },
    {
        "name": "07 00 04 01",
        "prop": [0x07, 0x00, 0x04, 0x01],
        "off": [0x08, 0x00],
        "on":  [0x08, 0x01],
    },
]


def bell():
    print("\a", end="", flush=True)


def load_core():
    path = Path(__file__).resolve().parent.parent / CORE_FILENAME

    if not path.is_file():
        # Permet aussi de lancer le script depuis la racine si besoin.
        alt = Path.cwd() / CORE_FILENAME
        if alt.is_file():
            path = alt
        else:
            raise SystemExit(
                f"ERREUR : {CORE_FILENAME} introuvable.\n"
                "Le script doit être dans ~/CVP_access/docs/ "
                "ou lancé depuis ~/CVP_access."
            )

    spec = importlib.util.spec_from_file_location(
        "cvp_core_metronome_test",
        path,
    )

    if spec is None or spec.loader is None:
        raise SystemExit(
            f"ERREUR : impossible de charger {path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hx(data):
    if data is None:
        return "AUCUNE RÉPONSE"

    return " ".join(
        f"{value:02X}"
        for value in data
    )


def set_property(core, port, prop, index, data):
    length = len(data)

    if length > 0x3FFF:
        raise ValueError("DATA trop longue")

    length_hi = (length >> 7) & 0x7F
    length_lo = length & 0x7F

    message = (
        core.HEADER
        + [0x01, 0x01]
        + prop
        + [index, 0x01, 0x00]
        + [length_hi, length_lo]
        + list(data)
        + [0xF7]
    )

    return core.send_sysex(
        port,
        message,
    )


def read_candidate(core, port, candidate):
    data = core.get_property(
        port,
        candidate["prop"],
        INDEX,
        timeout=0.5,
    )

    if data is None:
        return None

    return list(data)


def read_all(core, port):
    result = {}

    for candidate in CANDIDATES:
        result[candidate["name"]] = read_candidate(
            core,
            port,
            candidate,
        )
        time.sleep(0.03)

    return result


def print_state(title, state):
    print()
    print(title)

    for name, data in state.items():
        print(
            f"  {name} idx=00 -> {hx(data)}"
        )


def ask_yes_no(message):
    while True:
        bell()

        answer = input(
            message + " [o/n] : "
        ).strip().lower()

        if answer in ("o", "oui", "y", "yes"):
            return True

        if answer in ("n", "non", "no"):
            return False

        print("Réponds par o ou n.")


def main():
    print()
    print("CVP ACCESS - VALIDATION SET MÉTRONOME")
    print("=" * 72)
    print("5 propriétés candidates - idx=00")
    print("Valeurs SET limitées aux valeurs déjà observées OFF/ON.")
    print()

    core = load_core()

    port = core.find_midi_port()

    if port is None:
        raise SystemExit(
            "ERREUR : interface Prodipe MIDI introuvable."
        )

    print("MIDI :", port, "-", core.MIDI_NAME)

    receiver = threading.Thread(
        target=core.midi_receiver,
        args=(port,),
        daemon=True,
    )
    receiver.start()

    time.sleep(0.4)

    results = []

    try:
        bell()
        input(
            "\nMets d'abord le MÉTRONOME sur OFF manuellement, "
            "puis Entrée..."
        )

        initial = read_all(
            core,
            port,
        )

        print_state(
            "État initial :",
            initial,
        )

        print()
        print(
            "Le script va maintenant tester les 5 propriétés "
            "une par une."
        )

        for number, candidate in enumerate(
            CANDIDATES,
            1,
        ):
            print()
            print("=" * 72)
            print(
                f"TEST {number}/5 : {candidate['name']} idx=00"
            )
            print(
                "OFF attendu :",
                hx(candidate["off"]),
            )
            print(
                "ON attendu  :",
                hx(candidate["on"]),
            )
            print("=" * 72)

            # Toujours forcer l'état OFF connu avant le test.
            print(
                f"SET {candidate['name']} -> OFF "
                f"({hx(candidate['off'])})"
            )

            off_sent_pre = set_property(
                core,
                port,
                candidate["prop"],
                INDEX,
                candidate["off"],
            )

            time.sleep(0.25)

            before = read_all(
                core,
                port,
            )

            print_state(
                "Avant SET ON :",
                before,
            )

            bell()
            input(
                "\nAppuie sur Entrée pour envoyer le SET ON..."
            )

            on_sent = set_property(
                core,
                port,
                candidate["prop"],
                INDEX,
                candidate["on"],
            )

            time.sleep(0.35)

            after_on = read_all(
                core,
                port,
            )

            print_state(
                "Après SET ON :",
                after_on,
            )

            physical_on = ask_yes_no(
                "Le métronome est-il réellement ON ?"
            )

            print()
            print(
                f"SET {candidate['name']} -> OFF "
                f"({hx(candidate['off'])})"
            )

            off_sent = set_property(
                core,
                port,
                candidate["prop"],
                INDEX,
                candidate["off"],
            )

            time.sleep(0.35)

            after_off = read_all(
                core,
                port,
            )

            print_state(
                "Après SET OFF :",
                after_off,
            )

            physical_off = ask_yes_no(
                "Le métronome est-il réellement OFF ?"
            )

            results.append(
                {
                    "signature": candidate["name"],
                    "index": "00",
                    "off_value": hx(candidate["off"]),
                    "on_value": hx(candidate["on"]),
                    "set_off_before_ok": off_sent_pre,
                    "set_on_ok": on_sent,
                    "set_off_ok": off_sent,
                    "physical_on": physical_on,
                    "physical_off": physical_off,
                    "before": {
                        key: hx(value)
                        for key, value in before.items()
                    },
                    "after_on": {
                        key: hx(value)
                        for key, value in after_on.items()
                    },
                    "after_off": {
                        key: hx(value)
                        for key, value in after_off.items()
                    },
                }
            )

        validated = [
            item
            for item in results
            if item["physical_on"]
            and item["physical_off"]
        ]

        payload = {
            "generated_at":
                datetime.now().isoformat(),
            "model":
                "CVP-905",
            "firmware":
                "1.03",
            "results":
                results,
            "validated":
                [
                    item["signature"]
                    for item in validated
                ],
        }

        REPORT.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        print()
        print("=" * 72)
        print("RÉSUMÉ FINAL")
        print("=" * 72)

        if not validated:
            print(
                "Aucune des 5 propriétés n'a piloté "
                "le métronome ON puis OFF."
            )
        else:
            print(
                "PROPRIÉTÉS QUI PILOTENT RÉELLEMENT "
                "LE MÉTRONOME :"
            )

            for item in validated:
                print(
                    f"{item['signature']}|00 : "
                    f"OFF={item['off_value']} "
                    f"ON={item['on_value']}"
                )

        print()
        print("Rapport :", REPORT)
        bell()

    finally:
        core.cleanup()


if __name__ == "__main__":
    main()
