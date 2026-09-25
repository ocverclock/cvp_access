#!/usr/bin/env python3
"""Functional self-test for the CVP Access 1.7 keyboard/profile layer.

No Yamaha hardware is touched. A tiny evdev stub lets the real keyboard parser
run against a temporary configuration tree.
"""

from __future__ import annotations

import getpass
import hashlib
import importlib
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path


class _ECodes:
    EV_KEY = 1
    LED_CAPSL = 1

    def __init__(self):
        self._values = {}
        self._next = 10

    def __getattr__(self, name):
        if name not in self._values:
            self._values[name] = self._next
            self._next += 1
        return self._values[name]


evdev_stub = types.ModuleType("evdev")
evdev_stub.ecodes = _ECodes()
sys.modules["evdev"] = evdev_stub

root = Path(__file__).resolve().parent

with tempfile.TemporaryDirectory(prefix="cvp-access-170-") as tmp_raw:
    tmp = Path(tmp_raw)
    config_dir = tmp / "etc-cvp-access"
    runtime_dir = tmp / "runtime"
    config_dir.mkdir()
    runtime_dir.mkdir()

    factory = root / "config/default-current.toml"
    assert factory.is_file()
    shutil.copy2(factory, runtime_dir / "default-keyboard-current.toml")
    shutil.copy2(factory, config_dir / "keyboard.toml")

    os.environ["CVP_CONFIG_DIR"] = str(config_dir)
    os.environ["CVP_RUNTIME_DIR"] = str(runtime_dir)
    os.environ["CVP_USER"] = getpass.getuser()

    keyboard = importlib.import_module("cvp_keyboard")
    profiles = importlib.import_module("cvp_keyboard_profiles")
    web = importlib.import_module("cvp_keyboard_web")

    # Official factory profile parses exactly and the real runtime accepts it.
    factory_cfg = keyboard.read_config_file(factory)
    assert not factory_cfg.issues
    assert len(factory_cfg.bindings) == 83

    # An intentionally empty [keys] section is valid and must not fall back.
    empty_path = tmp / "empty.toml"
    empty_path.write_text(
        """[general]
format_version = 2
layout = "azerty"
caps_lock_layer = false
caps_fallback_to_base = true

[speech]
mode = "hybrid"
generation = "configured"
cache = true
voice = "fr_FR-siwis-medium"
length_scale = 0.85

[keys]
""",
        encoding="utf-8",
    )
    empty_cfg = keyboard.load_keyboard_config(empty_path, factory)
    assert empty_cfg.source == empty_path
    assert empty_cfg.bindings == {}
    assert not empty_cfg.issues

    state = profiles.ensure_store()
    assert state["active_profile_id"] == "standard"
    listed = profiles.list_profiles()
    assert {item["id"] for item in listed["profiles"]} == {"factory", "standard"}
    assert profiles.get_profile("factory")["protected"] is True
    standard = profiles.get_profile("standard")
    assert standard["active"] is True
    assert len(standard["bindings"]) == 83

    # Do not run systemd/Piper in the self-test. Keep the real transactional
    # code in production, but substitute its side effects for profile logic.
    def fake_activate(data):
        profiles._write_user_file(profiles.ACTIVE_CONFIG, data, 0o660)
        return {
            "ok": True,
            "revision": hashlib.sha256(data).hexdigest(),
            "backup": None,
        }

    profiles._activate_bytes = fake_activate

    # Create / rename / duplicate / delete.
    custom = profiles.create_profile("Gospel", "standard")
    assert custom["name"] == "Gospel"
    custom = profiles.rename_profile(custom["id"], "Gospel concert")
    assert custom["name"] == "Gospel concert"
    copy = profiles.duplicate_profile(custom["id"], "Gospel copie")
    assert copy["bindings"] == custom["bindings"]
    profiles.delete_profile(copy["id"])
    assert copy["id"] not in {
        item["id"] for item in profiles.list_profiles()["profiles"]
    }

    # Factory profile cannot be renamed/deleted.
    for operation in (
        lambda: profiles.rename_profile("factory", "Usine modifiée"),
        lambda: profiles.delete_profile("factory"),
    ):
        try:
            operation()
        except profiles.ProfileError:
            pass
        else:
            raise AssertionError("Le profil usine doit rester protégé")

    # Graphical edit uses the real parser and revision control.
    changed = profiles.save_profile(
        custom["id"],
        custom["revision"],
        [{"combo": "F8", "action": "song_track_toggle:7"}],
    )
    assert changed["bindings"]["F8"] == "song_track_toggle:7"

    try:
        profiles.save_profile(
            custom["id"],
            custom["revision"],
            [{"combo": "F9", "action": "announce_song_name"}],
        )
    except profiles.RevisionConflict:
        pass
    else:
        raise AssertionError("Une révision obsolète doit être refusée")

    # Recorder and CTRL stay server-side protected.
    for combo in ("F14", "SHIFT+F15", "CTRL+F8"):
        current = profiles.get_profile(custom["id"])
        try:
            profiles.save_profile(
                custom["id"],
                current["revision"],
                [{"combo": combo, "action": "announce_song_name"}],
            )
        except profiles.ProfileError:
            pass
        else:
            raise AssertionError(f"Combinaison réservée acceptée : {combo}")

    # Activate custom profile without changing any Yamaha code.
    result = profiles.activate_profile(custom["id"])
    assert result["profile"]["active"] is True
    assert profiles.file_revision(profiles.ACTIVE_CONFIG) == result["profile"]["revision"]

    # Deliberately remove every binding from the active profile.
    active = profiles.get_profile(custom["id"])
    clear_changes = [
        {"combo": combo, "action": None}
        for combo in active["bindings"]
    ]
    cleared = profiles.save_profile(
        custom["id"],
        active["revision"],
        clear_changes,
    )
    assert cleared["bindings"] == {}
    parsed_active = keyboard.read_config_file(profiles.ACTIVE_CONFIG)
    assert parsed_active.bindings == {}
    assert not parsed_active.issues

    # Manual/Samba edit is detected, and can be preserved as a new profile.
    external_data = factory.read_bytes()
    profiles._write_user_file(profiles.ACTIVE_CONFIG, external_data, 0o660)
    mismatch = profiles.get_profile(custom["id"])
    assert mismatch["active"] is True
    assert mismatch["active_file_matches_profile"] is False

    imported = profiles.save_active_external_as_profile("Import manuel")
    assert imported["active"] is False
    assert imported["bindings"]["A"].text if False else True
    assert imported["bindings"]["A"] == "song_track_toggle:1"

    # Re-activating the stored profile discards the external file by explicit
    # user action and restores the saved (empty) profile.
    profiles.activate_profile(custom["id"])
    assert keyboard.read_config_file(profiles.ACTIVE_CONFIG).bindings == {}

    # UI catalogue: no CAPS/CTRL creation layer, navigation keys present,
    # parameterized functions remain two-step.
    payload = web.catalog_payload()
    layer_names = [item["prefix"] for item in payload["layers"]]
    assert layer_names == ["", "SHIFT", "ALT", "ALTGR", "META"]
    all_keys = [item["key"] for row in payload["rows"] for item in row]
    for key in ("INSERT", "HOME", "PAGEUP", "DELETE", "END", "PAGEDOWN", "UP", "DOWN", "LEFT", "RIGHT"):
        assert key in all_keys
    song_track = next(
        item for item in payload["actions"]
        if item["id"] == "song_track_toggle"
    )
    assert song_track["parameter_required"] is True
    assert len(song_track["variants"]) == 16

print("CVP Access 1.7 keyboard/profile self-test: OK")
