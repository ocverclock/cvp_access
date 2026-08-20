#!/usr/bin/env bash
set -Eeuo pipefail

UPDATE_VERSION="0.3.2"
REQUIRED_CODENAME="${CVP_REQUIRED_CODENAME:-trixie}"
REQUIRED_ARCH="${CVP_REQUIRED_ARCH:-arm64}"
PIPER_VOICE="${CVP_PIPER_VOICE:-fr_FR-siwis-medium}"

log()  { printf '\n[CVP Access update] %s\n' "$*"; }
warn() { printf '\n[CVP Access update] WARNING: %s\n' "$*" >&2; }
die()  { printf '\n[CVP Access update] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || die "Run with: sudo bash cvp_access_installer/update.sh"

# Run from a temporary copy so `git pull` can safely replace update.sh itself.
if [[ "${CVP_UPDATE_FROM_TMP:-0}" != "1" ]]; then
    ORIGINAL_INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
    TMP_UPDATE="$(mktemp /tmp/cvp-access-update.XXXXXX)"
    cp -- "${BASH_SOURCE[0]}" "$TMP_UPDATE"
    chmod 0700 "$TMP_UPDATE"
    exec env \
        CVP_UPDATE_FROM_TMP=1 \
        CVP_INSTALLER_DIR="$ORIGINAL_INSTALLER_DIR" \
        CVP_USER="${CVP_USER:-${SUDO_USER:-}}" \
        bash "$TMP_UPDATE" "$@"
fi

INSTALLER_DIR="${CVP_INSTALLER_DIR:?Missing installer directory}"

# Locate the repository without invoking Git as root.
if [[ -d "$INSTALLER_DIR/../.git" || -f "$INSTALLER_DIR/../README.md" ]]; then
    REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
elif [[ -d "$INSTALLER_DIR/.git" ]]; then
    REPO_DIR="$INSTALLER_DIR"
else
    REPO_DIR="$INSTALLER_DIR"
fi

CVP_USER="${CVP_USER:-}"
if [[ -z "$CVP_USER" || "$CVP_USER" == "root" ]]; then
    owner="$(stat -c '%U' "$REPO_DIR" 2>/dev/null || true)"
    if [[ -n "$owner" && "$owner" != "root" ]]; then
        CVP_USER="$owner"
    else
        CVP_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
    fi
fi
[[ -n "$CVP_USER" ]] || die "Unable to determine normal user."
getent passwd "$CVP_USER" >/dev/null || die "User '$CVP_USER' does not exist."

CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"
RUNTIME_DIR="/opt/cvp-access"
VOICE_DIR="$CVP_HOME/cvp_voice"
PIPER_DIR="$CVP_HOME/.local/share/cvp-access/piper-env"
PIPER_VOICE_DIR="$CVP_HOME/piper-voices"
PIPER_MODEL="$PIPER_VOICE_DIR/${PIPER_VOICE}.onnx"
SERVICE_FILE="/etc/systemd/system/cvp-access.service"
SAMBA_FRAGMENT="/etc/samba/cvp-access.conf"
CONFIG_DIR="/etc/cvp-access"
CONFIG_FILE="$CONFIG_DIR/keyboard.toml"

log "CVP Access updater $UPDATE_VERSION"
printf 'Repository : %s\n' "$REPO_DIR"
printf 'Installer  : %s\n' "$INSTALLER_DIR"

git_user() {
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" git "$@"
}

# -----------------------------------------------------------------------------
# Git first: future dependency/configuration changes become available this run.
# Every Git operation runs as the repository owner to avoid safe.directory /
# dubious ownership failures caused by sudo/root.
# -----------------------------------------------------------------------------
if git_user -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if [[ -n "$(git_user -C "$REPO_DIR" status --porcelain)" ]]; then
        warn "Local repository changes detected. GitHub pull skipped to avoid overwriting work."
        git_user -C "$REPO_DIR" status --short
    else
        log "Updating CVP Access from GitHub"
        git_user -C "$REPO_DIR" pull --ff-only
    fi
else
    warn "No Git repository detected. Source update skipped."
fi

# -----------------------------------------------------------------------------
# OS safety and update
# -----------------------------------------------------------------------------
[[ -r /etc/os-release ]] || die "/etc/os-release is missing."
# shellcheck disable=SC1091
source /etc/os-release
CODENAME="${VERSION_CODENAME:-${DEBIAN_CODENAME:-unknown}}"
ARCH="$(dpkg --print-architecture)"
[[ "$CODENAME" == "$REQUIRED_CODENAME" ]] || die \
    "Unsupported OS codename '$CODENAME'; expected '$REQUIRED_CODENAME'."
[[ "$ARCH" == "$REQUIRED_ARCH" ]] || die \
    "Unsupported architecture '$ARCH'; expected '$REQUIRED_ARCH'."

log "Updating operating system"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get full-upgrade -y

# Reinstall declared packages so newly added project dependencies are handled.
PACKAGE_FILE="$INSTALLER_DIR/apt-packages.txt"
[[ -f "$PACKAGE_FILE" ]] || die "Missing dependency list: $PACKAGE_FILE"
mapfile -t APT_PACKAGES < <(grep -Ev '^[[:space:]]*(#|$)' "$PACKAGE_FILE")
log "Checking project dependencies"
apt-get install -y "${APT_PACKAGES[@]}"

usermod -aG audio,input "$CVP_USER"

# Read the Piper voice selected in the preserved customer configuration before
# repairing/downloading Piper.
if [[ -f "$CONFIG_FILE" ]]; then
    CONFIG_PIPER_VOICE="$(runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
        python3 -c 'import re,sys,tomllib; d=tomllib.load(open(sys.argv[1],"rb")); v=d.get("speech",{}).get("voice",""); print(v if isinstance(v,str) and re.fullmatch(r"[A-Za-z0-9_.-]+",v) else "")' \
        "$CONFIG_FILE" 2>/dev/null || true)"
    if [[ -n "$CONFIG_PIPER_VOICE" ]]; then
        PIPER_VOICE="$CONFIG_PIPER_VOICE"
        PIPER_MODEL="$PIPER_VOICE_DIR/${PIPER_VOICE}.onnx"
    fi
