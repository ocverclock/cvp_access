#!/usr/bin/env python3
"""Persistent Piper worker for CVP Access runtime/hybrid speech."""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig


def emit(payload):
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--length-scale", type=float, default=0.85)
    args = parser.parse_args()

    if not args.model.is_file():
        emit({"ready": False, "error": f"model absent: {args.model}"})
        return 2

    try:
        voice = PiperVoice.load(str(args.model))
        syn_config = SynthesisConfig(length_scale=args.length_scale)
    except Exception as exc:
        emit({"ready": False, "error": str(exc)})
        return 2

    emit({"ready": True})

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            request = json.loads(raw)
            text = request["text"]
            output = Path(request["output"])
            output.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file, syn_config=syn_config)
            emit({"ok": True, "output": str(output)})
        except Exception as exc:
            emit({"ok": False, "error": str(exc)})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
