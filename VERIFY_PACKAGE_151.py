#!/usr/bin/env python3
from pathlib import Path
import py_compile
import tomllib

root = Path(__file__).resolve().parent

for rel in [
    "cvp_access_1_5_1.py",
    "cvp_access_1_5_1_base.py",
    "cvp_access_v1.5.py",
    "cvp_access_v1.4.1.py",
    "cvp_keyboard.py",
    "cvp_keyboard_map.py",
    "cvp_song.py",
    "cvp_song_151.py",
    "cvp_speech.py",
    "cvp_speech_151.py",
    "cvp_piper_worker.py",
    "cvp_midi.py",
    "cvp_yamaha.py",
    "cvp_registration.py",
    "cvp_style.py",
    "cvp_voice.py",
    "cvp_voice_names.py",
    "cvp_access_installer/tools/generate_configured_voices.py",
    "cvp_access_installer/tools/generate_151_voices.py",
    "cvp_access_installer/tools/cvp_doctor_151.py",
]:
    path = root / rel
    assert path.is_file(), f"Fichier requis absent : {rel}"
    py_compile.compile(str(path), doraise=True)

speech_source = (root / "cvp_speech_151.py").read_text(encoding="utf-8")
runtime_source = (root / "cvp_access_v1.5.py").read_text(encoding="utf-8")
generator_source = (
    root / "cvp_access_installer/tools/generate_151_voices.py"
).read_text(encoding="utf-8")
doctor_source = (
    root / "cvp_access_installer/tools/cvp_doctor_151.py"
).read_text(encoding="utf-8")

assert "announce_startup_ready" in speech_source
assert "announce_startup_ready" in runtime_source
assert "system/startup_ready.wav" in generator_source
assert "system/startup_ready.wav" in doctor_source

with (root / "config/default-1.5.1.toml").open("rb") as handle:
    cfg = tomllib.load(handle)

general = cfg["general"]
keys = cfg["keys"]
assert general["caps_lock_layer"] is False

expected = {
    "TOP1": "style_part_toggle:1",
    "TOP8": "style_part_toggle:8",
    "RPAREN": "style_all_parts_on",
    "L": "song_all_tracks_on",
    "W": "announce_style_name",
    "X": "announce_song_name",
    "C": "announce_song_length",
    "V": "sync_start_toggle",
    "B": "guide_toggle",
    "M": "voice_guide_mute_toggle",
    "N": "announce_main_voice_name",
    "COMMA": "announce_layer_voice_name",
    "SEMICOLON": "announce_left_voice_name",
    "F7": "metronome_toggle",
    "PAGEUP": "style_volume_change:1",
    "SHIFT+PAGEUP": "style_volume_change:5",
    "PAGEDOWN": "style_volume_change:-1",
    "SHIFT+PAGEDOWN": "style_volume_change:-5",
}

song_keys = [
    "A", "Z", "E", "R", "T", "Y", "U", "I",
    "Q", "S", "D", "F", "G", "H", "J", "K",
]

for track, key in enumerate(song_keys, start=1):
    expected[key] = f"song_track_toggle:{track}"
    expected[f"SHIFT+{key}"] = f"song_track_solo:{track}"

for combo, action in expected.items():
    assert keys.get(combo) == action, (
        f"{combo}: attendu {action!r}, obtenu {keys.get(combo)!r}"
    )

assert not any(str(combo).upper().startswith("CAPS+") for combo in keys)
assert not any(
    str(combo).upper().startswith("ALT+")
    and str(value).startswith("song_track_solo:")
    for combo, value in keys.items()
)

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

for action in (
    "song_all_tracks_on",
    "style_all_parts_on",
    "song_track_solo",
    "voice_guide_mute_toggle",
):
    assert action in assigned_actions, f"Action attendue non affectée : {action}"

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
