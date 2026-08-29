#!/usr/bin/env python3
"""Applique la migration CVP Access 1.5.1 à un checkout existant."""

from __future__ import annotations

import sys
from pathlib import Path


def fail(msg):
    raise SystemExit("ERREUR: " + msg)


def replace_once(text, old, new, label):
    if old not in text:
        fail(f"ancre introuvable pour {label}")
    return text.replace(old, new, 1)


def replace_method(text, class_name, method_name, new_method):
    class_marker = f"class {class_name}"
    pos = text.find(class_marker)
    if pos < 0:
        fail(f"classe {class_name} introuvable")

    method_marker = f"    def {method_name}("
    start = text.find(method_marker, pos)
    if start < 0:
        fail(f"méthode {class_name}.{method_name} introuvable")

    next_method = text.find("\n    def ", start + len(method_marker))
    next_class = text.find("\nclass ", start + len(method_marker))

    candidates = [x for x in (next_method, next_class) if x >= 0]
    end = min(candidates) + 1 if candidates else len(text)

    return text[:start] + new_method.rstrip() + "\n\n" + text[end:]


def patch_runtime(repo):
    p = repo / "cvp_access_v1.5.py"
    if not p.is_file():
        fail("cvp_access_v1.5.py absent")

    s = p.read_text()

    s = s.replace(
        '"""CVP Access v1.5',
        '"""CVP Access v1.5.1',
        1,
    )
    s = replace_once(
        s,
        'VERSION = "1.5-RC4-dev"',
        'VERSION = "1.5.1-RC1-dev"',
        "VERSION runtime",
    )

    import_anchor = "from cvp_song import SongController\n"
    import_block = (
        "from cvp_song import SongController\n"
        "from cvp_midi import MidiService\n"
        "from cvp_registration import RegistrationController\n"
        "from cvp_style import StyleController\n"
        "from cvp_voice import VoiceController\n"
    )

    if "from cvp_midi import MidiService" not in s:
        s = replace_once(
            s,
            import_anchor,
            import_block,
            "imports 1.5.1",
        )

    init_anchor = (
        "        self.core = core\n"
        "        self.port = port\n"
        "        self.song = SongController(core, port)\n"
    )
    init_new = (
        "        self.core = core\n"
        "        self.port = port\n"
        "        self.midi = MidiService(core, port)\n"
        "        self.song = SongController(core, port)\n"
        "        self.style = StyleController(self.midi)\n"
        "        self.voice = VoiceController(self.midi)\n"
        "        self.registration = RegistrationController(self.midi)\n"
    )

    if "self.midi = MidiService(core, port)" not in s:
        s = replace_once(
            s,
            init_anchor,
            init_new,
            "CVPActions.__init__",
        )

    new_registration_method = """    def registration_recall(self, number):
        try:
            ok = self.registration.recall(
                number,
                verify_notification=False,
            )
        except ValueError:
            print("Numero de Registration invalide :", number)
            return

        if not ok:
            print(
                f"Impossible de rappeler Registration {number}."
            )
            return

        print(f"Registration {number} rappelée.")
"""

    s = replace_method(
        s,
        "CVPActions",
        "registration_recall",
        new_registration_method,
    )

    p.write_text(s)


def patch_song(repo):
    p = repo / "cvp_song.py"
    if not p.is_file():
        fail("cvp_song.py absent")

    s = p.read_text()

    if "from cvp_yamaha import decode_yamaha_text" not in s:
        s = replace_once(
            s,
            "import time\n",
            "import time\n\nfrom cvp_yamaha import decode_yamaha_text\n",
            "import codec Yamaha",
        )

    start = s.find("def decode_yamaha_text(data):")
    if start >= 0:
        end = s.find("\n\nclass SongController:", start)
        if end < 0:
            fail("fin de l'ancien decode_yamaha_text introuvable")
        s = s[:start] + s[end + 2:]

    p.write_text(s)


def patch_project_state(repo):
    p = repo / "PROJECT_STATE.md"
    if not p.is_file():
        return

    s = p.read_text()
    s = s.replace(
        "Runtime : CVP Access 1.5-RC4-dev",
        "Runtime : CVP Access 1.5.1-RC1-dev",
    )

    marker = "Moteur SysEx conservé : cvp_access_v1.4.1.py"
    replacement = (
        "Moteur SysEx historique conservé temporairement : "
        "cvp_access_v1.4.1.py\n"
        "API MIDI publique : cvp_midi.py"
    )
    s = s.replace(marker, replacement)
    p.write_text(s)


def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    required_new = [
        "cvp_midi.py",
        "cvp_yamaha.py",
        "cvp_registration.py",
        "cvp_style.py",
        "cvp_voice.py",
    ]

    for name in required_new:
        if not (repo / name).is_file():
            fail(
                f"{name} absent. Copie d'abord tous les fichiers "
                "du paquet 1.5.1 dans le dépôt."
            )

    patch_runtime(repo)
    patch_song(repo)
    patch_project_state(repo)

    print("CVP Access -> 1.5.1-RC1-dev")
    print("Fichiers runtime migrés avec succès.")


if __name__ == "__main__":
    main()
