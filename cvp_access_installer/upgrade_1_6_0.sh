#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/upgrade_1_6_0.sh"
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
RUNTIME_DIR="/opt/cvp-access"

# 1.6 builds on the complete 1.5.2 frontend, which itself uses the 1.5.1
# compatibility layer. The 1.5.1 upgrader installs that lower layer.
install -d -m 0755 "$RUNTIME_DIR"
install -m 0644 \
    "$REPO_DIR/cvp_access_1_5_2.py" \
    "$RUNTIME_DIR/cvp_access_1_5_2.py"

systemctl unset-environment CVP_RECORDER_PROBE >/dev/null 2>&1 || true

export CVP_FRONTEND_SOURCE="cvp_access_1_6_0.py"
export CVP_TARGET_VERSION="1.6.0-RC1"

exec bash "$INSTALLER_DIR/upgrade_1_5_1.sh"
