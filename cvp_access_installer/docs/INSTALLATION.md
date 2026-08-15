# Installation from a fresh Raspberry Pi OS Lite image

## Recommended image

- Raspberry Pi OS Lite 64-bit
- Debian 13 / Trixie generation
- Network configured in Raspberry Pi Imager if desired

The installer deliberately refuses an untested major OS release instead of attempting a risky Debian major-version migration. Raspberry Pi recommends re-imaging for major Raspberry Pi OS upgrades.

## Install

Clone the repository as the normal user:

```bash
git clone https://github.com/ocverclock/cvp_access.git CVP_access
cd CVP_access
```

Then launch the installer:

```bash
sudo bash cvp_access_installer/install.sh
```

`bash` is intentional: files uploaded through the GitHub web interface may not carry the executable bit.

The installer:

1. finds the Git repository root even though the installer lives in `cvp_access_installer/`;
2. validates Trixie and ARM64;
3. checks free disk space;
4. runs `apt update` and `apt full-upgrade`;
5. installs all packages declared in `apt-packages.txt`;
6. adds the normal user to `audio` and `input`;
7. installs Piper in an isolated venv;
8. downloads `fr_FR-siwis-medium`;
9. generates the complete voice bank;
10. copies the current CVP Access application to `/opt/cvp-access`;
11. configures `cvp-access.service`;
12. shares the full Git repository through Samba as `CVP_access`;
13. enables SSH, Avahi and Samba;
14. runs CVP Doctor;
15. offers one final reboot.

The installer is intended to be idempotent: it may be run again to repair or complete an installation.

## Which CVP Access version is installed?

The installer prefers:

```text
cvp_access.py
```

at the repository root.

Until that canonical file exists, it automatically chooses the newest versioned file matching:

```text
cvp_access_v*.py
```

using version sorting.

## Samba

On the first installation, a Samba password is requested for the normal Linux user.

Typical access:

```text
\\cvp-access.local\CVP_access
```

If a custom hostname was configured in Raspberry Pi Imager, it is preserved.

## Diagnostic

Normal diagnostic:

```bash
python3 cvp_access_installer/tools/cvp_doctor.py
```

Real Yamaha SysEx GET Tempo test:

```bash
sudo systemctl stop cvp-access
python3 cvp_access_installer/tools/cvp_doctor.py --active-midi
sudo systemctl start cvp-access
```

Optional real USB Audio playback test:

```bash
python3 cvp_access_installer/tools/cvp_doctor.py --active-audio
```

Both:

```bash
sudo systemctl stop cvp-access
python3 cvp_access_installer/tools/cvp_doctor.py --active-midi --active-audio
sudo systemctl start cvp-access
```

## Update

```bash
cd ~/CVP_access
sudo bash cvp_access_installer/update.sh
```

The updater refuses to overwrite local Git modifications. If files have been edited through Samba, it reports the dirty working tree and skips `git pull`.

## Uninstall runtime

```bash
sudo bash cvp_access_installer/uninstall.sh
```

Generated Piper/voice data is preserved by default.

To remove it too:

```bash
sudo bash cvp_access_installer/uninstall.sh --purge
```
