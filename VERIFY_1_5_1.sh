#!/usr/bin/env bash
set -euo pipefail

cd "${1:-.}"

python3 -m py_compile \
  cvp_access_v1.5.py \
  cvp_access_v1.4.1.py \
  cvp_midi.py \
  cvp_yamaha.py \
  cvp_registration.py \
  cvp_style.py \
  cvp_voice.py \
  cvp_song.py \
  cvp_keyboard.py

python3 - <<'PY'
from cvp_yamaha import decode_yamaha_text, parse_yamaha_path
from cvp_style import StyleController
from cvp_voice import XGVoice

raw = bytes.fromhex(
    "00 50 52 45 53 45 54 3A "
    "00 2F 53 4F 4E 47 2F 36 "
    "00 30 20 50 6F 70 75 6C "
    "00 61 72 2F 50 6F 70 2F "
    "00 53 68 61 6C 6C 6F 77 "
    "00 2E 53 30 30 30 2E 6D "
    "00 69 64"
)
expected = "PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid"
assert decode_yamaha_text(raw) == expected

info = parse_yamaha_path(
    "PRESET:/STYLE/Pop&Rock/Rock/80s Classic Rock.T310.prs"
)
assert info.source == "PRESET"
assert info.name == "80s Classic Rock.T310"
assert info.extension == "prs"

assert StyleController.encode_style_number(3697) == (0x1C, 0x71)
assert XGVoice(104, 21, 0).program == 1

print("Tests unitaires 1.5.1 : OK")
PY

echo "Compilation et tests : OK"
