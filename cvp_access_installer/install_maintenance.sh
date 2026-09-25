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

CVP_HOME="$(getent passwd "$CVP_USER" | cut -d: -f6)"
RECORDINGS_DIR="${CVP_RECORDINGS_DIR:-$CVP_HOME/CVP_Recordings}"

RUNTIME_DIR="/opt/cvp-access"
CONFIG_DIR="/etc/cvp-access"
HOTSPOT="CVP-ACCESS"
HOTSPOT_IP="10.42.0.1/24"
PASSWORD_FILE="$CONFIG_DIR/hotspot-password"

detect_wifi_device() {
    if [[ -n "${CVP_WIFI_DEVICE:-}" ]]; then
        printf '%s\n' "$CVP_WIFI_DEVICE"
        return
    fi

    local profile_dev=""
    profile_dev="$(nmcli -g connection.interface-name connection show "$HOTSPOT" 2>/dev/null || true)"
    if [[ -n "$profile_dev" ]] && nmcli -t -f DEVICE,TYPE,STATE device status 2>/dev/null |
        awk -F: -v dev="$profile_dev" '$1 == dev && $2 == "wifi" && $3 != "unavailable" { found=1 } END { exit(found ? 0 : 1) }'; then
        printf '%s\n' "$profile_dev"
        return
    fi

    nmcli -t -f DEVICE,TYPE,STATE device status 2>/dev/null |
        awk -F: '$2 == "wifi" && $3 != "unavailable" { print $1; exit }'
}

for command in nmcli python3; do
    command -v "$command" >/dev/null || {
        echo "Missing required command: $command" >&2
        exit 1
    }
done

DEV="$(detect_wifi_device)"
if [[ -n "$DEV" ]]; then
    HAS_WIFI=1
    echo "[CVP Access] Wi-Fi maintenance interface: $DEV"
else
    HAS_WIFI=0
    echo "[CVP Access] WARNING: no usable Wi-Fi interface detected." >&2
    echo "[CVP Access] Web maintenance will still be installed; hotspot setup is skipped for this run." >&2
fi

install -d -m 0755 "$CONFIG_DIR" "$RUNTIME_DIR"
install -d -o "$CVP_USER" -g "$CVP_USER" -m 0775 "$RECORDINGS_DIR"

if (( HAS_WIFI )); then
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
        HOTSPOT_PASSWORD="$(python3 -c 'import secrets; alphabet="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"; print("".join(secrets.choice(alphabet) for _ in range(14)))')"
    fi

    if ! nmcli -t -f NAME connection show | grep -Fxq "$HOTSPOT"; then
        nmcli connection add         type wifi         ifname "$DEV"         con-name "$HOTSPOT"         ssid "$HOTSPOT"
    fi

    nmcli connection modify "$HOTSPOT"     connection.autoconnect no     connection.interface-name "$DEV"     802-11-wireless.mode ap     802-11-wireless.band bg     802-11-wireless.ssid "$HOTSPOT"     802-11-wireless-security.key-mgmt wpa-psk     802-11-wireless-security.psk "$HOTSPOT_PASSWORD"     ipv4.method shared     ipv4.addresses "$HOTSPOT_IP"     ipv6.method disabled

    printf '%s\n' "$HOTSPOT_PASSWORD" > "$PASSWORD_FILE"
    chmod 0600 "$PASSWORD_FILE"

fi

install -m 0755     "$INSTALLER_DIR/network/cvp-wifi-fallback"     /usr/local/sbin/cvp-wifi-fallback

install -m 0755     "$INSTALLER_DIR/network/cvp-wifi-connect"     /usr/local/sbin/cvp-wifi-connect

install -m 0755     "$INSTALLER_DIR/tools/cvp_web.py"     "$RUNTIME_DIR/cvp_web.py"

install -m 0755 \
    "$INSTALLER_DIR/tools/cvp_update_from_github" \
    /usr/local/sbin/cvp-update-from-github

if [[ -f "$REPO_DIR/cvp_keyboard_map.py" ]]; then
    install -m 0755 "$REPO_DIR/cvp_keyboard_map.py" "$RUNTIME_DIR/cvp_keyboard_map.py"
    if [[ -f "$CONFIG_DIR/keyboard.toml" ]]; then
        echo "[CVP Access] Refreshing printable keyboard map"
        runuser -u "$CVP_USER" --             python3 "$RUNTIME_DIR/cvp_keyboard_map.py"             --config "$CONFIG_DIR/keyboard.toml"             --output "$CONFIG_DIR/keyboard-map.html"             || echo "WARNING: keyboard map regeneration failed." >&2
    fi
fi

install -m 0644     "$INSTALLER_DIR/systemd/cvp-wifi-fallback.service.in"     /etc/systemd/system/cvp-wifi-fallback.service

sed     -e "s#@CVP_USER@#$CVP_USER#g"     -e "s#@PROJECT_DIR@#$RUNTIME_DIR#g"     -e "s#@REPO_DIR@#$REPO_DIR#g"     -e "s#@RECORDINGS_DIR@#$RECORDINGS_DIR#g"     "$INSTALLER_DIR/systemd/cvp-web.service.in"     > /etc/systemd/system/cvp-web.service
chmod 0644 /etc/systemd/system/cvp-web.service

# NetworkManager's dnsmasq instance for shared connections reads this directory.
# Wildcard DNS plus DHCP option 114 gives phones/tablets a captive-portal hint.
install -d -m 0755 /etc/NetworkManager/dnsmasq-shared.d
cat > /etc/NetworkManager/dnsmasq-shared.d/cvp-access-portal.conf <<'EOF'
address=/#/10.42.0.1
dhcp-option=114,http://10.42.0.1/captive-portal
EOF
chmod 0644 /etc/NetworkManager/dnsmasq-shared.d/cvp-access-portal.conf

# Remove the old fixed hotspot alias if it exists. On a normal Wi-Fi network
# that address would be wrong; Avahi already publishes the real hostname.
if [[ -f /etc/avahi/hosts ]]; then
    sed -i '/^[[:space:]]*10\.42\.0\.1[[:space:]]\+cvp-access\.local[[:space:]]*$/d' /etc/avahi/hosts
fi

systemctl daemon-reload
systemctl enable cvp-wifi-fallback.service
systemctl enable cvp-web.service
systemctl restart cvp-wifi-fallback.service
systemctl restart cvp-web.service
systemctl try-restart avahi-daemon.service >/dev/null 2>&1 || true

echo
HOST_NOW="$(hostnamectl --static 2>/dev/null || hostname)"
echo "[CVP Access] Maintenance services installed"
echo "LAN       : http://$HOST_NOW.local"
if (( HAS_WIFI )); then
    echo "SSID      : $HOTSPOT"
    echo "Hotspot   : http://10.42.0.1"
    echo "Password  : stored in $PASSWORD_FILE"
    echo "Note      : captive DNS settings apply the next time the hotspot is activated."
else
    echo "Hotspot   : skipped (no usable Wi-Fi interface during this run)"
fi
