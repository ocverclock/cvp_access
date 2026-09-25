#!/usr/bin/env python3
"""Static + functional verifier for CVP Access 1.7.0-RC1."""

from __future__ import annotations

import ast
import re
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Python syntax: parse without importing hardware dependencies.
# ---------------------------------------------------------------------------

PYTHON_FILES = [
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
    "TEST_KEYBOARD_PROFILES_170.py",
]

for rel in PYTHON_FILES:
    path = ROOT / rel
    assert path.is_file(), f"Fichier Python requis absent : {rel}"
    ast.parse(path.read_text(encoding="utf-8"), filename=rel)


# ---------------------------------------------------------------------------
# Shell syntax.
# ---------------------------------------------------------------------------

SHELL_FILES = [
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

for rel in SHELL_FILES:
    path = ROOT / rel
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


# ---------------------------------------------------------------------------
# Release package identity.
# ---------------------------------------------------------------------------

for rel in (
    "config/default-current.toml",
    "config/default-1.5.1.toml",
    "cvp_access_installer/release.env",
    "cvp_access_installer/systemd/cvp-web.service.in",
    "docs/CVP_ACCESS_1_7_MAPPING_UI_DESIGN.md",
):
    assert (ROOT / rel).is_file(), f"Fichier requis absent : {rel}"

frontend = read("cvp_access_1_7.py")
assert 'VERSION = "1.7.0-RC1"' in frontend
assert "CVP_RECORDER_ENABLED" in frontend
assert "cvp_access_1_5_2" in frontend

release_manifest = read("cvp_access_installer/release.env")
assert "CVP_RELEASE_VERSION=1.7.0-RC1" in release_manifest
assert "CVP_RELEASE_FRONTEND=cvp_access_1_7.py" in release_manifest
assert "CVP_RELEASE_UPGRADER=upgrade_1_7_0.sh" in release_manifest
assert "CVP_RELEASE_VERIFIER=VERIFY_PACKAGE_170.py" in release_manifest

upgrade = read("cvp_access_installer/upgrade_1_7_0.sh")
assert 'CVP_FRONTEND_SOURCE="cvp_access_1_7.py"' in upgrade
assert 'CVP_TARGET_VERSION="1.7.0-RC1"' in upgrade
assert "CVP_SKIP_KEYBOARD_MIGRATION=1" in upgrade
assert "cvp_keyboard_profiles.py" in upgrade
assert "--init" in upgrade

shared_upgrade = read("cvp_access_installer/upgrade_1_5_1_base.sh")
for name in (
    "cvp_action_catalog.py",
    "cvp_keyboard_layout.py",
    "cvp_keyboard_profiles.py",
    "cvp_keyboard_web.py",
    "default-keyboard-current.toml",
):
    assert name in shared_upgrade, f"Déploiement runtime manquant : {name}"
assert "CVP_SKIP_KEYBOARD_MIGRATION" in shared_upgrade

legacy_migration = read("cvp_access_installer/upgrade_1_5_1.sh")
assert "CVP_SKIP_KEYBOARD_MIGRATION" in legacy_migration

fresh_install = read("cvp_access_installer/install.sh")
assert "config/default.toml" not in fresh_install
assert "config/default-current.toml" in fresh_install
assert "cvp_action_catalog.py" in fresh_install
assert "cvp_keyboard_layout.py" in fresh_install


# ---------------------------------------------------------------------------
# Canonical mapping and action catalogue.
# ---------------------------------------------------------------------------

with (ROOT / "config/default-current.toml").open("rb") as handle:
    factory = tomllib.load(handle)

assert factory["general"]["caps_lock_layer"] is False
factory_keys = factory["keys"]
assert isinstance(factory_keys, dict)
assert len(factory_keys) == 83

catalog_source = read("cvp_action_catalog.py")
catalog_actions = set(
    re.findall(
        r'^\s{4}"([a-z][a-z0-9_]+)"\s*:\s*_m\(',
        catalog_source,
        flags=re.M,
    )
)
assigned_actions = {
    value.split(":", 1)[0]
    for value in factory_keys.values()
    if isinstance(value, str)
}
missing_catalog = sorted(assigned_actions - catalog_actions)
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
    assert action in catalog_actions

keyboard = read("cvp_keyboard.py")
assert "from cvp_action_catalog import ACTION_SPECS, ActionSpec, action_help" in keyboard
assert "SHARED_MODIFIER_ORDER" in keyboard
assert 'source=Path("<builtin-1.7>")' in keyboard
assert "caps_lock_layer=False" in keyboard
assert "An empty [keys] table is valid in 1.7" in keyboard
assert "if not config.issues:" in keyboard

builtin_block = re.search(
    r"BUILTIN_BINDINGS\s*=\s*\{(.*?)\n\}",
    keyboard,
    flags=re.S,
)
assert builtin_block, "BUILTIN_BINDINGS absent"
builtin_pairs = dict(
    re.findall(
        r'^\s*"([^"]+)"\s*:\s*"([^"]+)"\s*,?\s*$',
        builtin_block.group(1),
        flags=re.M,
    )
)
assert builtin_pairs == factory_keys, (
    "Le mapping built-in diffère du profil usine canonique"
)

for wrapper_name in ("cvp_access_1_5_1_base.py", "cvp_access_1_5_2.py"):
    wrapper_source = read(wrapper_name)
    assert "NEW_ACTION_SPECS" not in wrapper_source
    assert "ACTION_SPECS.update" not in wrapper_source
    assert "from cvp_keyboard import ActionSpec" not in wrapper_source


# ---------------------------------------------------------------------------
# Profiles, safe apply and external-change handling.
# ---------------------------------------------------------------------------

profiles = read("cvp_keyboard_profiles.py")
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
    "def save_active_external_as_profile(",
    "runuser",
    "systemctl",
    "cvp-access.service",
):
    assert marker.lower() in profiles.lower(), (
        f"Gestion profils incomplète : {marker}"
    )
