#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/upgrade_1_5_1.sh"
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
CVP_USER="${CVP_USER:-${SUDO_USER:-}}"
if [[ -z "$CVP_USER" || "$CVP_USER" == "root" ]]; then
    CVP_USER="$(stat -c '%U' "$REPO_DIR")"
fi
CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"
RUNTIME_DIR="/opt/cvp-access"
CONFIG_DIR="/etc/cvp-access"
CONFIG_FILE="$CONFIG_DIR/keyboard.toml"
VOICE_DIR="$CVP_HOME/cvp_voice"
PIPER_DIR="$CVP_HOME/.local/share/cvp-access/piper-env"
PIPER_MODEL_DIR="$CVP_HOME/piper-voices"

echo
echo "[CVP Access] Upgrade runtime -> 1.5.1-RC3"

required=(
    cvp_access_1_5_1.py cvp_access_v1.5.py cvp_access_v1.4.1.py
    cvp_keyboard.py cvp_keyboard_map.py cvp_song.py cvp_song_151.py
    cvp_speech.py cvp_speech_151.py cvp_piper_worker.py cvp_midi.py
    cvp_yamaha.py cvp_registration.py cvp_style.py cvp_voice.py cvp_voice_names.py
    config/default-1.5.1.toml
    cvp_access_installer/tools/generate_configured_voices.py
    cvp_access_installer/tools/generate_151_voices.py
    cvp_access_installer/tools/cvp_doctor_151.py
)
for item in "${required[@]}"; do
    [[ -f "$REPO_DIR/$item" ]] || { echo "Missing: $item" >&2; exit 1; }
done

systemctl stop cvp-access.service 2>/dev/null || true
install -d -m 0755 "$RUNTIME_DIR"
install -m 0755 "$REPO_DIR/cvp_access_1_5_1.py" "$RUNTIME_DIR/cvp_access.py"
for item in cvp_access_v1.5.py cvp_access_v1.4.1.py cvp_keyboard.py cvp_song.py cvp_song_151.py cvp_speech.py cvp_speech_151.py cvp_piper_worker.py cvp_midi.py cvp_yamaha.py cvp_registration.py cvp_style.py cvp_voice.py cvp_voice_names.py; do
    install -m 0644 "$REPO_DIR/$item" "$RUNTIME_DIR/$item"
done
install -m 0755 "$REPO_DIR/cvp_keyboard_map.py" "$RUNTIME_DIR/cvp_keyboard_map.py"
install -m 0644 "$REPO_DIR/config/default-1.5.1.toml" "$RUNTIME_DIR/default-keyboard-1.5.1.toml"
install -m 0755 "$REPO_DIR/cvp_access_installer/tools/generate_configured_voices.py" "$RUNTIME_DIR/generate_configured_voices.py"
install -m 0755 "$REPO_DIR/cvp_access_installer/tools/generate_151_voices.py" "$RUNTIME_DIR/generate_151_voices.py"
install -m 0755 "$REPO_DIR/cvp_access_installer/tools/cvp_doctor_151.py" "$RUNTIME_DIR/cvp_doctor_151.py"

if [[ ! -f "$CONFIG_FILE" ]]; then
    install -d -o "$CVP_USER" -g "$CVP_USER" -m 0770 "$CONFIG_DIR"
    install -o "$CVP_USER" -g "$CVP_USER" -m 0660 "$REPO_DIR/config/default-1.5.1.toml" "$CONFIG_FILE"
else
    python3 - "$CONFIG_FILE" <<'PY'
from pathlib import Path
import re, sys, tomllib

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
with path.open("rb") as f:
    before = tomllib.load(f)
keys_before = before.get("keys", {})

# Anciennes affectations RC1 auto-générées : on ne les retire que si elles
# correspondent exactement au profil officiel RC1. Les personnalisations sont conservées.
old_caps = {
    "CAPS+F1": "announce_style_name", "CAPS+F2": "announce_song_name",
    "CAPS+F3": "announce_song_length", "CAPS+F4": "sync_start_toggle",
    "CAPS+F5": "guide_toggle", "CAPS+F6": "stream_lights_toggle",
    "CAPS+F7": "metronome_toggle", "CAPS+TOP1": "style_intro:1",
    "CAPS+TOP2": "style_intro:2", "CAPS+TOP3": "style_intro:3",
    "CAPS+TOP4": "style_main:1", "CAPS+TOP5": "style_main:2",
    "CAPS+TOP6": "style_main:3", "CAPS+TOP7": "style_main:4",
    "CAPS+TOP8": "style_break", "CAPS+A": "style_fill:1",
    "CAPS+Z": "style_fill:2", "CAPS+E": "style_fill:3",
    "CAPS+R": "style_fill:4", "CAPS+T": "style_ending:1",
    "CAPS+Y": "style_ending:2", "CAPS+U": "style_ending:3",
    "CAPS+Q": "registration_recall:1", "CAPS+S": "registration_recall:2",
    "CAPS+D": "registration_recall:3", "CAPS+F": "registration_recall:4",
    "CAPS+G": "registration_recall:5", "CAPS+H": "registration_recall:6",
    "CAPS+J": "registration_recall:7", "CAPS+K": "registration_recall:8",
}
for combo, action in old_caps.items():
    if keys_before.get(combo) == action:
        patt = re.compile(rf'^\s*"?{re.escape(combo)}"?\s*=\s*"{re.escape(action)}"\s*\n?', re.M)
        text = patt.sub("", text)

