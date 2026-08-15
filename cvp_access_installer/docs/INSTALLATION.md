# Installation from a fresh Raspberry Pi OS Lite image

## Recommended image

- Raspberry Pi OS Lite 64-bit
- Debian 13 / Trixie generation
- Network configured in Raspberry Pi Imager if desired

## Install

Clone the repository as the normal user, then run the installer with sudo:

```bash
git clone https://github.com/ocverclock/cvp_access.git CVP_access
cd CVP_access
sudo ./install.sh
```

The installer:

1. validates Trixie and ARM64;
2. checks free disk space;
3. runs `apt update` and `apt full-upgrade`;
4. installs Python, ALSA/MIDI, Samba, SSH, Avahi and diagnostic packages;
5. adds the normal user to `audio` and `input`;
6. installs Piper in an isolated venv;
7. downloads `fr_FR-siwis-medium`;
8. generates the complete voice bank;
9. installs a runtime copy under `/opt/cvp-access`;
10. configures the `cvp-access.service` systemd service;
11. shares the Git checkout through Samba as `CVP_access`;
12. enables SSH, Avahi and Samba;
13. runs CVP Doctor;
14. offers one final reboot.

The installer is designed to be idempotent: running it again should repair/complete the installation without duplicating Samba configuration or regenerating existing WAV files.

## Samba

On the first install, a Samba password is requested for the normal Linux user. The project is then reachable at approximately:

```text
\\cvp-access.local\CVP_access
```

If a custom hostname was already configured in Raspberry Pi Imager, that hostname is preserved.

## Diagnostic

```bash
python3 tools/cvp_doctor.py
```

For an actual Yamaha GET Tempo SysEx test, first stop the running service:

```bash
sudo systemctl stop cvp-access
python3 tools/cvp_doctor.py --active-midi
sudo systemctl start cvp-access
```

## Update

```bash
cd ~/CVP_access
sudo ./update.sh
```

## Uninstall runtime

```bash
sudo ./uninstall.sh
```

Generated Piper/voice data is preserved by default. To remove it too:

```bash
sudo ./uninstall.sh --purge
```
