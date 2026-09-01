#!/usr/bin/env python3
from pathlib import Path
import py_compile
import tomllib

root = Path(__file__).resolve().parent

for rel in [
    "cvp_access_1_5_1.py",
    "cvp_song_151.py",
    "cvp_speech_151.py",
    "cvp_access_installer/tools/generate_151_voices.py",
    "cvp_access_installer/tools/cvp_doctor_151.py",
]:
    py_compile.compile(
        str(root / rel),
        doraise=True,
    )

with (
    root / "config/default-1.5.1.toml"
).open("rb") as handle:
    cfg = tomllib.load(handle)

keys = cfg["keys"]
assert keys["CAPS+F1"] == "announce_style_name"
assert keys["CAPS+F7"] == "metronome_toggle"
assert keys["CAPS+K"] == "registration_recall:8"

print("CVP Access 1.5.1 RC1 package: OK")
