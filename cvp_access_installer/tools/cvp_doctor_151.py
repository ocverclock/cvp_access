#!/usr/bin/env python3
"""Contrôle de cohérence spécifique CVP Access 1.5.1."""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path


OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


def main():
    home = Path.home()
    runtime = Path(
        os.environ.get(
            "CVP_RUNTIME_DIR",
            "/opt/cvp-access",
        )
    )
    config = Path(
        os.environ.get(
            "CVP_CONFIG_FILE",
            "/etc/cvp-access/keyboard.toml",
        )
    )
    voices = Path(
        os.environ.get(
            "CVP_VOICE_DIR",
            home / "cvp_voice",
        )
    )

    expected = [
        "cvp_access.py",
        "cvp_access_v1.5.py",
        "cvp_access_v1.4.1.py",
        "cvp_keyboard.py",
        "cvp_song.py",
        "cvp_song_151.py",
        "cvp_speech.py",
        "cvp_speech_151.py",
        "cvp_piper_worker.py",
        "cvp_midi.py",
        "cvp_yamaha.py",
        "cvp_registration.py",
        "cvp_style.py",
        "cvp_voice.py",
        "default-keyboard-1.5.1.toml",
    ]

    results = []

    def add(name, status, detail):
        results.append(
            (
                name,
                status,
                detail,
            )
        )

    missing = [
        name
        for name in expected
        if not (
            runtime / name
        ).is_file()
    ]
    add(
        "Runtime 1.5.1",
        OK if not missing else FAIL,
        (
            "modules complets"
            if not missing
            else "absents: "
            + ", ".join(
                missing
            )
        ),
    )

    if str(runtime) not in sys.path:
        sys.path.insert(
            0,
            str(runtime),
        )

    try:
        import cvp_access
        version = getattr(
            cvp_access,
            "VERSION",
            "?",
        )
        add(
            "Version runtime",
            (
                OK
                if str(version).startswith(
                    "1.5.1"
                )
                else FAIL
            ),
            str(version),
        )
    except Exception as exc:
        add(
            "Import runtime",
            FAIL,
            repr(exc),
        )

    try:
        with config.open(
            "rb"
        ) as handle:
            data = tomllib.load(
                handle
            )
        keys = data.get(
            "keys",
            {},
        )
    except Exception as exc:
        add(
            "Configuration",
            FAIL,
            repr(exc),
        )
        keys = {}

    expected_caps = {
        "W": "announce_style_name",
        "X": "announce_song_name",
        "C": "announce_song_length",
        "V": "sync_start_toggle",
        "B": "guide_toggle",
        "M": "voice_guide_mute_toggle",
        "L": "song_all_tracks_on",
        "RPAREN": "style_all_parts_on",
        "F7": "metronome_toggle",
        "PAGEUP": "style_volume_change:1",
        "SHIFT+PAGEUP": "style_volume_change:5",
        "PAGEDOWN": "style_volume_change:-1",
        "SHIFT+PAGEDOWN": "style_volume_change:-5",
    }

    song_keys = (
        "A", "Z", "E", "R", "T", "Y", "U", "I",
        "Q", "S", "D", "F", "G", "H", "J", "K",
    )
    for track, key in enumerate(song_keys, start=1):
        expected_caps[f"SHIFT+{key}"] = f"song_track_solo:{track}"

    missing_caps = [
        key
        for key, value
        in expected_caps.items()
        if keys.get(key) != value
    ]

    add(
        "Layout accessibilité",
        OK if not missing_caps else WARN,
        (
            "présente"
            if not missing_caps
            else "manquants/conflits: "
            + ", ".join(
                missing_caps
            )
        ),
    )

    # Vérification des WAV finis 1.5.1.
    state_files = []
    for stem in (
        "sync_start",
        "guide",
        "stream_lights",
        "metronome",
        "voice_guide",
    ):
        for state in (
            "on",
            "off",
        ):
            state_files.append(
                voices
                / "state"
                / f"{stem}_{state}.wav"
            )

    missing_states = [
        p
        for p in state_files
        if not p.is_file()
    ]

    add(
        "WAV états 1.5.1",
        (
            OK
            if not missing_states
            else WARN
        ),
        (
            f"{len(state_files)} présents"
            if not missing_states
            else f"{len(missing_states)} absents"
        ),
    )

    style_stems = (
        "rhythm_1",
        "rhythm_2",
        "bass",
        "chord_1",
        "chord_2",
        "pad",
        "phrase_1",
        "phrase_2",
    )
    style_mute_files = [
        voices / "style_part" / f"{stem}_mute.wav"
        for stem in style_stems
    ]
    missing_style_mutes = [
        p
        for p in style_mute_files
        if not p.is_file()
    ]

    add(
        "WAV mute Style",
        OK if not missing_style_mutes else WARN,
        (
            "8 présents"
            if not missing_style_mutes
            else f"{len(missing_style_mutes)} absents"
        ),
    )

    solo_files = [
        voices / "song_solo" / f"solo_{track:02d}.wav"
        for track in range(1, 17)
    ]
    missing_solo = [
        p
        for p in solo_files
        if not p.is_file()
    ]

    add(
        "WAV Solo Song",
        OK if not missing_solo else WARN,
        (
            "16 présents"
            if not missing_solo
            else f"{len(missing_solo)} absents"
        ),
    )

    print()
    print(
        "CVP Access Doctor 1.5.1"
    )
    print(
        "=" * 72
    )

    for name, status, detail in results:
        print(
            f"{status:4s}  "
            f"{name:24s}  "
            f"{detail}"
        )

    print(
        "=" * 72
    )

    failures = sum(
        status == FAIL
        for _, status, _
        in results
    )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
