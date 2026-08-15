#!/usr/bin/env bash
set -Eeuo pipefail

INSTALLER_VERSION="0.2.1"
REQUIRED_CODENAME="${CVP_REQUIRED_CODENAME:-trixie}"
REQUIRED_ARCH="${CVP_REQUIRED_ARCH:-arm64}"
MIN_FREE_KB="${CVP_MIN_FREE_KB:-2097152}"   # 2 GiB
PIPER_VOICE="${CVP_PIPER_VOICE:-fr_FR-siwis-medium}"

log()  { printf '\n[CVP Access] %s\n' "$*"; }
warn() { printf '\n[CVP Access] WARNING: %s\n' "$*" >&2; }
die()  { printf '\n[CVP Access] ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || die "Run with: sudo bash cvp_access_installer/install.sh"

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# Locate the repository root without invoking Git as root.
# A repository cloned by the normal user can trigger Git's safe.directory
# protection when inspected by root.
if [[ -d "$INSTALLER_DIR/../.git" || -f "$INSTALLER_DIR/../README.md" ]]; then
    REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
elif [[ -d "$INSTALLER_DIR/.git" ]]; then
    REPO_DIR="$INSTALLER_DIR"
else
    REPO_DIR="$INSTALLER_DIR"
fi

# Prefer the user who invoked sudo. Fall back to repository owner, then UID 1000.
CVP_USER="${CVP_USER:-${SUDO_USER:-}}"
if [[ -z "$CVP_USER" || "$CVP_USER" == "root" ]]; then
    owner="$(stat -c '%U' "$REPO_DIR" 2>/dev/null || true)"
    if [[ -n "$owner" && "$owner" != "root" ]]; then
        CVP_USER="$owner"
    else
        CVP_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
    fi
fi
[[ -n "$CVP_USER" ]] || die "Unable to determine the normal user. Set CVP_USER explicitly."
getent passwd "$CVP_USER" >/dev/null || die "User '$CVP_USER' does not exist."

CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"
RUNTIME_DIR="/opt/cvp-access"
VOICE_DIR="$CVP_HOME/cvp_voice"
PIPER_DIR="$CVP_HOME/.local/share/cvp-access/piper-env"
PIPER_VOICE_DIR="$CVP_HOME/piper-voices"
PIPER_MODEL="$PIPER_VOICE_DIR/${PIPER_VOICE}.onnx"
SERVICE_FILE="/etc/systemd/system/cvp-access.service"
SAMBA_FRAGMENT="/etc/samba/cvp-access.conf"

log "CVP Access installer $INSTALLER_VERSION"
printf 'User        : %s\n' "$CVP_USER"
printf 'Home        : %s\n' "$CVP_HOME"
printf 'Repository  : %s\n' "$REPO_DIR"
printf 'Installer   : %s\n' "$INSTALLER_DIR"
printf 'Runtime     : %s\n' "$RUNTIME_DIR"
printf 'Voice bank  : %s\n' "$VOICE_DIR"

# -----------------------------------------------------------------------------
# OS preflight
# -----------------------------------------------------------------------------
[[ -r /etc/os-release ]] || die "/etc/os-release is missing."
# shellcheck disable=SC1091
source /etc/os-release
CODENAME="${VERSION_CODENAME:-${DEBIAN_CODENAME:-unknown}}"
ARCH="$(dpkg --print-architecture)"

log "System detected: ${PRETTY_NAME:-unknown} / $ARCH"
[[ "$CODENAME" == "$REQUIRED_CODENAME" ]] || die \
    "This release supports Debian/Raspberry Pi OS '$REQUIRED_CODENAME' (found '$CODENAME'). Re-image with a supported Raspberry Pi OS Lite release rather than forcing a major in-place upgrade."
[[ "$ARCH" == "$REQUIRED_ARCH" ]] || die \
    "This release expects $REQUIRED_ARCH (found $ARCH). Use Raspberry Pi OS Lite 64-bit."

AVAILABLE_KB="$(df -Pk / | awk 'NR==2 {print $4}')"
[[ "$AVAILABLE_KB" =~ ^[0-9]+$ ]] || die "Unable to determine free disk space."
(( AVAILABLE_KB >= MIN_FREE_KB )) || die \
    "Less than $((MIN_FREE_KB / 1024)) MiB free on /. Free disk space before installation."

# -----------------------------------------------------------------------------
# Full OS update
# -----------------------------------------------------------------------------
log "Updating Raspberry Pi OS"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get full-upgrade -y

# -----------------------------------------------------------------------------
# Packages
# -----------------------------------------------------------------------------
PACKAGE_FILE="$INSTALLER_DIR/apt-packages.txt"
[[ -f "$PACKAGE_FILE" ]] || die "Missing dependency list: $PACKAGE_FILE"
mapfile -t APT_PACKAGES < <(grep -Ev '^[[:space:]]*(#|$)' "$PACKAGE_FILE")
(( ${#APT_PACKAGES[@]} > 0 )) || die "APT dependency list is empty."

log "Installing CVP Access dependencies"
apt-get install -y "${APT_PACKAGES[@]}"

# -----------------------------------------------------------------------------
# User permissions
# -----------------------------------------------------------------------------
log "Configuring audio/input permissions"
getent group audio >/dev/null || groupadd --system audio
getent group input >/dev/null || groupadd --system input
usermod -aG audio,input "$CVP_USER"

# -----------------------------------------------------------------------------
# Friendly hostname on a stock image
# -----------------------------------------------------------------------------
CURRENT_HOSTNAME="$(hostnamectl --static 2>/dev/null || hostname)"
if [[ "$CURRENT_HOSTNAME" == "raspberrypi" ]]; then
    log "Setting hostname to cvp-access"
    hostnamectl set-hostname cvp-access
    if grep -qE '^[[:space:]]*127\.0\.1\.1[[:space:]]+raspberrypi([[:space:]]|$)' /etc/hosts; then
        sed -i -E 's/^([[:space:]]*127\.0\.1\.1[[:space:]]+)raspberrypi([[:space:]]|$)/\1cvp-access\2/' /etc/hosts
    fi
fi

# -----------------------------------------------------------------------------
# Locate current application source
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
[[ -n "$SOURCE_MAIN" && -f "$SOURCE_MAIN" ]] || die \
    "No cvp_access.py or versioned cvp_access_v*.py was found at repository root."

log "Using application source: $(basename "$SOURCE_MAIN")"

# -----------------------------------------------------------------------------
# Runtime copy
# -----------------------------------------------------------------------------
log "Installing runtime files"
install -d -m 0755 "$RUNTIME_DIR"
install -m 0755 "$SOURCE_MAIN" "$RUNTIME_DIR/cvp_access.py"

# Transitional compatibility with releases that hard-coded /home/pi.
# Only the runtime copy is changed; source files in Git are never rewritten.
if grep -Fq '/home/pi/cvp_voice' "$RUNTIME_DIR/cvp_access.py"; then
    sed -i "s#/home/pi/cvp_voice#$VOICE_DIR#g" "$RUNTIME_DIR/cvp_access.py"
fi

# -----------------------------------------------------------------------------
# Piper
# -----------------------------------------------------------------------------
log "Installing Piper in an isolated Python environment"
install -d -o "$CVP_USER" -g "$CVP_USER" \
    "$CVP_HOME/.local/share/cvp-access" \
    "$PIPER_VOICE_DIR" \
    "$VOICE_DIR"

if [[ ! -x "$PIPER_DIR/bin/python" ]]; then
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" python3 -m venv "$PIPER_DIR"
fi

runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
    "$PIPER_DIR/bin/python" -m pip install --upgrade pip

PIPER_REQUIREMENTS="$INSTALLER_DIR/requirements-piper.txt"
[[ -f "$PIPER_REQUIREMENTS" ]] || die "Missing $PIPER_REQUIREMENTS"
runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
    "$PIPER_DIR/bin/python" -m pip install -r "$PIPER_REQUIREMENTS"

if [[ ! -f "$PIPER_MODEL" || ! -f "$PIPER_MODEL.json" ]]; then
    log "Downloading Piper voice $PIPER_VOICE"
    runuser -u "$CVP_USER" -- env HOME="$CVP_HOME" \
        "$PIPER_DIR/bin/python" -m piper.download_voices \
        "$PIPER_VOICE" --data-dir "$PIPER_VOICE_DIR"
fi

# -----------------------------------------------------------------------------
# Voice bank
# -----------------------------------------------------------------------------
log "Generating missing voice prompts"
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

# -----------------------------------------------------------------------------
# systemd
# -----------------------------------------------------------------------------
log "Installing systemd service"
SERVICE_TEMPLATE="$INSTALLER_DIR/systemd/cvp-access.service.in"
[[ -f "$SERVICE_TEMPLATE" ]] || die "Missing systemd template."
sed \
    -e "s#@CVP_USER@#$CVP_USER#g" \
    -e "s#@CVP_HOME@#$CVP_HOME#g" \
    -e "s#@PROJECT_DIR@#$RUNTIME_DIR#g" \
    -e "s#@VOICE_DIR@#$VOICE_DIR#g" \
    "$SERVICE_TEMPLATE" > "$SERVICE_FILE"
chmod 0644 "$SERVICE_FILE"
systemctl daemon-reload

# -----------------------------------------------------------------------------
# Samba
# -----------------------------------------------------------------------------
log "Configuring Samba repository share"
SAMBA_TEMPLATE="$INSTALLER_DIR/samba/cvp-access.conf.in"
[[ -f "$SAMBA_TEMPLATE" ]] || die "Missing Samba template."
sed \
    -e "s#@CVP_USER@#$CVP_USER#g" \
    -e "s#@PROJECT_DIR@#$REPO_DIR#g" \
    "$SAMBA_TEMPLATE" > "$SAMBA_FRAGMENT"
chmod 0644 "$SAMBA_FRAGMENT"

INCLUDE_LINE="include = $SAMBA_FRAGMENT"
grep -Fqx "$INCLUDE_LINE" /etc/samba/smb.conf || printf '\n%s\n' "$INCLUDE_LINE" >> /etc/samba/smb.conf

testparm -s >/dev/null || die "Samba configuration validation failed."

if ! runuser -u "$CVP_USER" -- test -r "$REPO_DIR"; then
    warn "The repository is not readable by $CVP_USER. Samba access may fail."
fi

if ! pdbedit -L 2>/dev/null | cut -d: -f1 | grep -Fxq "$CVP_USER"; then
    if [[ -t 0 && -r /dev/tty ]]; then
        printf '\nCreate the Samba password for %s.\n' "$CVP_USER"
        while true; do
            IFS= read -r -s -p "Samba password: " SMB_PASS </dev/tty
            printf '\n'
            IFS= read -r -s -p "Confirm password: " SMB_PASS2 </dev/tty
            printf '\n'
            [[ -n "$SMB_PASS" ]] || { warn "Password cannot be empty."; continue; }
            [[ "$SMB_PASS" == "$SMB_PASS2" ]] || { warn "Passwords do not match."; continue; }
            printf '%s\n%s\n' "$SMB_PASS" "$SMB_PASS" | smbpasswd -a -s "$CVP_USER"
            unset SMB_PASS SMB_PASS2
            break
        done
    else
        warn "No interactive terminal: Samba user was not created. Run later: sudo smbpasswd -a $CVP_USER"
    fi
fi

# -----------------------------------------------------------------------------
# Services
# -----------------------------------------------------------------------------
log "Enabling services"
systemctl enable --now ssh
systemctl enable --now avahi-daemon
systemctl enable --now smbd
systemctl enable --now nmbd 2>/dev/null || true
systemctl restart smbd

systemctl enable cvp-access.service
systemctl restart cvp-access.service || true

# -----------------------------------------------------------------------------
# Diagnostic
# -----------------------------------------------------------------------------
log "Running CVP Doctor"
DOCTOR="$INSTALLER_DIR/tools/cvp_doctor.py"
if [[ -f "$DOCTOR" ]]; then
    runuser -u "$CVP_USER" -- env \
        HOME="$CVP_HOME" \
        CVP_PROJECT_DIR="$REPO_DIR" \
        CVP_RUNTIME_DIR="$RUNTIME_DIR" \
        CVP_VOICE_DIR="$VOICE_DIR" \
        CVP_PIPER_MODEL="$PIPER_MODEL" \
        python3 "$DOCTOR" || true
fi

# Keep installed packages intact. Do not autoremove on a machine we did not provision.
apt-get clean

HOST_NOW="$(hostnamectl --static 2>/dev/null || hostname)"
log "Installation complete"
printf 'SSH   : ssh %s@%s.local\n' "$CVP_USER" "$HOST_NOW"
printf 'Samba : \\\\%s.local\\CVP_access\n' "$HOST_NOW"
printf 'Status: systemctl status cvp-access\n'
printf 'Doctor: python3 %s/tools/cvp_doctor.py\n' "$INSTALLER_DIR"

if [[ -f /var/run/reboot-required ]]; then
    warn "A reboot is required by the OS update."
else
    warn "A reboot is recommended after the first installation."
fi

if [[ -t 0 && -r /dev/tty ]]; then
    printf '\n'
    IFS= read -r -p "Reboot now? [Y/n] " answer </dev/tty || true
    case "${answer:-Y}" in
        n|N|no|NO|non|NON) printf 'Reboot postponed.\n' ;;
        *) reboot ;;
    esac
fi
