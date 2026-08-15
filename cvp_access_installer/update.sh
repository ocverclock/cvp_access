#!/usr/bin/env bash
set -Eeuo pipefail

log()  { printf '\n[CVP Access update] %s\n' "$*"; }
die()  { printf '\n[CVP Access update] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || die "Run with: sudo ./update.sh"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
CVP_USER="${CVP_USER:-${SUDO_USER:-$(stat -c '%U' "$SCRIPT_DIR")}}"
[[ "$CVP_USER" != "root" ]] || CVP_USER="$(getent passwd 1000 | cut -d: -f1)"
getent passwd "$CVP_USER" >/dev/null || die "Unable to determine normal user."
CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"
RUNTIME_DIR="/opt/cvp-access"
VOICE_DIR="$CVP_HOME/cvp_voice"
PIPER_DIR="$CVP_HOME/.local/share/cvp-access/piper-env"
PIPER_VOICE_DIR="$CVP_HOME/piper-voices"
PIPER_MODEL="$PIPER_VOICE_DIR/fr_FR-siwis-medium.onnx"

log "Updating operating system"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get full-upgrade -y

if [[ -d "$SCRIPT_DIR/.git" ]]; then
    log "Updating CVP Access from GitHub"
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" git -C "$SCRIPT_DIR" pull --ff-only
else
    log "No .git directory: source update skipped"
fi

log "Updating Piper"
runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
    "$PIPER_DIR/bin/python" -m pip install --upgrade -r "$SCRIPT_DIR/requirements-piper.txt"

log "Refreshing runtime copy"
SOURCE_MAIN="$SCRIPT_DIR/cvp_access.py"
[[ -f "$SOURCE_MAIN" ]] || SOURCE_MAIN="$SCRIPT_DIR/cvp_access_v1.4.1.py"
[[ -f "$SOURCE_MAIN" ]] || die "cvp_access.py not found."
install -m 0755 "$SOURCE_MAIN" "$RUNTIME_DIR/cvp_access.py"
if grep -Fq '/home/pi/cvp_voice' "$RUNTIME_DIR/cvp_access.py"; then
    sed -i "s#/home/pi/cvp_voice#$VOICE_DIR#g" "$RUNTIME_DIR/cvp_access.py"
fi

log "Generating any new voice prompts"
for generator in "$SCRIPT_DIR/tools/generate_track_voices.py" "$SCRIPT_DIR/tools/generate_value_voices.py"; do
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" CVP_VOICE_DIR="$VOICE_DIR" CVP_PIPER_MODEL="$PIPER_MODEL" \
        "$PIPER_DIR/bin/python" "$generator"
done

systemctl daemon-reload
systemctl restart cvp-access.service || true

log "Running CVP Doctor"
runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" CVP_PROJECT_DIR="$SCRIPT_DIR" CVP_RUNTIME_DIR="$RUNTIME_DIR" CVP_VOICE_DIR="$VOICE_DIR" CVP_PIPER_MODEL="$PIPER_MODEL" \
    python3 "$SCRIPT_DIR/tools/cvp_doctor.py" || true

apt-get autoremove -y
apt-get clean

if [[ -f /var/run/reboot-required ]]; then
    printf '\nA reboot is required: sudo reboot\n'
fi
