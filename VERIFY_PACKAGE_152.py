#!/usr/bin/env python3
from pathlib import Path
import py_compile
import tomllib

root = Path(__file__).resolve().parent

for rel in [
    "cvp_access_1_5_2.py",
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
    "cvp_access_installer/tools/cvp_web.py",
]:
    path = root / rel
    assert path.is_file(), f"Fichier requis absent : {rel}"
    py_compile.compile(str(path), doraise=True)

maintenance_required = [
    "cvp_access_installer/upgrade_1_5_2.sh",
    "cvp_access_installer/install_maintenance.sh",
    "cvp_access_installer/network/cvp-wifi-fallback",
    "cvp_access_installer/network/cvp-wifi-connect",
    "cvp_access_installer/systemd/cvp-wifi-fallback.service.in",
    "cvp_access_installer/systemd/cvp-web.service.in",
]
for rel in maintenance_required:
    assert (root / rel).is_file(), f"Fichier maintenance absent : {rel}"

frontend_152_source = (root / "cvp_access_1_5_2.py").read_text(encoding="utf-8")
assert 'VERSION = "1.5.2-RC1"' in frontend_152_source
assert "cvp_access_1_5_1_base" in frontend_152_source

core_source = (root / "cvp_access_v1.4.1.py").read_text(encoding="utf-8")
assert "ProdipeMIDIlilo MIDI 1" in core_source
assert "USB MIDI Interface MIDI 1" in core_source
assert "configured_midi_name" in core_source
assert "configured_keyboard_path" in core_source
assert "/etc/cvp-access/hardware.toml" in core_source

keyboard_map_source = (root / "cvp_keyboard_map.py").read_text(encoding="utf-8")
assert "maintenance-grid" in keyboard_map_source
assert "Accès Web" in keyboard_map_source
assert "Partages Samba" in keyboard_map_source
assert "@page{size:A4 landscape" in keyboard_map_source
assert "height:198mm" in keyboard_map_source
assert "${html.escape(hostname)}" not in keyboard_map_source
assert "copyValue(this)" in keyboard_map_source
assert "smb://" in keyboard_map_source

portal_source = (
    root / "cvp_access_installer/tools/cvp_web.py"
).read_text(encoding="utf-8")
assert "10.42.0.1" in portal_source
assert "/api/midi/select" in portal_source
assert "/api/keyboard/select" in portal_source
assert "/api/wifi/connect" in portal_source
assert "/api/wifi/scan" in portal_source
assert "webAccess" in portal_source
assert "sambaAccess" in portal_source
assert "copyButton(value)" in portal_source
assert "smbProject" in portal_source
assert "request_authorized" in portal_source
assert "cvp-access.service" in portal_source

speech_source = (root / "cvp_speech_151.py").read_text(encoding="utf-8")
runtime_source = (root / "cvp_access_v1.5.py").read_text(encoding="utf-8")
generator_source = (
    root / "cvp_access_installer/tools/generate_151_voices.py"
).read_text(encoding="utf-8")
doctor_source = (
    root / "cvp_access_installer/tools/cvp_doctor_151.py"
).read_text(encoding="utf-8")

assert "announce_startup_ready" in speech_source
assert "announce_device_restart" in speech_source
assert "announce_startup_ready" in runtime_source
assert "system/startup_ready.wav" in generator_source
assert "system/restart_device.wav" in generator_source
assert "startup_ready.wav" in doctor_source
assert "restart_device.wav" in doctor_source
assert "WAV système" in doctor_source
assert '("1.5.1", "1.5.2")' in doctor_source

fresh_install_source = (
    root / "cvp_access_installer/install.sh"
).read_text(encoding="utf-8")
update_source = (
    root / "cvp_access_installer/update.sh"
).read_text(encoding="utf-8")
upgrade_152_source = (
    root / "cvp_access_installer/upgrade_1_5_2.sh"
).read_text(encoding="utf-8")
assert "upgrade_1_5_2.sh" in fresh_install_source
assert "upgrade_1_5_2.sh" in update_source
assert 'CVP_FRONTEND_SOURCE="cvp_access_1_5_2.py"' in upgrade_152_source
assert 'CVP_TARGET_VERSION="1.5.2-RC1"' in upgrade_152_source

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

print("CVP Access 1.5.2 RC1 package: OK")
