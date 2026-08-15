#!/usr/bin/env bash
set -Eeuo pipefail

PURGE=0
[[ "${1:-}" == "--purge" ]] && PURGE=1
[[ ${EUID} -eq 0 ]] || { echo "Run with: sudo bash cvp_access_installer/uninstall.sh [--purge]" >&2; exit 1; }

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if REPO_DIR="$(git -C "$INSTALLER_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
    :
else
    REPO_DIR="$(cd "$INSTALLER_DIR/.." 2>/dev/null && pwd -P || printf '%s' "$INSTALLER_DIR")"
fi

CVP_USER="${CVP_USER:-${SUDO_USER:-}}"
if [[ -z "$CVP_USER" || "$CVP_USER" == "root" ]]; then
    owner="$(stat -c '%U' "$REPO_DIR" 2>/dev/null || true)"
    if [[ -n "$owner" && "$owner" != "root" ]]; then
        CVP_USER="$owner"
    else
        CVP_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
    fi
fi
[[ -n "$CVP_USER" ]] || { echo "Unable to determine normal user." >&2; exit 1; }
CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"

systemctl disable --now cvp-access.service 2>/dev/null || true
rm -f /etc/systemd/system/cvp-access.service
systemctl daemon-reload

SAMBA_FRAGMENT="/etc/samba/cvp-access.conf"
if [[ -f /etc/samba/smb.conf ]]; then
    sed -i '\#^[[:space:]]*include[[:space:]]*=[[:space:]]*/etc/samba/cvp-access\.conf[[:space:]]*$#d' /etc/samba/smb.conf
fi
rm -f "$SAMBA_FRAGMENT"
systemctl restart smbd 2>/dev/null || true

rm -rf /opt/cvp-access

if (( PURGE )); then
    rm -rf \
        "$CVP_HOME/cvp_voice" \
        "$CVP_HOME/piper-voices" \
        "$CVP_HOME/.local/share/cvp-access" \
        "$CVP_HOME/.cache/cvp_voice_cache" \
        "$CVP_HOME/.cache/cvp_voice_sequences"
    echo "Runtime, Piper, generated voices and CVP voice caches removed."
else
    echo "Runtime removed. Project source, Piper and generated voices were preserved."
    echo "Use --purge to remove generated/Piper data too."
fi

echo "System packages, SSH, Samba, Avahi and Linux group memberships were intentionally left installed."
