#!/usr/bin/env python3
"""Contrôle de cohérence CVP Access 1.6.1 et couches compatibles."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


def service_state(name):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() or "inactive"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def command_output(args):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


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
    recordings = Path(
        os.environ.get(
            "CVP_RECORDINGS_DIR",
            home / "CVP_Recordings",
        )
    )

    expected = [
        "cvp_access.py",
        "cvp_access_v1.5.py",
        "cvp_access_v1.4.1.py",
        "cvp_keyboard.py",
        "cvp_recorder.py",
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
        "Runtime CVP Access",
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
                    ("1.5.1", "1.5.2", "1.6.0", "1.6.1")
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

    # Les annonces système doivent toujours être pré-générées.
    startup_file = voices / "system" / "startup_ready.wav"
    restart_file = voices / "system" / "restart_device.wav"
    system_missing = [
        p for p in (startup_file, restart_file)
        if not p.is_file()
    ]
    add(
        "WAV système",
        OK if not system_missing else FAIL,
        (
            "démarrage + relance présents"
            if not system_missing
            else "absents: "
            + ", ".join(
                str(p.relative_to(voices))
                for p in system_missing
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
        "WAV états",
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

    recorder_fixed = [
        voices / "recorder" / name
        for name in (
            "ready.wav",
            "cancelled.wav",
            "no_recording.wav",
            "play_stopped.wav",
            "play_finished.wav",
            "output_missing.wav",
            "save_error.wav",
            "stop.wav",
            "previous.wav",
            "next.wav",
            "numero.wav",
        )
    ]
    recorder_fixed.extend(
        voices / "recorder" / f"month_{month:02d}.wav"
        for month in range(1, 13)
    )
    missing_recorder_fixed = [
        path for path in recorder_fixed
        if not path.is_file()
    ]
    add(
        "WAV Recorder",
        OK if not missing_recorder_fixed else WARN,
        (
            f"{len(recorder_fixed)} présents"
            if not missing_recorder_fixed
            else f"{len(missing_recorder_fixed)} absents"
        ),
    )

    number_files = [
        voices / "numbers" / f"number_{number:03d}.wav"
        for number in range(0, 151)
    ]
    missing_numbers = [
        path for path in number_files
        if not path.is_file()
    ]
    add(
        "WAV nombres 0..150",
        OK if not missing_numbers else WARN,
        (
            "151 présents"
            if not missing_numbers
            else f"{len(missing_numbers)} absents"
        ),
    )

    recorder_dir_ok = (
        recordings.is_dir()
        and os.access(recordings, os.R_OK | os.W_OK | os.X_OK)
    )
    midi_files = (
        len(list(recordings.glob("*.mid")))
        if recordings.is_dir()
        else 0
    )
    add(
        "Recorder stockage",
        OK if recorder_dir_ok else FAIL,
        (
            f"{midi_files} fichier(s) MIDI · {recordings}"
            if recorder_dir_ok
            else f"dossier absent/non accessible: {recordings}"
        ),
    )

    selection_file = recordings / ".cvp-selection.json"
    selection_detail = "aucune sélection"
    selection_status = OK
    if selection_file.is_file():
        try:
            import json
            selected = json.loads(
                selection_file.read_text(encoding="utf-8")
            ).get("selected")
            target = recordings / str(selected)
            if (
                not isinstance(selected, str)
                or Path(selected).name != selected
                or not target.is_file()
            ):
                selection_status = WARN
                selection_detail = "sélection invalide"
            else:
                selection_detail = selected
        except Exception as exc:
            selection_status = WARN
            selection_detail = f"illisible: {exc}"
    add(
        "Recorder sélection",
        selection_status,
        selection_detail,
    )

    for command in ("aplaymidi", "sox"):
        add(
            f"Commande {command}",
            OK if shutil.which(command) else FAIL,
            shutil.which(command) or "absente",
        )

    wifi_state = service_state("cvp-wifi-fallback.service")
    web_state = service_state("cvp-web.service")
    add(
        "Wi-Fi fallback",
        OK if wifi_state == "active" else WARN,
        wifi_state,
    )
    add(
        "Portail maintenance",
        OK if web_state == "active" else WARN,
        web_state,
    )

    nm_rc, nm_out, nm_err = command_output(
        ["nmcli", "-g", "802-11-wireless.mode,ipv4.method,ipv4.addresses",
         "connection", "show", "CVP-ACCESS"]
    )
    expected_hotspot = (
        nm_rc == 0
        and "ap" in nm_out
        and "shared" in nm_out
        and "10.42.0.1/24" in nm_out
    )
    add(
        "Profil CVP-ACCESS",
        OK if expected_hotspot else WARN,
        nm_out.replace("\n", " | ") if nm_out else (nm_err or "absent"),
    )

    portal_file = runtime / "cvp_web.py"
    add(
        "Portail Web runtime",
        OK if portal_file.is_file() else WARN,
        str(portal_file),
    )

    print()
    print(
        "CVP Access Doctor 1.6.1"
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
