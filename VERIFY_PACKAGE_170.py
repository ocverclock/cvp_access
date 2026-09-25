#!/usr/bin/env python3
"""Static/package verifier for CVP Access 1.7.0-RC1."""

from __future__ import annotations

import ast
import re
import subprocess
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parent

python_files = [
    "cvp_access_1_7.py",
    "cvp_access_1_6_1.py",
    "cvp_access_1_5_2.py",
    "cvp_access_1_5_1_base.py",
    "cvp_access_v1.5.py",
    "cvp_access_v1.4.1.py",
    "cvp_action_catalog.py",
    "cvp_keyboard_layout.py",
    "cvp_keyboard.py",
    "cvp_keyboard_profiles.py",
    "cvp_keyboard_web.py",
    "cvp_keyboard_map.py",
    "cvp_recorder.py",
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
    "cvp_access_installer/tools/cvp_doctor.py",
    "cvp_access_installer/tools/cvp_web.py",
]

for rel in python_files:
    path = root / rel
    assert path.is_file(), f"Fichier Python requis absent : {rel}"
    ast.parse(path.read_text(encoding="utf-8"), filename=rel)

shell_files = [
    "cvp_access_installer/install.sh",
    "cvp_access_installer/update.sh",
    "cvp_access_installer/upgrade_1_5_1.sh",
    "cvp_access_installer/upgrade_1_5_1_base.sh",
    "cvp_access_installer/upgrade_1_5_2.sh",
    "cvp_access_installer/upgrade_1_6_0.sh",
    "cvp_access_installer/upgrade_1_6_1.sh",
    "cvp_access_installer/upgrade_1_7_0.sh",
    "cvp_access_installer/install_maintenance.sh",
    "cvp_access_installer/network/cvp-wifi-fallback",
    "cvp_access_installer/network/cvp-wifi-connect",
    "cvp_access_installer/tools/cvp_update_from_github",
    "cvp_access_installer/tools/generate_recorder_cues.sh",
]
for rel in shell_files:
    path = root / rel
    assert path.is_file(), f"Script shell absent : {rel}"
    result = subprocess.run(
        ["bash", "-n", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Syntaxe shell invalide : {rel}\n{result.stderr}"
    )

required_files = [
    "config/default-current.toml",
    "config/default-1.5.1.toml",
    "cvp_access_installer/release.env",
    "cvp_access_installer/systemd/cvp-web.service.in",
    "docs/CVP_ACCESS_1_7_MAPPING_UI_DESIGN.md",
]
for rel in required_files:
    assert (root / rel).is_file(), f"Fichier requis absent : {rel}"

frontend = (root / "cvp_access_1_7.py").read_text(encoding="utf-8")
assert 'VERSION = "1.7.0-RC1"' in frontend
assert "CVP_RECORDER_ENABLED" in frontend
assert "cvp_access_1_5_2" in frontend

release_manifest = (
    root / "cvp_access_installer/release.env"
).read_text(encoding="utf-8")
assert "CVP_RELEASE_VERSION=1.7.0-RC1" in release_manifest
assert "CVP_RELEASE_FRONTEND=cvp_access_1_7.py" in release_manifest
assert "CVP_RELEASE_UPGRADER=upgrade_1_7_0.sh" in release_manifest
assert "CVP_RELEASE_VERIFIER=VERIFY_PACKAGE_170.py" in release_manifest

upgrade = (
    root / "cvp_access_installer/upgrade_1_7_0.sh"
).read_text(encoding="utf-8")
assert 'CVP_FRONTEND_SOURCE="cvp_access_1_7.py"' in upgrade
assert 'CVP_TARGET_VERSION="1.7.0-RC1"' in upgrade
assert "CVP_SKIP_KEYBOARD_MIGRATION=1" in upgrade
assert "cvp_keyboard_profiles.py" in upgrade
assert "--init" in upgrade

shared_upgrade = (
    root / "cvp_access_installer/upgrade_1_5_1_base.sh"
).read_text(encoding="utf-8")
for name in (
    "cvp_action_catalog.py",
    "cvp_keyboard_layout.py",
    "cvp_keyboard_profiles.py",
    "cvp_keyboard_web.py",
    "default-keyboard-current.toml",
):
    assert name in shared_upgrade, f"Déploiement runtime manquant : {name}"
assert 'CVP_SKIP_KEYBOARD_MIGRATION' in shared_upgrade

legacy_migration = (
    root / "cvp_access_installer/upgrade_1_5_1.sh"
).read_text(encoding="utf-8")
assert 'CVP_SKIP_KEYBOARD_MIGRATION' in legacy_migration

fresh_install = (
    root / "cvp_access_installer/install.sh"
).read_text(encoding="utf-8")
assert "config/default-current.toml" in fresh_install
assert "cvp_action_catalog.py" in fresh_install
assert "cvp_keyboard_layout.py" in fresh_install

with (root / "config/default-current.toml").open("rb") as handle:
    factory = tomllib.load(handle)
assert factory["general"]["caps_lock_layer"] is False
factory_keys = factory["keys"]
assert isinstance(factory_keys, dict)
assert len(factory_keys) == 83

catalog_ns = {}
exec(
    compile(
        (root / "cvp_action_catalog.py").read_text(encoding="utf-8"),
        "cvp_action_catalog.py",
        "exec",
    ),
    catalog_ns,
)
catalog = catalog_ns["ACTION_CATALOG"]
assigned_actions = {
    value.split(":", 1)[0]
    for value in factory_keys.values()
    if isinstance(value, str)
}
missing_catalog = sorted(assigned_actions - set(catalog))
assert not missing_catalog, (
    "Actions du profil usine absentes du catalogue : "
    + ", ".join(missing_catalog)
)
for action in (
    "song_track_solo",
    "song_all_tracks_on",
    "style_all_parts_on",
    "voice_guide_mute_toggle",
):
    assert action in catalog

keyboard = (root / "cvp_keyboard.py").read_text(encoding="utf-8")
assert "from cvp_action_catalog import ACTION_SPECS, ActionSpec, action_help" in keyboard
assert "SHARED_MODIFIER_ORDER" in keyboard
assert 'source=Path("<builtin-1.7>")' in keyboard
assert "caps_lock_layer=False" in keyboard
assert "An empty [keys] table is valid in 1.7" in keyboard
assert "if not config.issues:" in keyboard

profiles = (root / "cvp_keyboard_profiles.py").read_text(encoding="utf-8")
for marker in (
    "keyboard-profiles.json",
    'RESERVED_KEYS = {"F14", "F15", "F16"}',
    "RevisionConflict",
    "def create_profile(",
    "def duplicate_profile(",
    "def rename_profile(",
    "def delete_profile(",
    "def activate_profile(",
    "def save_profile(",
    "runuser",
    "systemctl",
    "restart",
    "cvp-access.service",
    "rollback",
):
    assert marker.lower() in profiles.lower(), f"Gestion profils incomplète : {marker}"
assert 'if "CTRL" in parts[:-1]' in profiles
assert "active_revision != current_revision" in profiles
assert "MAX_BACKUPS = 10" in profiles
assert "_write_user_file(ACTIVE_CONFIG" in profiles

web_helper = (root / "cvp_keyboard_web.py").read_text(encoding="utf-8")
for marker in (
    "KEYBOARD_EDITOR",
    "/api/keyboard/apply",
    "/api/keyboard/profiles/create",
    "/api/keyboard/profiles/duplicate",
    "/api/keyboard/profiles/rename",
    "/api/keyboard/profiles/delete",
    "/api/keyboard/profiles/activate",
    "Enregistrer sous",
    "Activer cette configuration",
    "Rechercher une fonction",
    "Modifications en attente",
):
    assert marker in web_helper, f"Éditeur Web incomplet : {marker}"

portal = (
    root / "cvp_access_installer/tools/cvp_web.py"
).read_text(encoding="utf-8")
for marker in (
    "/keyboard",
    "/api/keyboard/catalog",
    "/api/keyboard/config",
    "/api/keyboard/profiles",
    "keyboard_write_authorized",
    "Configuration clavier",
):
    assert marker in portal, f"Portail 1.7 incomplet : {marker}"
assert "if not AUTH_REQUIRED" in portal
strict_auth = re.search(
    r"def keyboard_write_authorized\(payload\):(.*?)(?=\ndef )",
    portal,
    flags=re.S,
)
assert strict_auth, "Fonction d'autorisation clavier absente"
assert "if not AUTH_REQUIRED" not in strict_auth.group(1)
assert "hmac.compare_digest" in strict_auth.group(1)

doctor = (
    root / "cvp_access_installer/tools/cvp_doctor.py"
).read_text(encoding="utf-8")
assert "profil personnalisé" in doctor
assert "Configuration clavier" in doctor
assert "default-keyboard-current.toml" in doctor
assert "expected_caps" not in doctor

layout = (root / "cvp_keyboard_layout.py").read_text(encoding="utf-8")
assert '("CTRL", "ALT", "ALTGR", "SHIFT", "META", "CAPS")' in layout
assert '"F14": "Morceau précédent / Recorder"' in layout
assert '"F15": "Dictaphone MIDI"' in layout
assert '"F16": "Morceau suivant / Recorder"' in layout

service = (
    root / "cvp_access_installer/systemd/cvp-web.service.in"
).read_text(encoding="utf-8")
# Global dev auth may remain disabled in RC1; keyboard writes are independently
# protected server-side and the verifier checks that strict path above.
assert "Environment=CVP_WEB_REQUIRE_AUTH=0" in service

print("CVP Access 1.7.0 RC1 package: OK")