fi

# -----------------------------------------------------------------------------
# Piper can repair a deleted/incomplete venv
# -----------------------------------------------------------------------------
log "Updating Piper"
install -d -o "$CVP_USER" -g "$CVP_USER" \
    "$CVP_HOME/.local/share/cvp-access" "$PIPER_VOICE_DIR" "$VOICE_DIR"

if [[ ! -x "$PIPER_DIR/bin/python" ]]; then
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" python3 -m venv "$PIPER_DIR"
fi

runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
    "$PIPER_DIR/bin/python" -m pip install --upgrade pip
runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
    "$PIPER_DIR/bin/python" -m pip install --upgrade -r "$INSTALLER_DIR/requirements-piper.txt"

if [[ ! -f "$PIPER_MODEL" || ! -f "$PIPER_MODEL.json" ]]; then
    log "Downloading missing Piper voice $PIPER_VOICE"
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
        "$PIPER_DIR/bin/python" -m piper.download_voices \
        "$PIPER_VOICE" --data-dir "$PIPER_VOICE_DIR"
fi

# -----------------------------------------------------------------------------
# Runtime
# -----------------------------------------------------------------------------
SOURCE_MAIN=""
if [[ -f "$REPO_DIR/cvp_access.py" ]]; then
    SOURCE_MAIN="$REPO_DIR/cvp_access.py"
else
    SOURCE_MAIN="$(
        find "$REPO_DIR" -maxdepth 1 -type f -iname 'cvp_access_v*.py' -printf '%p\n' \
        | sort -V \
        | tail -n 1
    )"
