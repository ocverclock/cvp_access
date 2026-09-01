#!/usr/bin/env python3
from pathlib import Path
import py_compile
import tomllib

root = Path(__file__).resolve().parent

for rel in [
    "cvp_access_1_5_1.py",
    "cvp_keyboard.py",
    "cvp_keyboard_map.py",
    "cvp_song_151.py",
    "cvp_speech.py",
    "cvp_speech_151.py",
    "cvp_access_installer/tools/generate_configured_voices.py",
    "cvp_access_installer/tools/generate_151_voices.py",
    "cvp_access_installer/tools/cvp_doctor_151.py",
]:
    py_compile.compile(str(root / rel), doraise=True)

with (root / "config/default-1.5.1.toml").open("rb") as handle:
    cfg = tomllib.load(handle)

general = cfg["general"]
keys = cfg["keys"]
assert general["caps_lock_layer"] is False

expected = {
    "TOP1": "style_part_toggle:1",
    "TOP8": "style_part_toggle:8",
    "W": "announce_style_name",
    "X": "announce_song_name",
    "C": "announce_song_length",
    "V": "sync_start_toggle",
    "B": "guide_toggle",
    "F7": "metronome_toggle",
    "PAGEUP": "style_volume_change:1",
    "SHIFT+PAGEUP": "style_volume_change:5",
    "PAGEDOWN": "style_volume_change:-1",
    "SHIFT+PAGEDOWN": "style_volume_change:-5",
}
for combo, action in expected.items():
    assert keys[combo] == action, f"{combo}: attendu {action!r}, obtenu {keys.get(combo)!r}"

assert not any(str(combo).upper().startswith("CAPS+") for combo in keys)

assigned_actions = {
    str(value).split(":", 1)[0]
    for value in keys.values()
    if isinstance(value, str)
}
for action in (
    "style_intro",
    "style_main",
    "style_fill",
    "style_break",
    "style_ending",
    "registration_recall",
    "stream_lights_toggle",
):
    assert action not in assigned_actions

print("CVP Access 1.5.1 RC2 package: OK")
