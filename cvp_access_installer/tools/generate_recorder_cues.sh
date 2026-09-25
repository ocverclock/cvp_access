#!/usr/bin/env bash
set -Eeuo pipefail

VOICE_DIR="${CVP_VOICE_DIR:-$HOME/cvp_voice}"
OUT_DIR="$VOICE_DIR/recorder"

command -v sox >/dev/null 2>&1 || {
    echo "SoX absent : impossible de générer les sons de navigation Recorder." >&2
    exit 1
}

mkdir -p "$OUT_DIR"

# Mini-glissandos de 90 ms :
# - previous : aigu -> grave
# - next     : grave -> aigu
#
# 22.05 kHz / mono / 16 bit suffit largement pour ces repères sonores et
# réduit le coût de lecture. Les fades courts évitent les clics numériques.
sox -q -n -r 22050 -b 16 -c 1 "$OUT_DIR/previous.wav" \
    synth 0.09 sine 880:600 fade q 0.005 0.09 0.012 gain -14

sox -q -n -r 22050 -b 16 -c 1 "$OUT_DIR/next.wav" \
    synth 0.09 sine 600:880 fade q 0.005 0.09 0.012 gain -14

chmod 0644 "$OUT_DIR/previous.wav" "$OUT_DIR/next.wav"

echo "Recorder cues générés :"
echo "  $OUT_DIR/previous.wav"
echo "  $OUT_DIR/next.wav"
