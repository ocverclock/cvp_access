#!/usr/bin/env bash
set -Eeuo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/install_1_5_1.sh"
    exit 1
}
bash "$DIR/install.sh"
bash "$DIR/upgrade_1_5_1.sh"
