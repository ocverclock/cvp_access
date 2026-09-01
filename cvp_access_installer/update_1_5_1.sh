#!/usr/bin/env bash
set -Eeuo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/update_1_5_1.sh"
    exit 1
}
bash "$DIR/update.sh"
bash "$DIR/upgrade_1_5_1.sh"
