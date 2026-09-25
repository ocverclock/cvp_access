#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/upgrade_1_7_0.sh"
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
RUNTIME_DIR="/opt/cvp-access"

CVP_USER="${CVP_USER:-${SUDO_USER:-}}"
if [[ -z "$CVP_USER" || "$CVP_USER" == "root" ]]; then
    CVP_USER="$(stat -c '%U' "$REPO_DIR")"
fi
CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"

echo "[CVP Access] Upgrade runtime -> 1.7.0-RC1"
echo "[CVP Access] Existing keyboard mappings are authoritative."

install -d -m 0755 "$RUNTIME_DIR"
install -m 0644 "$REPO_DIR/cvp_access_1_5_2.py" "$RUNTIME_DIR/cvp_access_1_5_2.py"

export CVP_FRONTEND_SOURCE="cvp_access_1_7.py"
export CVP_TARGET_VERSION="1.7.0-RC1"
export CVP_SKIP_KEYBOARD_MIGRATION=1

bash "$INSTALLER_DIR/upgrade_1_5_1.sh"

echo "[CVP Access] Initialising named keyboard profiles"
env HOME="$CVP_HOME" CVP_USER="$CVP_USER" CVP_RUNTIME_DIR="$RUNTIME_DIR" CVP_CONFIG_DIR="/etc/cvp-access" python3 "$RUNTIME_DIR/cvp_keyboard_profiles.py" --init

systemctl restart cvp-web.service
systemctl restart cvp-access.service

echo "[CVP Access] 1.7.0-RC1 installed."
echo "Keyboard editor: http://cvp-access.local/keyboard"