fi
[[ -n "$SOURCE_MAIN" && -f "$SOURCE_MAIN" ]] || die "CVP Access main program not found."

log "Refreshing runtime from $(basename "$SOURCE_MAIN")"
install -d -m 0755 "$RUNTIME_DIR"
install -m 0755 "$SOURCE_MAIN" "$RUNTIME_DIR/cvp_access.py"

# v1.5 configurable keyboard frontend.
# The MIDI/SysEx engine remains the validated v1.4.1 implementation.
if [[ "$(basename "$SOURCE_MAIN")" == "cvp_access_v1.5.py" ]]; then
    [[ -f "$REPO_DIR/cvp_access_v1.4.1.py" ]] || die "v1.5 requires cvp_access_v1.4.1.py."
    [[ -f "$REPO_DIR/cvp_keyboard.py" ]] || die "v1.5 requires cvp_keyboard.py."
    [[ -f "$REPO_DIR/cvp_song.py" ]] || die "v1.5 requires cvp_song.py."
    [[ -f "$REPO_DIR/cvp_speech.py" ]] || die "v1.5 requires cvp_speech.py."
    [[ -f "$REPO_DIR/cvp_piper_worker.py" ]] || die "v1.5 requires cvp_piper_worker.py."
    [[ -f "$REPO_DIR/config/default.toml" ]] || die "v1.5 requires config/default.toml."

    install -m 0644 "$REPO_DIR/cvp_access_v1.4.1.py" "$RUNTIME_DIR/cvp_access_v1.4.1.py"
    install -m 0644 "$REPO_DIR/cvp_keyboard.py" "$RUNTIME_DIR/cvp_keyboard.py"
    install -m 0644 "$REPO_DIR/cvp_song.py" "$RUNTIME_DIR/cvp_song.py"
    install -m 0644 "$REPO_DIR/cvp_speech.py" "$RUNTIME_DIR/cvp_speech.py"
    install -m 0644 "$REPO_DIR/cvp_piper_worker.py" "$RUNTIME_DIR/cvp_piper_worker.py"
    install -m 0644 "$REPO_DIR/config/default.toml" "$RUNTIME_DIR/default-keyboard.toml"
    if [[ -f "$INSTALLER_DIR/tools/generate_configured_voices.py" ]]; then
        install -m 0755 "$INSTALLER_DIR/tools/generate_configured_voices.py" "$RUNTIME_DIR/generate_configured_voices.py"
    fi
    if [[ -f "$REPO_DIR/cvp_keyboard_map.py" ]]; then
        install -m 0755 "$REPO_DIR/cvp_keyboard_map.py" "$RUNTIME_DIR/cvp_keyboard_map.py"
    fi

    log "Refreshing configurable keyboard support"
    install -d -o "$CVP_USER" -g "$CVP_USER" -m 0770 "$CONFIG_DIR"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        install -o "$CVP_USER" -g "$CVP_USER" -m 0660 \
            "$REPO_DIR/config/default.toml" "$CONFIG_FILE"
        log "Created default keyboard configuration: $CONFIG_FILE"
    else
        log "Preserving customer keyboard configuration: $CONFIG_FILE"
    fi
fi
# -----------------------------------------------------------------------------
# Optional keyboard map
# -----------------------------------------------------------------------------
if [[ -f "$RUNTIME_DIR/cvp_keyboard_map.py" && -f "$CONFIG_FILE" ]]; then
    log "Generating keyboard map HTML"
    if ! runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
        python3 "$RUNTIME_DIR/cvp_keyboard_map.py" \
        --config "$CONFIG_FILE" \
        --output "$CONFIG_DIR/keyboard-map.html"; then
        warn "Keyboard map generation failed; runtime installation continues."
    fi
fi

if grep -Fq '/home/pi/cvp_voice' "$RUNTIME_DIR/cvp_access.py"; then
    sed -i "s#/home/pi/cvp_voice#$VOICE_DIR#g" "$RUNTIME_DIR/cvp_access.py"
