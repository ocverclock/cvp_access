#!/usr/bin/env python3
"""Named keyboard profiles and safe activation for CVP Access 1.7."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path

from cvp_keyboard import normalize_combo, parse_action, read_config_file


CONFIG_DIR = Path(os.environ.get("CVP_CONFIG_DIR", "/etc/cvp-access"))
ACTIVE_CONFIG = CONFIG_DIR / "keyboard.toml"
PROFILES_DIR = CONFIG_DIR / "profiles"
BACKUPS_DIR = CONFIG_DIR / "backups"
REGISTRY_FILE = CONFIG_DIR / "keyboard-profiles.json"
KEYBOARD_MAP = CONFIG_DIR / "keyboard-map.html"
RUNTIME_DIR = Path(os.environ.get("CVP_RUNTIME_DIR", "/opt/cvp-access"))
CVP_USER = os.environ.get("CVP_USER", "pi")

RESERVED_KEYS = {"F14", "F15", "F16"}
REGISTRY_SCHEMA = 1
MAX_BACKUPS = 10


class ProfileError(RuntimeError):
    pass


class RevisionConflict(ProfileError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_revision(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return ""


def _atomic_write(path: Path, data: bytes, mode: int = 0o660):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _run(args, timeout=20, env=None):
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _factory_source() -> Path:
    candidates = [
        RUNTIME_DIR / "default-keyboard-current.toml",
        RUNTIME_DIR / "default-keyboard-1.5.1.toml",
        Path(__file__).resolve().with_name("default-keyboard-current.toml"),
        Path(__file__).resolve().parent / "config" / "default-current.toml",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise ProfileError("Profil usine CVP Access introuvable")


def _load_registry():
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("schema") != REGISTRY_SCHEMA:
        return None
    profiles = data.get("profiles")
    if not isinstance(profiles, list):
        return None
    return data


def _save_registry(data):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    _atomic_write(REGISTRY_FILE, body, 0o660)


def _profile_entry(registry, profile_id):
    for item in registry.get("profiles", []):
        if item.get("id") == profile_id:
            return item
    raise ProfileError("Configuration inconnue")


def _profile_path(entry):
    name = entry.get("file", "")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.toml", name):
        raise ProfileError("Chemin de profil invalide")
    path = PROFILES_DIR / name
    try:
        path.relative_to(PROFILES_DIR)
    except ValueError as exc:
        raise ProfileError("Chemin de profil invalide") from exc
    return path


def _clean_name(name):
    if not isinstance(name, str):
        raise ProfileError("Nom de configuration invalide")
    name = " ".join(name.strip().split())
    if not name or len(name) > 80:
        raise ProfileError("Le nom doit contenir entre 1 et 80 caractères")
    if any(ord(ch) < 32 for ch in name):
        raise ProfileError("Le nom contient un caractère interdit")
    return name


def ensure_store():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    registry = _load_registry()
    if registry is not None:
        return registry

    factory_source = _factory_source()
    factory_data = factory_source.read_bytes()
    factory_path = PROFILES_DIR / "factory.toml"
    _atomic_write(factory_path, factory_data, 0o640)

    if ACTIVE_CONFIG.is_file():
        current_data = ACTIVE_CONFIG.read_bytes()
    else:
        current_data = factory_data
        _atomic_write(ACTIVE_CONFIG, current_data, 0o660)

    standard_id = "standard"
    standard_path = PROFILES_DIR / "standard.toml"
    _atomic_write(standard_path, current_data, 0o660)

    registry = {
        "schema": REGISTRY_SCHEMA,
        "active_profile_id": standard_id,
        "profiles": [
            {
                "id": "factory",
                "name": "Profil usine CVP Access",
                "file": "factory.toml",
                "protected": True,
            },
            {
                "id": standard_id,
                "name": "Standard",
                "file": "standard.toml",
                "protected": False,
            },
        ],
    }
    _save_registry(registry)
    return registry


def list_profiles():
    registry = ensure_store()
    active_id = registry.get("active_profile_id")
    active_revision = file_revision(ACTIVE_CONFIG)
    items = []
    for entry in registry["profiles"]:
        path = _profile_path(entry)
        revision = file_revision(path)
        items.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "protected": bool(entry.get("protected")),
                "active": entry["id"] == active_id,
                "revision": revision,
                "matches_active_file": bool(
                    entry["id"] == active_id and revision and revision == active_revision
                ),
            }
        )
    return {
        "active_profile_id": active_id,
        "active_revision": active_revision,
        "profiles": items,
    }


def _toml_keys(data: bytes):
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ProfileError(f"TOML invalide : {exc}") from exc
    keys = parsed.get("keys", {})
    if not isinstance(keys, dict):
        raise ProfileError("[keys] doit être une table TOML")
    return keys


def validate_bytes(data: bytes):
    fd, tmp_name = tempfile.mkstemp(prefix="cvp-keyboard-validate-", suffix=".toml")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_bytes(data)
        try:
            config = read_config_file(tmp)
        except Exception as exc:
            raise ProfileError(f"Configuration invalide : {exc}") from exc
        if config.issues:
            raise ProfileError("Configuration invalide : " + " ; ".join(config.issues))

        for combo in config.bindings:
            parts = combo.split("+")
            key = parts[-1]
            if key in RESERVED_KEYS:
                raise ProfileError(f"{key} est réservée au Dictaphone MIDI")
            if "CTRL" in parts[:-1]:
                raise ProfileError("CTRL est réservé à l'aide vocale")
        return config
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def get_profile(profile_id=None):
    registry = ensure_store()
    if profile_id is None:
        profile_id = registry.get("active_profile_id")
    entry = _profile_entry(registry, profile_id)
    path = _profile_path(entry)
    if not path.is_file():
        raise ProfileError("Fichier de configuration introuvable")
    data = path.read_bytes()
    validate_bytes(data)
    keys = _toml_keys(data)
    normalized = {}
    for combo, action in keys.items():
        if not isinstance(combo, str) or not isinstance(action, str):
            continue
        try:
            normalized[normalize_combo(combo)] = parse_action(action).text
        except ValueError:
            continue

    active_revision = file_revision(ACTIVE_CONFIG)
    profile_revision = _sha256_bytes(data)
    return {
        "id": entry["id"],
        "name": entry["name"],
        "protected": bool(entry.get("protected")),
        "active": entry["id"] == registry.get("active_profile_id"),
        "revision": profile_revision,
        "active_file_revision": active_revision,
        "active_file_matches_profile": (
            entry["id"] == registry.get("active_profile_id")
            and profile_revision == active_revision
        ),
        "bindings": normalized,
    }


def _render_keys_section(bindings):
    lines = ["[keys]"]
    for combo in sorted(bindings):
        action = bindings[combo]
        combo_q = json.dumps(combo, ensure_ascii=False)
        action_q = json.dumps(action, ensure_ascii=False)
        lines.append(f"{combo_q} = {action_q}")
    return "\n".join(lines) + "\n"


def _replace_keys_section(data: bytes, bindings):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProfileError("Le profil n'est pas en UTF-8") from exc

    match = re.search(r"(?m)^\[keys\][ \t]*$", text)
    if not match:
        raise ProfileError("Section [keys] absente")

    next_section = re.search(r"(?m)^\[[^\]\n]+\][ \t]*$", text[match.end():])
    if next_section:
        end = match.end() + next_section.start()
        suffix = text[end:]
    else:
        suffix = ""

    prefix = text[:match.start()]
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    body = _render_keys_section(bindings)
    if suffix and not suffix.startswith("\n"):
        body += "\n"
    return (prefix + body + suffix).encode("utf-8")


def _apply_changes_to_bytes(data: bytes, changes):
    raw_keys = _toml_keys(data)
    bindings = {}
    for combo, action in raw_keys.items():
        if not isinstance(combo, str) or not isinstance(action, str):
            raise ProfileError("[keys] contient une affectation non textuelle")
        try:
            normalized = normalize_combo(combo)
            invocation = parse_action(action)
        except ValueError as exc:
            raise ProfileError(str(exc)) from exc
        bindings[normalized] = invocation.text

    if not isinstance(changes, list) or len(changes) > 200:
        raise ProfileError("Liste de modifications invalide")

    for change in changes:
        if not isinstance(change, dict):
            raise ProfileError("Modification invalide")
        raw_combo = change.get("combo")
        raw_action = change.get("action")
        if not isinstance(raw_combo, str):
            raise ProfileError("Combinaison invalide")

        try:
            combo = normalize_combo(raw_combo)
        except ValueError as exc:
            raise ProfileError(str(exc)) from exc

        parts = combo.split("+")
        key = parts[-1]
        if key in RESERVED_KEYS:
            raise ProfileError(f"{key} est réservée au Dictaphone MIDI")
        if "CTRL" in parts[:-1]:
            raise ProfileError("CTRL est réservé à l'aide vocale")

        if raw_action is None:
            bindings.pop(combo, None)
            continue
        if not isinstance(raw_action, str):
            raise ProfileError("Action invalide")
        try:
            invocation = parse_action(raw_action)
        except ValueError as exc:
            raise ProfileError(str(exc)) from exc
        bindings[combo] = invocation.text

    result = _replace_keys_section(data, bindings)
    validate_bytes(result)
    return result


def create_profile(name, source_id=None):
    registry = ensure_store()
    name = _clean_name(name)
    if any(item["name"].casefold() == name.casefold() for item in registry["profiles"]):
        raise ProfileError("Une configuration porte déjà ce nom")

    if source_id is None:
        source_id = registry.get("active_profile_id")
    source = _profile_entry(registry, source_id)
    source_path = _profile_path(source)
    data = source_path.read_bytes()
    validate_bytes(data)

    profile_id = "p-" + secrets.token_hex(8)
    filename = profile_id + ".toml"
    _atomic_write(PROFILES_DIR / filename, data, 0o660)
    registry["profiles"].append(
        {"id": profile_id, "name": name, "file": filename, "protected": False}
    )
    _save_registry(registry)
    return get_profile(profile_id)


def duplicate_profile(source_id, name):
    return create_profile(name, source_id=source_id)


def rename_profile(profile_id, name):
    registry = ensure_store()
    entry = _profile_entry(registry, profile_id)
    if entry.get("protected"):
        raise ProfileError("Le profil usine ne peut pas être renommé")
    name = _clean_name(name)
    if any(
        item["id"] != profile_id and item["name"].casefold() == name.casefold()
        for item in registry["profiles"]
    ):
        raise ProfileError("Une configuration porte déjà ce nom")
    entry["name"] = name
    _save_registry(registry)
    return get_profile(profile_id)


def delete_profile(profile_id):
    registry = ensure_store()
    entry = _profile_entry(registry, profile_id)
    if entry.get("protected"):
        raise ProfileError("Le profil usine ne peut pas être supprimé")
    if registry.get("active_profile_id") == profile_id:
        raise ProfileError("La configuration active ne peut pas être supprimée")
    path = _profile_path(entry)
    registry["profiles"] = [item for item in registry["profiles"] if item["id"] != profile_id]
    _save_registry(registry)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return list_profiles()


def _trim_backups():
    backups = sorted(BACKUPS_DIR.glob("keyboard-*.toml"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[MAX_BACKUPS:]:
        try:
            old.unlink()
        except OSError:
            pass


def _generate_runtime_assets():
    map_script = RUNTIME_DIR / "cvp_keyboard_map.py"
    if map_script.is_file():
        rc, out, err = _run(
            [
                "python3", str(map_script),
                "--config", str(ACTIVE_CONFIG),
                "--output", str(KEYBOARD_MAP),
            ],
            timeout=20,
        )
        if rc != 0:
            raise ProfileError("Régénération de la carte clavier impossible : " + (err or out))

    home = Path(os.path.expanduser(f"~{CVP_USER}"))
    piper_python = home / ".local/share/cvp-access/piper-env/bin/python"
    generators = [
        RUNTIME_DIR / "generate_configured_voices.py",
        RUNTIME_DIR / "generate_151_voices.py",
    ]
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CVP_RUNTIME_DIR"] = str(RUNTIME_DIR)
    env.setdefault("CVP_CONFIG_FILE", str(ACTIVE_CONFIG))

    for generator in generators:
        if not generator.is_file():
            continue
        if not piper_python.is_file():
            raise ProfileError("Environnement Piper absent pour régénérer les annonces")
        rc, out, err = _run(
            [str(piper_python), str(generator), "--config", str(ACTIVE_CONFIG)],
            timeout=180,
            env=env,
        )
        if rc != 0:
            raise ProfileError(
                f"Régénération vocale impossible ({generator.name}) : " + (err or out)
            )


def _verify_active(expected_revision):
    try:
        config = read_config_file(ACTIVE_CONFIG)
    except Exception as exc:
        raise ProfileError(f"Le fichier actif ne peut pas être relu : {exc}") from exc
    if config.issues:
        raise ProfileError("Le fichier actif contient des erreurs : " + " ; ".join(config.issues))
    if file_revision(ACTIVE_CONFIG) != expected_revision:
        raise ProfileError("La révision active ne correspond pas à la configuration validée")
    rc, out, err = _run(["systemctl", "is-active", "cvp-access.service"], timeout=8)
    if rc != 0 or out.strip() != "active":
        raise ProfileError("cvp-access.service n'est pas actif" + (f" : {err}" if err else ""))
    if (RUNTIME_DIR / "cvp_keyboard_map.py").is_file() and not KEYBOARD_MAP.is_file():
        raise ProfileError("La carte clavier n'a pas été régénérée")


def _activate_bytes(new_data: bytes):
    validate_bytes(new_data)
    expected_revision = _sha256_bytes(new_data)
    previous = ACTIVE_CONFIG.read_bytes() if ACTIVE_CONFIG.is_file() else b""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = BACKUPS_DIR / f"keyboard-{stamp}.toml"
    if previous:
        _atomic_write(backup, previous, 0o640)

    try:
        _atomic_write(ACTIVE_CONFIG, new_data, 0o660)
        _generate_runtime_assets()
        rc, out, err = _run(["systemctl", "restart", "cvp-access.service"], timeout=15)
        if rc != 0:
            raise ProfileError("Redémarrage de CVP Access impossible : " + (err or out))
        time.sleep(0.6)
        _verify_active(expected_revision)
        _trim_backups()
        return {
            "ok": True,
            "revision": expected_revision,
            "backup": str(backup) if previous else None,
        }
    except Exception as exc:
        if previous:
            _atomic_write(ACTIVE_CONFIG, previous, 0o660)
            try:
                _generate_runtime_assets()
            except Exception:
                pass
            try:
                _run(["systemctl", "restart", "cvp-access.service"], timeout=15)
            except Exception:
                pass
        raise ProfileError(
            "Activation impossible ; l'ancienne configuration a été restaurée. "
            + str(exc)
        ) from exc


def activate_profile(profile_id):
    registry = ensure_store()
    entry = _profile_entry(registry, profile_id)
    data = _profile_path(entry).read_bytes()
    result = _activate_bytes(data)
    registry["active_profile_id"] = profile_id
    _save_registry(registry)
    result["profile"] = get_profile(profile_id)
    return result


def save_profile(profile_id, revision, changes):
    registry = ensure_store()
    entry = _profile_entry(registry, profile_id)
    if entry.get("protected"):
        raise ProfileError("Le profil usine est en lecture seule ; utilisez « Enregistrer sous »")
    path = _profile_path(entry)
    current = path.read_bytes()
    current_revision = _sha256_bytes(current)
    if not isinstance(revision, str) or revision != current_revision:
        raise RevisionConflict("La configuration a changé depuis l'ouverture de l'éditeur")

    new_data = _apply_changes_to_bytes(current, changes)
    new_revision = _sha256_bytes(new_data)

    if registry.get("active_profile_id") == profile_id:
        active_revision = file_revision(ACTIVE_CONFIG)
        if active_revision != current_revision:
            raise RevisionConflict(
                "keyboard.toml a été modifié hors du portail depuis l'ouverture"
            )
        _activate_bytes(new_data)

    _atomic_write(path, new_data, 0o660)
    result = get_profile(profile_id)
    result["saved_revision"] = new_revision
    return result


def save_active_external_as_profile(name):
    if not ACTIVE_CONFIG.is_file():
        raise ProfileError("Configuration active absente")
    validate_bytes(ACTIVE_CONFIG.read_bytes())
    profile = create_profile(name)
    registry = ensure_store()
    entry = _profile_entry(registry, profile["id"])
    _atomic_write(_profile_path(entry), ACTIVE_CONFIG.read_bytes(), 0o660)
    return get_profile(profile["id"])