# Ancien volume Style officiel -> nouveau pas fin ±1 / Maj ±5.
replacements = {
    "PAGEUP": ("style_volume_up", "style_volume_change:1"),
    "PAGEDOWN": ("style_volume_down", "style_volume_change:-1"),
}
for combo, (old, new) in replacements.items():
    if keys_before.get(combo) == old:
        patt = re.compile(rf'^(\s*"?{re.escape(combo)}"?\s*=\s*)"{re.escape(old)}"\s*$', re.M)
        text = patt.sub(rf'\1"{new}"', text)

# Relecture après retrait/remplacement.
path.write_text(text, encoding="utf-8")
with path.open("rb") as f:
    data = tomllib.load(f)
keys = data.get("keys", {})

bindings = {
    "W": "announce_style_name", "X": "announce_song_name",
    "C": "announce_song_length", "V": "sync_start_toggle",
    "B": "guide_toggle", "F7": "metronome_toggle",
    "N": "announce_main_voice_name",
    "COMMA": "announce_layer_voice_name",
    "SEMICOLON": "announce_left_voice_name",
    "PAGEUP": "style_volume_change:1", "SHIFT+PAGEUP": "style_volume_change:5",
    "PAGEDOWN": "style_volume_change:-1", "SHIFT+PAGEDOWN": "style_volume_change:-5",
}

lines = text.splitlines()
keys_start = next((i for i,l in enumerate(lines) if l.strip() == "[keys]"), None)
if keys_start is None:
    lines += ["", "[keys]"]
    keys_start = len(lines)-1
keys_end = len(lines)
for i in range(keys_start+1, len(lines)):
    s = lines[i].strip()
    if s.startswith("[") and s.endswith("]"):
        keys_end = i; break

for combo, action in bindings.items():
    if combo not in keys:
        lines.insert(keys_end, f'"{combo}" = "{action}"')
        keys_end += 1

text = "\n".join(lines) + "\n"
path.write_text(text, encoding="utf-8")

# Caps Lock n'est désactivé que s'il ne reste aucune vraie affectation CAPS personnalisée.
with path.open("rb") as f:
    final = tomllib.load(f)
if not any(str(k).upper().startswith("CAPS+") for k in final.get("keys", {})):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'(?m)^caps_lock_layer\s*=\s*true\s*$', 'caps_lock_layer = false', text, count=1)
    path.write_text(text, encoding="utf-8")
PY
    chown "$CVP_USER:$CVP_USER" "$CONFIG_FILE"
fi

python3 -m py_compile "$RUNTIME_DIR/cvp_access.py" "$RUNTIME_DIR/cvp_access_v1.5.py" "$RUNTIME_DIR/cvp_access_v1.4.1.py" "$RUNTIME_DIR/cvp_keyboard.py" "$RUNTIME_DIR/cvp_keyboard_map.py" "$RUNTIME_DIR/cvp_song.py" "$RUNTIME_DIR/cvp_song_151.py" "$RUNTIME_DIR/cvp_speech.py" "$RUNTIME_DIR/cvp_speech_151.py" "$RUNTIME_DIR/cvp_midi.py" "$RUNTIME_DIR/cvp_yamaha.py" "$RUNTIME_DIR/cvp_registration.py" "$RUNTIME_DIR/cvp_style.py" "$RUNTIME_DIR/cvp_voice.py" "$RUNTIME_DIR/cvp_voice_names.py"

install -d -o "$CVP_USER" -g "$CVP_USER" -m 0770 "$CONFIG_DIR"
runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" python3 "$RUNTIME_DIR/cvp_keyboard_map.py" --config "$CONFIG_FILE" --output "$CONFIG_DIR/keyboard-map.html" || echo "WARNING: keyboard map generation failed; upgrade continues." >&2

VOICE_NAME="$(runuser -u "$CVP_USER" -- python3 - "$CONFIG_FILE" <<'PY'
import sys, tomllib
with open(sys.argv[1], "rb") as f: d=tomllib.load(f)
print(d.get("speech", {}).get("voice", "fr_FR-siwis-medium"))
PY
)"
PIPER_MODEL="$PIPER_MODEL_DIR/${VOICE_NAME}.onnx"

if [[ -x "$PIPER_DIR/bin/python" ]]; then
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" CVP_VOICE_DIR="$VOICE_DIR" CVP_PIPER_MODEL="$PIPER_MODEL" "$PIPER_DIR/bin/python" "$RUNTIME_DIR/generate_configured_voices.py" --config "$CONFIG_FILE"
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" CVP_RUNTIME_DIR="$RUNTIME_DIR" CVP_VOICE_DIR="$VOICE_DIR" CVP_PIPER_MODEL="$PIPER_MODEL" "$PIPER_DIR/bin/python" "$RUNTIME_DIR/generate_151_voices.py" --config "$CONFIG_FILE"
else
    echo "WARNING: Piper environment absent; WAV generation skipped." >&2
fi

runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" CVP_RUNTIME_DIR="$RUNTIME_DIR" CVP_VOICE_DIR="$VOICE_DIR" CVP_CONFIG_FILE="$CONFIG_FILE" python3 "$RUNTIME_DIR/cvp_doctor_151.py"
systemctl restart cvp-access.service

echo
echo "[CVP Access] 1.5.1-RC3 installed."
echo "Rollback: sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py && sudo systemctl restart cvp-access"
