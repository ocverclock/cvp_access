#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID} -eq 0 ]] || {
    echo "Run with: sudo bash cvp_access_installer/install_maintenance.sh" >&2
    exit 1
}

INSTALLER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_DIR="$(cd "$INSTALLER_DIR/.." && pwd -P)"
CVP_USER="${CVP_USER:-${SUDO_USER:-}}"
if [[ -z "$CVP_USER" || "$CVP_USER" == "root" ]]; then
    CVP_USER="$(stat -c '%U' "$REPO_DIR" 2>/dev/null || true)"
fi
[[ -n "$CVP_USER" && "$CVP_USER" != "root" ]] || CVP_USER="$(getent passwd 1000 | cut -d: -f1)"
[[ -n "$CVP_USER" ]] || { echo "Unable to determine CVP user." >&2; exit 1; }

RUNTIME_DIR="/opt/cvp-access"
CONFIG_DIR="/etc/cvp-access"
HOTSPOT="CVP-ACCESS"
DEV="${CVP_WIFI_DEVICE:-wlan0}"
HOTSPOT_IP="10.42.0.1/24"
PASSWORD_FILE="$CONFIG_DIR/hotspot-password"

for command in nmcli python3; do
    command -v "$command" >/dev/null || {
        echo "Missing required command: $command" >&2
        exit 1
    }
done

install -d -m 0755 "$CONFIG_DIR" "$RUNTIME_DIR"

# Preserve the password of an already installed hotspot. Fresh installations
# receive a random password unless CVP_HOTSPOT_PASSWORD is explicitly supplied.
EXISTING_PSK=""
if nmcli -t -f NAME connection show | grep -Fxq "$HOTSPOT"; then
    EXISTING_PSK="$(nmcli --show-secrets -g 802-11-wireless-security.psk connection show "$HOTSPOT" 2>/dev/null || true)"
fi

if [[ -n "${CVP_HOTSPOT_PASSWORD:-}" ]]; then
    HOTSPOT_PASSWORD="$CVP_HOTSPOT_PASSWORD"
elif [[ -n "$EXISTING_PSK" ]]; then
    HOTSPOT_PASSWORD="$EXISTING_PSK"
elif [[ -r "$PASSWORD_FILE" ]]; then
    HOTSPOT_PASSWORD="$(cat "$PASSWORD_FILE")"
else
    HOTSPOT_PASSWORD="$(python3 - <<'PY'
import secrets
alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
print("".join(secrets.choice(alphabet) for _ in range(14)))
PY
)"
fi

if ! nmcli -t -f NAME connection show | grep -Fxq "$HOTSPOT"; then
    nmcli connection add         type wifi         ifname "$DEV"         con-name "$HOTSPOT"         ssid "$HOTSPOT"
fi

nmcli connection modify "$HOTSPOT"     connection.autoconnect no     connection.interface-name "$DEV"     802-11-wireless.mode ap     802-11-wireless.band bg     802-11-wireless.ssid "$HOTSPOT"     802-11-wireless-security.key-mgmt wpa-psk     802-11-wireless-security.psk "$HOTSPOT_PASSWORD"     ipv4.method shared     ipv4.addresses "$HOTSPOT_IP"     ipv6.method disabled

printf '%s\n' "$HOTSPOT_PASSWORD" > "$PASSWORD_FILE"
chmod 0600 "$PASSWORD_FILE"

install -m 0755     "$INSTALLER_DIR/network/cvp-wifi-fallback"     /usr/local/sbin/cvp-wifi-fallback

install -m 0755     "$INSTALLER_DIR/tools/cvp_web.py"     "$RUNTIME_DIR/cvp_web.py"

install -m 0644     "$INSTALLER_DIR/systemd/cvp-wifi-fallback.service.in"     /etc/systemd/system/cvp-wifi-fallback.service

sed     -e "s#@CVP_USER@#$CVP_USER#g"     -e "s#@PROJECT_DIR@#$RUNTIME_DIR#g"     "$INSTALLER_DIR/systemd/cvp-web.service.in"     > /etc/systemd/system/cvp-web.service
chmod 0644 /etc/systemd/system/cvp-web.service

# NetworkManager's dnsmasq instance for shared connections reads this directory.
# Wildcard DNS plus DHCP option 114 gives phones/tablets a captive-portal hint.
install -d -m 0755 /etc/NetworkManager/dnsmasq-shared.d
cat > /etc/NetworkManager/dnsmasq-shared.d/cvp-access-portal.conf <<'EOF'
address=/#/10.42.0.1
dhcp-option=114,http://10.42.0.1/
EOF
chmod 0644 /etc/NetworkManager/dnsmasq-shared.d/cvp-access-portal.conf

# Publish a stable maintenance alias without changing the machine hostname.
touch /etc/avahi/hosts
if ! grep -Fqx "10.42.0.1 cvp-access.local" /etc/avahi/hosts; then
    printf '\n10.42.0.1 cvp-access.local\n' >> /etc/avahi/hosts
fi

systemctl daemon-reload
systemctl enable --now cvp-wifi-fallback.service
systemctl enable --now cvp-web.service
systemctl try-restart avahi-daemon.service >/dev/null 2>&1 || true

echo
echo "[CVP Access] Maintenance network installed"
echo "SSID      : $HOTSPOT"
echo "IP        : 10.42.0.1"
echo "Portal    : http://10.42.0.1"
echo "mDNS      : http://cvp-access.local"
echo "Password  : stored in $PASSWORD_FILE"
echo "Note      : captive DNS settings apply the next time the hotspot is activated."
