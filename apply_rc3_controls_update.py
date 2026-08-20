#!/usr/bin/env python3
'''
Applique le lot RC3 controls au checkout local CVP Access.

Modifie/remplace :
- cvp_access_v1.5.py
- cvp_song.py
- cvp_speech.py
- cvp_keyboard_map.py
- keyboard_RC3_example.toml
- CVP905_PROTOCOL_CHECKPOINT_RC3.md
- cvp_keyboard.py
- config/default.toml
- cvp_access_installer/tools/generate_configured_voices.py

Sauvegardes : *.bak-RC3-controls
Aucune commande MIDI n'est envoyée.
'''

from __future__ import annotations

import py_compile
import shutil
import sys
import tomllib
from pathlib import Path


BACKUP_SUFFIX = ".bak-RC3-controls"


def fail(message):
    raise SystemExit("ERREUR : " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        fail(
            f"{label}: motif attendu une fois, trouvé {count} fois"
        )
    return text.replace(old, new, 1)


def backup(path):
    target = path.with_name(
        path.name + BACKUP_SUFFIX
    )
    if not target.exists():
        shutil.copy2(path, target)
    return target


def write_text(path, text):
    backup(path)
    path.write_text(
        text,
        encoding="utf-8",
    )


def copy_complete(src, dst):
    if not src.is_file():
        fail(f"fichier du lot absent : {src}")

    if dst.exists():
        backup(dst)

    shutil.copy2(src, dst)


def patch_keyboard(path):
    text = path.read_text(
        encoding="utf-8"
    )

    text = replace_once(
        text,
        '**{f"F{i}": getattr(ecodes, f"KEY_F{i}") for i in range(1, 13)},',
        '**{f"F{i}": getattr(ecodes, f"KEY_F{i}") for i in range(1, 14)},',
        "cvp_keyboard.py/F13",
    )

    old_specs = '''    "song_position": ActionSpec(description="Annonce mesure et temps"),
    "voice_volume_up": ActionSpec(description="Augmente le volume vocal"),
'''

    new_specs = '''    "song_position": ActionSpec(description="Annonce mesure et temps"),
    "song_measure_previous": ActionSpec(description="Recule d'une mesure"),
    "song_measure_next": ActionSpec(description="Avance d'une mesure"),
    "song_measure_previous_5": ActionSpec(description="Recule de cinq mesures"),
    "song_measure_next_5": ActionSpec(description="Avance de cinq mesures"),
    "song_goto_measure": ActionSpec(description="Aller à une mesure"),
    "song_loop_point_a": ActionSpec(description="Définit le point A"),
    "song_loop_point_b": ActionSpec(description="Définit le point B"),
    "song_loop_toggle": ActionSpec(description="Active / désactive la boucle A/B"),
    "style_start_stop": ActionSpec(description="Démarre / arrête le Style"),
    "song_volume_change": ActionSpec(
        True, -5, 5, "Modifie le volume Song / MidiMaster"
    ),
    "main_volume_change": ActionSpec(
        True, -5, 5, "Modifie le volume Main"
    ),
    "voice_volume_up": ActionSpec(description="Augmente le volume vocal"),
'''

    text = replace_once(
        text,
        old_specs,
        new_specs,
        "cvp_keyboard.py/ACTION_SPECS",
    )

    text = text.replace(
        "# Exact built-in fallback reproducing v1.4.1.",
        "# Built-in fallback reproducing the current RC3 mapping.",
        1,
    )

    old_bind = '''    "F1": "announce_tempo",
    "F2": "announce_transpose",
    "SPACE": "song_play_pause",
    "ENTER": "song_stop",
    "P": "song_position",
    "UP": "voice_volume_up",
    "DOWN": "voice_volume_down",
    "PAGEUP": "style_volume_up",
    "PAGEDOWN": "style_volume_down",
    "ESC": "restart",
'''

    new_bind = '''    "F1": "announce_tempo",
    "F2": "announce_transpose",
    "F3": "song_goto_measure",
    "F4": "song_loop_point_a",
    "F5": "song_loop_point_b",
    "F6": "song_loop_toggle",
    "F13": "style_start_stop",
    "SPACE": "song_play_pause",
    "ENTER": "song_stop",
    "P": "song_position",
    "LEFT": "song_measure_previous",
    "RIGHT": "song_measure_next",
    "SHIFT+LEFT": "song_measure_previous_5",
    "SHIFT+RIGHT": "song_measure_next_5",
    "UP": "voice_volume_up",
    "DOWN": "voice_volume_down",
    "PAGEUP": "style_volume_up",
    "PAGEDOWN": "style_volume_down",
    "HOME": "song_volume_change:1",
    "SHIFT+HOME": "song_volume_change:5",
    "END": "song_volume_change:-1",
    "SHIFT+END": "song_volume_change:-5",
    "INSERT": "main_volume_change:1",
    "SHIFT+INSERT": "main_volume_change:5",
    "DELETE": "main_volume_change:-1",
    "SHIFT+DELETE": "main_volume_change:-5",
    "ESC": "restart",
'''

    text = replace_once(
        text,
        old_bind,
        new_bind,
        "cvp_keyboard.py/BUILTIN_BINDINGS",
    )

    write_text(
        path,
        text,
    )


def patch_default_toml(path):
    text = path.read_text(
        encoding="utf-8"
    )

    old_transport = '''F1 = "announce_tempo"
F2 = "announce_transpose"

SPACE = "song_play_pause"
ENTER = "song_stop"
P = "song_position"
'''

    new_transport = '''F1 = "announce_tempo"
F2 = "announce_transpose"
F3 = "song_goto_measure"
F4 = "song_loop_point_a"
F5 = "song_loop_point_b"
F6 = "song_loop_toggle"
F13 = "style_start_stop"

SPACE = "song_play_pause"
ENTER = "song_stop"
P = "song_position"

LEFT = "song_measure_previous"
RIGHT = "song_measure_next"
"SHIFT+LEFT" = "song_measure_previous_5"
"SHIFT+RIGHT" = "song_measure_next_5"
'''

    text = replace_once(
        text,
        old_transport,
        new_transport,
        "config/default.toml/transport",
    )

    old_volumes = '''PAGEUP = "style_volume_up"
PAGEDOWN = "style_volume_down"
'''

    new_volumes = '''PAGEUP = "style_volume_up"
PAGEDOWN = "style_volume_down"

HOME = "song_volume_change:1"
"SHIFT+HOME" = "song_volume_change:5"
END = "song_volume_change:-1"
"SHIFT+END" = "song_volume_change:-5"

INSERT = "main_volume_change:1"
"SHIFT+INSERT" = "main_volume_change:5"
DELETE = "main_volume_change:-1"
"SHIFT+DELETE" = "main_volume_change:-5"
'''

    text = replace_once(
        text,
        old_volumes,
        new_volumes,
        "config/default.toml/volumes",
    )

    text = text.replace(
        "#   F1 ... F12",
        "#   F1 ... F13",
        1,
    )

    write_text(
        path,
        text,
    )


def patch_voice_generator(path):
    text = path.read_text(
        encoding="utf-8"
    )

    old_core = '''            ("song_position", None),
            ("voice_volume_up", None),
            ("voice_volume_down", None),
            ("style_volume_up", None),
            ("style_volume_down", None),
        })
'''

    new_core = '''            ("song_position", None),
            ("song_measure_previous", None),
            ("song_measure_next", None),
            ("song_measure_previous_5", None),
            ("song_measure_next_5", None),
            ("song_goto_measure", None),
            ("song_loop_point_a", None),
            ("song_loop_point_b", None),
            ("song_loop_toggle", None),
            ("style_start_stop", None),
            ("song_volume_change", 1),
            ("main_volume_change", 1),
            ("voice_volume_up", None),
            ("voice_volume_down", None),
            ("style_volume_up", None),
            ("style_volume_down", None),
        })
'''

    text = replace_once(
        text,
        old_core,
        new_core,
        "generate_configured_voices/core actions",
    )

    old_branch = '''        elif name in {"style_volume_up", "style_volume_down"}:
            for volume in range(0, 128):
                add(
                    f"style_volume/style_volume_{volume:03d}.wav",
                    f"Accompagnement {volume}.",
                )

        elif name == "song_play_pause":
'''

    new_branch = '''        elif name in {"style_volume_up", "style_volume_down"}:
            for volume in range(0, 128):
                add(
                    f"style_volume/style_volume_{volume:03d}.wav",
                    f"Accompagnement {volume}.",
                )

        elif name == "song_volume_change":
            for volume in range(0, 128):
                add(
                    f"song_volume/song_volume_{volume:03d}.wav",
                    f"Volume Song {volume}.",
                )

        elif name == "main_volume_change":
            for volume in range(0, 128):
                add(
                    f"main_volume/main_volume_{volume:03d}.wav",
                    f"Volume Main {volume}.",
                )

        elif name == "style_start_stop":
            add("style_transport/start.wav", "Style démarré.")
            add("style_transport/stop.wav", "Style arrêté.")

        elif name == "song_goto_measure":
            add("song/goto_prompt.wav", "Saisir le numéro de mesure puis Entrée.")
            add("song/goto_cancelled.wav", "Saisie mesure annulée.")
            add("song/invalid_measure.wav", "Mesure invalide.")
            add("song/no_song.wav", "Aucun Song chargé.")
            add("song/detection_error.wav", "Impossible de vérifier le Song.")

        elif name in {"song_loop_point_a", "song_loop_point_b", "song_loop_toggle"}:
            add("song/loop_a_missing.wav", "Point A non défini.")
            add("song/loop_b_invalid.wav", "Point B invalide.")
            add("song/loop_points_missing.wav", "Points A et B non définis.")

        elif name == "song_play_pause":
'''

    text = replace_once(
        text,
        old_branch,
        new_branch,
        "generate_configured_voices/prompts",
    )

    write_text(
        path,
        text,
    )


def validate(root):
    py_files = [
        root / "cvp_access_v1.5.py",
        root / "cvp_song.py",
        root / "cvp_speech.py",
        root / "cvp_keyboard.py",
        root / "cvp_keyboard_map.py",
        root
        / "cvp_access_installer"
        / "tools"
        / "generate_configured_voices.py",
    ]

    for path in py_files:
        py_compile.compile(
            str(path),
            doraise=True,
        )

    for path in [
        root / "keyboard_RC3_example.toml",
        root / "config" / "default.toml",
    ]:
        with path.open("rb") as handle:
            tomllib.load(handle)

    checks = {
        root / "cvp_access_v1.5.py": [
            '"style_start_stop"',
            '"song_volume_change"',
            '"main_volume_change"',
        ],
        root / "cvp_keyboard.py": [
            '"F13": "style_start_stop"',
            '"SHIFT+HOME": "song_volume_change:5"',
            '"SHIFT+DELETE": "main_volume_change:-5"',
        ],
        root / "config" / "default.toml": [
            'F13 = "style_start_stop"',
            '"SHIFT+END" = "song_volume_change:-5"',
        ],
    }

    for path, needles in checks.items():
        text = path.read_text(
            encoding="utf-8"
        )
        for needle in needles:
            if needle not in text:
                fail(
                    f"validation : {path.name} ne contient pas {needle}"
                )


def main():
    bundle_dir = Path(
        __file__
    ).resolve().parent

    if len(sys.argv) >= 2:
        root = Path(
            sys.argv[1]
        ).expanduser().resolve()
    else:
        root = Path.cwd().resolve()

    if not (
        root / "cvp_access_v1.5.py"
    ).is_file():
        fail(
            f"{root} n'est pas le checkout CVP_access"
        )

    complete = [
        "cvp_access_v1.5.py",
        "cvp_song.py",
        "cvp_speech.py",
        "cvp_keyboard_map.py",
        "keyboard_RC3_example.toml",
        "CVP905_PROTOCOL_CHECKPOINT_RC3.md",
    ]

    for name in complete:
        copy_complete(
            bundle_dir / name,
            root / name,
        )

    patch_keyboard(
        root / "cvp_keyboard.py"
    )
    patch_default_toml(
        root / "config" / "default.toml"
    )
    patch_voice_generator(
        root
        / "cvp_access_installer"
        / "tools"
        / "generate_configured_voices.py"
    )

    validate(root)

    print()
    print("RC3 CONTROLS : MISE À JOUR APPLIQUÉE")
    print("=" * 64)
    print("F13           : Style Start / Stop")
    print("HOME / END    : Volume Song +/-1")
    print("Maj+HOME / END: Volume Song +/-5")
    print("INS / DEL     : Volume Main +/-1")
    print("Maj+INS / DEL : Volume Main +/-5")
    print("Métronome     : conservation navigation arrière")
    print()
    print("Validation Python/TOML : OK")
    print("Sauvegardes            : *" + BACKUP_SUFFIX)
    print()
    print("Étape suivante : tester le runtime avant git commit.")


if __name__ == "__main__":
    main()
