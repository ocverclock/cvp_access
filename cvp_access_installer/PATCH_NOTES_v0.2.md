# CVP Access installer v0.2 corrections

Major fixes compared with the first uploaded draft:

1. The installer now distinguishes the repository root from the nested `cvp_access_installer/` directory.
2. The main CVP program is found at repository root, preferring `cvp_access.py` and otherwise selecting the newest `cvp_access_v*.py`.
3. Samba now shares the full Git repository rather than only the installer directory.
4. `update.sh` now finds the real `.git` directory, safely updates from a temporary copy, handles new APT dependencies, repairs Piper, refreshes systemd and Samba, and regenerates newly introduced voice prompts.
5. Documentation uses `sudo bash ...` because GitHub web uploads currently store the shell files without the executable bit.
6. The systemd unit no longer orders itself after `multi-user.target`.
7. Automatic `apt autoremove` was removed to avoid deleting packages on an existing system.
8. `cvp_doctor.py` now auto-detects the repository, finds `/usr/sbin` tools reliably, checks the Piper venv, and offers an optional real USB Audio playback test.
9. The APT package list is centralized in `apt-packages.txt`.
10. `libgomp1` is explicitly installed for ONNX Runtime compatibility.
