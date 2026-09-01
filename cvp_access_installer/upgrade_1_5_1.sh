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
CONFIG_FILE="/etc/cvp-access/keyboard.toml"
VOICE_DIR="$CVP_HOME/cvp_voice"
PIPER_DIR="$CVP_HOME/.local/share/cvp-access/piper-env"
PIPER_MODEL_DIR="$CVP_HOME/piper-voices"

echo
echo "[CVP Access] Upgrade runtime -> 1.5.1-RC1-dev"

required=(
    cvp_access_1_5_1.py
    cvp_access_v1.5.py
    cvp_access_v1.4.1.py
    cvp_keyboard.py
    cvp_song.py
    cvp_song_151.py
    cvp_speech.py
    cvp_speech_151.py
    cvp_piper_worker.py
    cvp_midi.py
    cvp_yamaha.py
    cvp_registration.py
    cvp_style.py
    cvp_voice.py
    config/default-1.5.1.toml
    cvp_access_installer/tools/generate_151_voices.py
    cvp_access_installer/tools/cvp_doctor_151.py
)

for item in "${required[@]}"; do
    [[ -f "$REPO_DIR/$item" ]] || {
        echo "Missing: $item" >&2
        exit 1
    }
done

systemctl stop cvp-access.service 2>/dev/null || true

install -d -m 0755 "$RUNTIME_DIR"

install -m 0755 \
    "$REPO_DIR/cvp_access_1_5_1.py" \
    "$RUNTIME_DIR/cvp_access.py"

for item in \
    cvp_access_v1.5.py \
    cvp_access_v1.4.1.py \
    cvp_keyboard.py \
    cvp_song.py \
    cvp_song_151.py \
    cvp_speech.py \
    cvp_speech_151.py \
    cvp_piper_worker.py \
    cvp_midi.py \
    cvp_yamaha.py \
    cvp_registration.py \
    cvp_style.py \
    cvp_voice.py
do
    install -m 0644 \
        "$REPO_DIR/$item" \
        "$RUNTIME_DIR/$item"
done

install -m 0644 \
    "$REPO_DIR/config/default-1.5.1.toml" \
    "$RUNTIME_DIR/default-keyboard-1.5.1.toml"

install -m 0755 \
    "$REPO_DIR/cvp_access_installer/tools/generate_151_voices.py" \
    "$RUNTIME_DIR/generate_151_voices.py"

install -m 0755 \
    "$REPO_DIR/cvp_access_installer/tools/cvp_doctor_151.py" \
    "$RUNTIME_DIR/cvp_doctor_151.py"

# ------------------------------------------------------------------
# Complète la configuration cliente sans écraser ses affectations.
# ------------------------------------------------------------------
if [[ ! -f "$CONFIG_FILE" ]]; then
    install -d -o "$CVP_USER" -g "$CVP_USER" -m 0770 \
        "$(dirname "$CONFIG_FILE")"
    install -o "$CVP_USER" -g "$CVP_USER" -m 0660 \
        "$REPO_DIR/config/default-1.5.1.toml" \
        "$CONFIG_FILE"
else
    python3 - "$CONFIG_FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

bindings = {
    "CAPS+F1": "announce_style_name",
    "CAPS+F2": "announce_song_name",
    "CAPS+F3": "announce_song_length",
    "CAPS+F4": "sync_start_toggle",
    "CAPS+F5": "guide_toggle",
    "CAPS+F6": "stream_lights_toggle",
    "CAPS+F7": "metronome_toggle",
    "CAPS+TOP1": "style_intro:1",
    "CAPS+TOP2": "style_intro:2",
    "CAPS+TOP3": "style_intro:3",
    "CAPS+TOP4": "style_main:1",
    "CAPS+TOP5": "style_main:2",
    "CAPS+TOP6": "style_main:3",
    "CAPS+TOP7": "style_main:4",
    "CAPS+TOP8": "style_break",
    "CAPS+A": "style_fill:1",
    "CAPS+Z": "style_fill:2",
    "CAPS+E": "style_fill:3",
    "CAPS+R": "style_fill:4",
    "CAPS+T": "style_ending:1",
    "CAPS+Y": "style_ending:2",
    "CAPS+U": "style_ending:3",
    "CAPS+Q": "registration_recall:1",
    "CAPS+S": "registration_recall:2",
    "CAPS+D": "registration_recall:3",
    "CAPS+F": "registration_recall:4",
    "CAPS+G": "registration_recall:5",
    "CAPS+H": "registration_recall:6",
    "CAPS+J": "registration_recall:7",
    "CAPS+K": "registration_recall:8",
}

