#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/upgrade_1_5_2.sh"
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# 1.5.2 conserve toutes les migrations clavier/configuration de 1.5.1.
# Seul le frontend courant et le numéro de paquet changent.
export CVP_FRONTEND_SOURCE="cvp_access_1_5_2.py"
export CVP_TARGET_VERSION="1.5.2-RC1"

exec bash "$INSTALLER_DIR/upgrade_1_5_1.sh"