assert 'if "CTRL" in parts[:-1]' in profiles
assert "active_revision != current_revision" in profiles
assert "MAX_BACKUPS = 10" in profiles
assert "ancienne configuration a été restaurée" in profiles
assert "_write_user_file(ACTIVE_CONFIG" in profiles


# ---------------------------------------------------------------------------
# Graphical editor and portal routing/auth.
# ---------------------------------------------------------------------------

web_helper = read("cvp_keyboard_web.py")
assert r"\n" not in web_helper, (
    "L'éditeur Web contient un \\n littéral susceptible de casser le JavaScript/HTML"
)
assert "adminPassword" not in web_helper
assert "Mot de passe maintenance pour enregistrer/activer" not in web_helper
assert "admin_password" not in web_helper
assert "minmax(260px,330px)" in web_helper
for marker in (
    "KEYBOARD_EDITOR",
    "/api/keyboard/apply",
    "/api/keyboard/profiles/create",
    "/api/keyboard/profiles/duplicate",
    "/api/keyboard/profiles/rename",
    "/api/keyboard/profiles/delete",
    "/api/keyboard/profiles/activate",
    "/api/keyboard/profiles/import-active",
    "Enregistrer sous",
    "Activer cette configuration",
    "Enregistrer comme nouveau profil",
    "Rechercher une fonction",
    "Modifications en attente",
    "Choisir : ",
    "confirmRecoveryKey",
):
    assert marker in web_helper, f"Éditeur Web incomplet : {marker}"

portal = read("cvp_access_installer/tools/cvp_web.py")
assert '</a>\\n        <a class="btn secondary" href="/keyboard-map">' not in portal
for marker in (
    "/keyboard",
    "/api/keyboard/catalog",
    "/api/keyboard/config",
    "/api/keyboard/profiles",
    "/api/keyboard/profiles/import-active",
    "/api/keyboard/select",
    "Configuration clavier",
):
    assert marker in portal, f"Portail 1.7 incomplet : {marker}"

assert "keyboard_write_authorized" not in portal
assert "Mot de passe maintenance requis pour modifier le clavier" not in portal
keyboard_write_pos = portal.index("keyboard_editor_writes")
global_auth_pos = portal.index("if not request_authorized(payload):")
assert keyboard_write_pos < global_auth_pos, (
    "Les écritures clavier doivent rester libres du code maintenance"
)
assert 'path.startswith("/api/keyboard/")' not in portal

maintenance = read("cvp_access_installer/install_maintenance.sh")
assert "MAINTENANCE_PASSWORD_FILE" in maintenance
assert "CVP_MAINTENANCE_PASSWORD" in maintenance
assert "maintenance-password" in maintenance
assert 'Admin key : stored in $MAINTENANCE_PASSWORD_FILE' in maintenance


# ---------------------------------------------------------------------------
# Doctor, printable map and shared physical layout.
# ---------------------------------------------------------------------------

doctor = read("cvp_access_installer/tools/cvp_doctor.py")
assert "profil personnalisé" in doctor
assert "Configuration clavier" in doctor
assert "default-keyboard-current.toml" in doctor
assert "expected_caps" not in doctor

keyboard_map = read("cvp_keyboard_map.py")
assert "from cvp_action_catalog import ACTION_CATALOG, action_text" in keyboard_map
assert "from cvp_keyboard_layout import (" in keyboard_map
assert "ACTION_LABELS =" not in keyboard_map
assert "KEY_LABELS = {" not in keyboard_map
assert "ROWS = [" not in keyboard_map
assert "Layout accessibilité 1.7 RC1" in keyboard_map
assert "Layout accessibilité 1.6.1 RC2" not in keyboard_map

layout = read("cvp_keyboard_layout.py")
assert '("CTRL", "ALT", "ALTGR", "SHIFT", "META", "CAPS")' in layout
assert '"F14": "Morceau précédent / Recorder"' in layout
assert '"F15": "Dictaphone MIDI"' in layout
assert '"F16": "Morceau suivant / Recorder"' in layout
assert "EDITOR_NAV_ROWS" in layout
assert '("INSERT",1),("HOME",1),("PAGEUP",1)' in layout
assert '("LEFT",1),("DOWN",1),("RIGHT",1)' in layout

service = read("cvp_access_installer/systemd/cvp-web.service.in")
# Global portal auth remains in development mode for RC1. Keyboard/profile
# editing is intentionally code-free on the already LAN-restricted portal.
assert "Environment=CVP_WEB_REQUIRE_AUTH=0" in service


# ---------------------------------------------------------------------------
# Functional profile/editor self-test with a local evdev stub.
# ---------------------------------------------------------------------------

self_test = subprocess.run(
    ["python3", str(ROOT / "TEST_KEYBOARD_PROFILES_170.py")],
    capture_output=True,
    text=True,
    check=False,
)
assert self_test.returncode == 0, (
    "Self-test clavier/profils en échec:\n"
    + self_test.stdout
    + "\n"
    + self_test.stderr
)
assert "keyboard/profile self-test: OK" in self_test.stdout

print("CVP Access 1.7.0 RC1 package: OK")