lines = text.splitlines()
keys_start = None
keys_end = len(lines)

for i, line in enumerate(lines):
    if line.strip() == "[keys]":
        keys_start = i
        continue
    if (
        keys_start is not None
        and i > keys_start
        and line.strip().startswith("[")
        and line.strip().endswith("]")
    ):
        keys_end = i
        break

if keys_start is None:
    lines += ["", "[keys]"]
    keys_start = len(lines) - 1
    keys_end = len(lines)

section = "\n".join(lines[keys_start + 1:keys_end])

to_add = []
for combo, action in bindings.items():
    # Ne jamais écraser une combinaison déjà personnalisée.
    if f'"{combo}"' in section or f"{combo} =" in section:
        continue
    to_add.append(f'"{combo}" = "{action}"')

if to_add:
    block = [
        "",
        "# CVP Access 1.5.1 - couche CAPS ajoutée automatiquement",
        *to_add,
    ]
    lines[keys_end:keys_end] = block
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Added {len(to_add)} CAPS bindings.")
else:
    print("No CAPS binding added; configuration already contains them/conflicts.")
PY

    chown "$CVP_USER:$CVP_USER" "$CONFIG_FILE"
fi

# Vérification syntaxique dans le runtime.
python3 -m py_compile \
    "$RUNTIME_DIR/cvp_access.py" \
    "$RUNTIME_DIR/cvp_access_v1.5.py" \
    "$RUNTIME_DIR/cvp_access_v1.4.1.py" \
    "$RUNTIME_DIR/cvp_keyboard.py" \
    "$RUNTIME_DIR/cvp_song.py" \
    "$RUNTIME_DIR/cvp_song_151.py" \
    "$RUNTIME_DIR/cvp_speech.py" \
    "$RUNTIME_DIR/cvp_speech_151.py" \
    "$RUNTIME_DIR/cvp_midi.py" \
    "$RUNTIME_DIR/cvp_yamaha.py" \
    "$RUNTIME_DIR/cvp_registration.py" \
    "$RUNTIME_DIR/cvp_style.py" \
    "$RUNTIME_DIR/cvp_voice.py"

# Modèle Piper sélectionné par keyboard.toml.
VOICE_NAME="$(
    runuser -u "$CVP_USER" -- \
    python3 - "$CONFIG_FILE" <<'PY'
import sys, tomllib
with open(sys.argv[1], "rb") as f:
    d = tomllib.load(f)
print(d.get("speech", {}).get("voice", "fr_FR-siwis-medium"))
PY
)"
PIPER_MODEL="$PIPER_MODEL_DIR/${VOICE_NAME}.onnx"

# Banque existante v1.5, puis compléments 1.5.1.
if [[ -x "$PIPER_DIR/bin/python" ]]; then
    if [[ -x "$RUNTIME_DIR/generate_configured_voices.py" ]]; then
        runuser -u "$CVP_USER" -- env \
            HOME="$CVP_HOME" \
            CVP_VOICE_DIR="$VOICE_DIR" \
            CVP_PIPER_MODEL="$PIPER_MODEL" \
            "$PIPER_DIR/bin/python" \
            "$RUNTIME_DIR/generate_configured_voices.py" \
            --config "$CONFIG_FILE"
    fi

    runuser -u "$CVP_USER" -- env \
        HOME="$CVP_HOME" \
        CVP_RUNTIME_DIR="$RUNTIME_DIR" \
        CVP_VOICE_DIR="$VOICE_DIR" \
        CVP_PIPER_MODEL="$PIPER_MODEL" \
        "$PIPER_DIR/bin/python" \
        "$RUNTIME_DIR/generate_151_voices.py" \
        --config "$CONFIG_FILE"
else
    echo "WARNING: Piper environment absent; WAV generation skipped." >&2
fi

runuser -u "$CVP_USER" -- env \
    HOME="$CVP_HOME" \
    CVP_RUNTIME_DIR="$RUNTIME_DIR" \
    CVP_VOICE_DIR="$VOICE_DIR" \
    CVP_CONFIG_FILE="$CONFIG_FILE" \
    python3 "$RUNTIME_DIR/cvp_doctor_151.py"

systemctl restart cvp-access.service

echo
echo "[CVP Access] 1.5.1-RC1-dev installed."
echo "Rollback: sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py && sudo systemctl restart cvp-access"
