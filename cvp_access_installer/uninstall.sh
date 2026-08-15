#!/usr/bin/env bash
set -Eeuo pipefail

PURGE=0
[[ "${1:-}" == "--purge" ]] && PURGE=1
[[ ${EUID} -eq 0 ]] || { echo "Run with: sudo ./uninstall.sh [--purge]" >&2; exit 1; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
CVP_USER="${CVP_USER:-${SUDO_USER:-$(stat -c '%U' "$SCRIPT_DIR")}}"
[[ "$CVP_USER" != "root" ]] || CVP_USER="$(getent passwd 1000 | cut -d: -f1)"
CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"

systemctl disable --now cvp-access.service 2>/dev/null || true
rm -f /etc/systemd/system/cvp-access.service
systemctl daemon-reload

SAMBA_FRAGMENT="/etc/samba/cvp-access.conf"
if [[ -f /etc/samba/smb.conf ]]; then
    sed -i '\#^include = /etc/samba/cvp-access\.conf$#d' /etc/samba/smb.conf
fi
rm -f "$SAMBA_FRAGMENT"
systemctl restart smbd 2>/dev/null || true

rm -rf /opt/cvp-access

if (( PURGE )); then
    rm -rf "$CVP_HOME/cvp_voice" \
           "$CVP_HOME/piper-voices" \
           "$CVP_HOME/.local/share/cvp-access"
    echo "Runtime, Piper and generated voice data removed."
else
    echo "Runtime removed. Project source, Piper and generated voices were preserved."
    echo "Use --purge to remove generated/Piper data too."
fi

echo "System packages, SSH, Samba and Avahi were intentionally left installed."
