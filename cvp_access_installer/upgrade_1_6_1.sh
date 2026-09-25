#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/upgrade_1_6_1.sh"
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
RUNTIME_DIR="/opt/cvp-access"

# 1.6.1 is a consolidation release. Keep the validated compatibility stack
# intact and change only the top-level frontend / release identity.
install -d -m 0755 "$RUNTIME_DIR"
install -m 0644 \
    "$REPO_DIR/cvp_access_1_5_2.py" \
    "$RUNTIME_DIR/cvp_access_1_5_2.py"

# Development probe must never remain enabled in a normal release.
systemctl unset-environment CVP_RECORDER_PROBE >/dev/null 2>&1 || true

export CVP_FRONTEND_SOURCE="cvp_access_1_6_1.py"
export CVP_TARGET_VERSION="1.6.1-RC1"

exec bash "$INSTALLER_DIR/upgrade_1_5_1.sh"