fi

# -----------------------------------------------------------------------------
# Voice bank
# -----------------------------------------------------------------------------
log "Generating any new voice prompts"
CONFIGURED_GENERATOR="$INSTALLER_DIR/tools/generate_configured_voices.py"
if [[ -f "$CONFIG_FILE" && -f "$CONFIGURED_GENERATOR" && "$(basename "$SOURCE_MAIN")" == "cvp_access_v1.5.py" ]]; then
    runuser -u "$CVP_USER" -- env \
        HOME="$CVP_HOME" \
        CVP_VOICE_DIR="$VOICE_DIR" \
        CVP_PIPER_MODEL="$PIPER_MODEL" \
        "$PIPER_DIR/bin/python" "$CONFIGURED_GENERATOR" --config "$CONFIG_FILE"
else
    for generator in \
        "$INSTALLER_DIR/tools/generate_track_voices.py" \
        "$INSTALLER_DIR/tools/generate_value_voices.py"; do
        [[ -f "$generator" ]] || die "Missing voice generator: $generator"
        runuser -u "$CVP_USER" -- env \
            HOME="$CVP_HOME" \
            CVP_VOICE_DIR="$VOICE_DIR" \
            CVP_PIPER_MODEL="$PIPER_MODEL" \
            "$PIPER_DIR/bin/python" "$generator"
    done
fi

# -----------------------------------------------------------------------------
# Refresh systemd configuration
# -----------------------------------------------------------------------------
log "Refreshing systemd service"
sed \
    -e "s#@CVP_USER@#$CVP_USER#g" \
    -e "s#@CVP_HOME@#$CVP_HOME#g" \
    -e "s#@PROJECT_DIR@#$RUNTIME_DIR#g" \
    -e "s#@VOICE_DIR@#$VOICE_DIR#g" \
    "$INSTALLER_DIR/systemd/cvp-access.service.in" > "$SERVICE_FILE"
chmod 0644 "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable cvp-access.service

# -----------------------------------------------------------------------------
# Refresh Samba configuration
# -----------------------------------------------------------------------------
log "Refreshing Samba share"
sed \
    -e "s#@CVP_USER@#$CVP_USER#g" \
    -e "s#@PROJECT_DIR@#$REPO_DIR#g" \
    -e "s#@CONFIG_DIR@#$CONFIG_DIR#g" \
    "$INSTALLER_DIR/samba/cvp-access.conf.in" > "$SAMBA_FRAGMENT"
chmod 0644 "$SAMBA_FRAGMENT"

INCLUDE_LINE="include = $SAMBA_FRAGMENT"
grep -Fqx "$INCLUDE_LINE" /etc/samba/smb.conf || printf '\n%s\n' "$INCLUDE_LINE" >> /etc/samba/smb.conf
testparm -s >/dev/null || die "Samba configuration validation failed."

systemctl enable --now ssh
systemctl enable --now avahi-daemon
systemctl enable --now smbd
systemctl restart smbd
systemctl restart cvp-access.service || true

# -----------------------------------------------------------------------------
# Diagnostic
# -----------------------------------------------------------------------------
log "Running CVP Doctor"
runuser -u "$CVP_USER" -- env \
    HOME="$CVP_HOME" \
    CVP_PROJECT_DIR="$REPO_DIR" \
    CVP_RUNTIME_DIR="$RUNTIME_DIR" \
    CVP_VOICE_DIR="$VOICE_DIR" \
    CVP_PIPER_MODEL="$PIPER_MODEL" \
    CVP_CONFIG_FILE="$CONFIG_FILE" \
    python3 "$INSTALLER_DIR/tools/cvp_doctor.py" || true

apt-get clean

if [[ -f /var/run/reboot-required ]]; then
    warn "A reboot is required by the OS update: sudo reboot"
fi

rm -f -- "${BASH_SOURCE[0]}" 2>/dev/null || true
log "Update complete"
