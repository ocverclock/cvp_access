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
    "cvp_voice_names.py",
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
    "N": "announce_main_voice_name",
    "COMMA": "announce_layer_voice_name",
    "SEMICOLON": "announce_left_voice_name",
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

from cvp_voice_names import (
    CVPVoiceId,
    decode_cvp_voice,
    resolve_voice_name,
)

assert decode_cvp_voice(bytes([0x03, 0x30, 0x00, 0x00])) == CVPVoiceId(108, 0, 1)
assert decode_cvp_voice(bytes([0x00, 0x20, 0x42, 0x31])) == CVPVoiceId(8, 33, 50)
assert decode_cvp_voice(bytes([0x03, 0x20, 0x0E, 0x04])) == CVPVoiceId(104, 7, 5)

assert resolve_voice_name(CVPVoiceId(108, 0, 1)) == "CFX Concert Grand"
assert resolve_voice_name(CVPVoiceId(8, 33, 50)) == "Seattle Strings"
assert resolve_voice_name(CVPVoiceId(104, 7, 5)) == "Suitcase Soft"

print("CVP Access 1.5.1 RC3 package: OK")
