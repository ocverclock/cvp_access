#!/usr/bin/env python3
import argparse
import glob
import grp
import os
import pwd
import re
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

MIDI_NAME = "ProdipeMIDIlilo MIDI 1"
AUDIO_NAME = "Clavinova"
AUDIO_DEVICE = "plughw:CARD=Clavinova,DEV=0"
TEMPO_GET = "F0 43 73 01 52 25 26 01 00 08 00 00 01 00 01 00 F7"
TEMPO_PROP = [0x08, 0x00, 0x00, 0x01]
HEADER = [0xF0, 0x43, 0x73, 0x01, 0x52, 0x25, 0x26]

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"
SKIP = "SKIP"


def run(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def find_command(command):
    path = shutil.which(command)
    if path:
        return path
    for directory in ("/usr/local/sbin", "/usr/sbin", "/sbin", "/usr/local/bin", "/usr/bin", "/bin"):
        candidate = Path(directory) / command
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def service_state(name):
    rc, out, _ = run(["systemctl", "is-active", name])
    return out.strip() if out.strip() else ("active" if rc == 0 else "inactive")


def repo_default():
    here = Path(__file__).resolve()
    installer = here.parent.parent
    rc, out, _ = run(["git", "-C", str(installer), "rev-parse", "--show-toplevel"])
    if rc == 0 and out.strip():
        return Path(out.strip())
    parent = installer.parent
    return parent if (parent / "README.md").exists() else installer


def find_midi_port():
    rc, out, err = run(["amidi", "-l"])
    if rc != 0:
        return None, out + err
    for line in out.splitlines():
        if MIDI_NAME in line:
            match = re.search(r"(hw:\d+,\d+,\d+)", line)
            if match:
                return match.group(1), out
    return None, out


def parse_hex_stream(text):
    return [int(x, 16) for x in re.findall(r"\b[0-9A-Fa-f]{2}\b", text)]


def active_tempo_test(port):
    if service_state("cvp-access.service") == "active":
        return SKIP, "cvp-access.service is active; stop it before an active MIDI test"

    try:
        receiver = subprocess.Popen(
            ["amidi", "-p", port, "-d"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
        )
    except OSError as exc:
        return FAIL, str(exc)

    try:
        time.sleep(0.25)
        rc, _, err = run(["amidi", "-p", port, "-S", TEMPO_GET], timeout=3)
        if rc != 0:
            return FAIL, f"GET Tempo send failed: {err.strip()}"

        import select
        deadline = time.monotonic() + 2.0
        collected = ""
        while time.monotonic() < deadline:
            if receiver.poll() is not None:
                break
            ready, _, _ = select.select([receiver.stdout], [], [], 0.1)
            if ready:
                ch = receiver.stdout.read(1)
                if ch:
                    collected += ch
                    if "F7" in collected.upper():
                        break

        values = parse_hex_stream(collected)
        for start in range(len(values)):
            if values[start:start + 7] != HEADER:
                continue
            msg = values[start:]
            try:
                end = msg.index(0xF7)
            except ValueError:
                continue
            msg = msg[:end + 1]
            if len(msg) < 21:
                continue
            if msg[7:9] != [0x00, 0x00] or msg[9:13] != TEMPO_PROP:
                continue
            length = (msg[16] << 7) | msg[17]
            data = msg[18:18 + length]
            if len(data) == 2:
                tempo = (data[0] << 7) | data[1]
                return OK, f"CVP replied to GET Tempo: {tempo} BPM"

        return WARN, "no valid GET Tempo response detected"
    finally:
        if receiver.poll() is None:
            receiver.terminate()
            try:
                receiver.wait(timeout=1)
            except subprocess.TimeoutExpired:
                receiver.kill()


def active_audio_test(voices):
    candidates = [
        voices / "piste_01_on.wav",
        voices / "transport" / "lecture.wav",
    ]
    source = next((p for p in candidates if p.is_file()), None)
    if source is None:
        return SKIP, "no generated test WAV available"

    rc, _, err = run(["aplay", "-q", "-D", AUDIO_DEVICE, str(source)], timeout=10)
    if rc == 0:
        return OK, f"played {source.name} through {AUDIO_DEVICE}"
    return FAIL, err.strip() or "aplay failed"


def count_glob(path, pattern):
    return len(list(path.glob(pattern))) if path.exists() else 0


def main():
    parser = argparse.ArgumentParser(description="CVP Access installation/hardware diagnostic")
    parser.add_argument("--active-midi", action="store_true",
                        help="send a GET Tempo SysEx when cvp-access.service is stopped")
    parser.add_argument("--active-audio", action="store_true",
                        help="play a short generated voice through Clavinova USB Audio")
    args = parser.parse_args()

    home = Path.home()
    project = Path(os.environ.get("CVP_PROJECT_DIR", repo_default()))
    runtime = Path(os.environ.get("CVP_RUNTIME_DIR", "/opt/cvp-access"))
    voices = Path(os.environ.get("CVP_VOICE_DIR", home / "cvp_voice"))
    model = Path(os.environ.get(
        "CVP_PIPER_MODEL",
        home / "piper-voices" / "fr_FR-siwis-medium.onnx"
    ))
    config_file = Path(os.environ.get(
        "CVP_CONFIG_FILE",
        "/etc/cvp-access/keyboard.toml"
    ))
    if "CVP_PIPER_MODEL" not in os.environ and config_file.is_file():
        try:
            with config_file.open("rb") as handle:
                cfg = tomllib.load(handle)
            configured_voice = cfg.get("speech", {}).get("voice")
            if configured_voice:
                model = home / "piper-voices" / f"{configured_voice}.onnx"
        except Exception:
            pass
    piper_python = home / ".local/share/cvp-access/piper-env/bin/python"

    results = []

    def check(name, status, detail=""):
        results.append((name, status, detail))

    os_release = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os_release[k] = v.strip().strip('"')
    except OSError:
        pass

    codename = os_release.get("VERSION_CODENAME", "unknown")
    check("OS", OK if codename == "trixie" else WARN,
          os_release.get("PRETTY_NAME", codename))

    rc, arch, _ = run(["dpkg", "--print-architecture"])
    arch = arch.strip()
    check("Architecture", OK if rc == 0 and arch == "arm64" else WARN,
          arch or "unknown")

    for command in ["python3", "amidi", "aplay", "git", "smbd", "avahi-daemon", "ssh"]:
        path = find_command(command)
        check(command, OK if path else FAIL, path or "not found")

    try:
        import evdev  # noqa: F401
        check("Python evdev", OK, "import successful")
    except Exception as exc:
        check("Python evdev", FAIL, str(exc))

    check("Piper venv", OK if piper_python.is_file() else FAIL, str(piper_python))

    username = pwd.getpwuid(os.getuid()).pw_name
    memberships = {g.gr_name for g in grp.getgrall() if username in g.gr_mem}
    try:
        memberships.add(grp.getgrgid(pwd.getpwnam(username).pw_gid).gr_name)
    except KeyError:
        pass
    missing_groups = [g for g in ("audio", "input") if g not in memberships]
    check("audio/input groups",
          OK if not missing_groups else WARN,
          "missing: " + ", ".join(missing_groups)
          if missing_groups else "member of audio,input")

    check("Project directory", OK if project.exists() else WARN, str(project))
    check("Runtime", OK if (runtime / "cvp_access.py").is_file() else FAIL,
          str(runtime / "cvp_access.py"))

    speech_runtime = runtime / "cvp_speech.py"
    piper_worker = runtime / "cvp_piper_worker.py"
    if speech_runtime.is_file() or piper_worker.is_file():
        check(
            "Runtime speech",
            OK if speech_runtime.is_file() and piper_worker.is_file() else FAIL,
            "cvp_speech.py + cvp_piper_worker.py"
            if speech_runtime.is_file() and piper_worker.is_file()
            else "runtime speech files incomplete",
        )

    keyboard_router = runtime / "cvp_keyboard.py"
    if keyboard_router.is_file():
        rc, out, err = run(
            ["python3", str(keyboard_router), "--check", str(config_file)],
            timeout=10,
        )
        detail_lines = [
            line.strip()
            for line in (out + "\n" + err).splitlines()
            if line.strip()
        ]
        detail = detail_lines[0] if detail_lines else str(config_file)
        check("Keyboard config", OK if rc == 0 else FAIL, detail)
    elif config_file.exists():
        check("Keyboard config", WARN,
              f"{config_file} present but cvp_keyboard.py is missing")
    else:
        check("Keyboard config", SKIP,
              "v1.4.x runtime / configurable keyboard not installed")

    keyboards = glob.glob("/dev/input/by-id/*-event-kbd")
    check("USB keyboard", OK if keyboards else WARN,
          keyboards[0] if keyboards else "not detected")

    midi_port, _ = find_midi_port()
    check("Prodipe MIDI", OK if midi_port else WARN, midi_port or "not detected")

    rc, aplay_out, aplay_err = run(["aplay", "-l"])
    audio_found = rc == 0 and AUDIO_NAME.lower() in aplay_out.lower()
    check("Clavinova USB Audio",
          OK if audio_found else WARN,
          "detected" if audio_found else (aplay_err.strip() or "not detected"))

    check("Piper model",
          OK if model.is_file() and Path(str(model) + ".json").is_file() else FAIL,
          str(model))

    # Voice bank expectations follow keyboard.toml instead of assuming a
    # permanently generated 599-file bank.
    try:
        with config_file.open("rb") as handle:
            config_data = tomllib.load(handle)
    except Exception:
        config_data = {}

    speech_cfg = config_data.get("speech", {}) if isinstance(config_data, dict) else {}
    speech_mode = speech_cfg.get("mode", "pregenerated")
    generation_mode = speech_cfg.get("generation", "core")

    def parse_action(value):
        if not isinstance(value, str):
            return None, None
        if ":" in value:
            name, raw = value.split(":", 1)
            try:
                return name.strip().lower(), int(raw.strip())
            except ValueError:
                return name.strip().lower(), None
        return value.strip().lower(), None

    def required_voice_files():
        actions = set()
        keys = config_data.get("keys", {}) if isinstance(config_data, dict) else {}
        if generation_mode == "configured" and isinstance(keys, dict):
            for value in keys.values():
                name, parameter = parse_action(value)
                if name:
                    actions.add((name, parameter))
        else:
            actions.update(("song_track_toggle", n) for n in range(1, 17))
            actions.update(("style_part_toggle", n) for n in range(1, 9))
            actions.update({
                ("layer_toggle", None), ("left_toggle", None),
                ("announce_tempo", None), ("announce_transpose", None),
                ("song_play_pause", None), ("song_stop", None),
                ("song_position", None),
                ("voice_volume_up", None), ("voice_volume_down", None),
                ("style_volume_up", None), ("style_volume_down", None),
            })

        style_stems = [
            "rhythm_1", "rhythm_2", "bass", "chord_1",
            "chord_2", "pad", "phrase_1", "phrase_2",
        ]
        paths = set()
        for name, parameter in actions:
            if name == "song_track_toggle" and parameter and 1 <= parameter <= 16:
                paths.add(voices / f"piste_{parameter:02d}_off.wav")
                paths.add(voices / f"piste_{parameter:02d}_on.wav")
            elif name == "style_part_toggle" and parameter and 1 <= parameter <= 8:
                stem = style_stems[parameter - 1]
                paths.add(voices / "style_part" / f"{stem}_on.wav")
                paths.add(voices / "style_part" / f"{stem}_off.wav")
            elif name == "layer_toggle":
                paths.add(voices / "voice_part" / "layer_on.wav")
                paths.add(voices / "voice_part" / "layer_off.wav")
            elif name == "left_toggle":
                paths.add(voices / "voice_part" / "left_on.wav")
                paths.add(voices / "voice_part" / "left_off.wav")
            elif name == "announce_tempo":
                paths.update(voices / "tempo" / f"tempo_{v:03d}.wav" for v in range(5, 281))
            elif name == "announce_transpose":
                paths.add(voices / "transpose" / "transpose_000.wav")
                paths.update(voices / "transpose" / f"transpose_m{v:02d}.wav" for v in range(1, 13))
                paths.update(voices / "transpose" / f"transpose_p{v:02d}.wav" for v in range(1, 13))
            elif name in {"voice_volume_up", "voice_volume_down"}:
                paths.update(voices / "volume" / f"volume_{v:03d}.wav" for v in range(10, 101, 10))
            elif name in {"style_volume_up", "style_volume_down"}:
                paths.update(voices / "style_volume" / f"style_volume_{v:03d}.wav" for v in range(128))
            elif name == "song_play_pause":
                paths.add(voices / "transport" / "lecture.wav")
                paths.add(voices / "transport" / "pause.wav")
            elif name == "song_stop":
                paths.add(voices / "transport" / "stop.wav")
            elif name == "song_position":
                paths.add(voices / "words" / "mesure.wav")
                paths.add(voices / "words" / "temps.wav")
                paths.update(voices / "numbers" / f"number_{v:03d}.wav" for v in range(101))
        return paths

    if speech_mode == "runtime":
        check("Voice bank", SKIP, "runtime mode: Piper synthesizes on demand")
    else:
        required = required_voice_files()
        missing = [path for path in required if not path.is_file()]
        present = len(required) - len(missing)
        if not missing:
            voice_status = OK
        elif speech_mode == "hybrid":
            voice_status = WARN
        else:
            voice_status = FAIL
        detail = f"{present}/{len(required)} required WAV ({generation_mode})"
        if missing:
            sample = ", ".join(str(path.relative_to(voices)) for path in missing[:4])
            detail += f"; missing {len(missing)}: {sample}"
        check("Voice bank", voice_status, detail)

    for service in ["cvp-access.service", "smbd.service",
                    "avahi-daemon.service", "ssh.service"]:
        state = service_state(service)
        status = OK if state == "active" else WARN
        check(service, status, state)

    rc, out, err = run(["testparm", "-s"], timeout=10)
    samba_ok = rc == 0 and "[CVP_access]" in out
    check("Samba CVP_access",
          OK if samba_ok else WARN,
          "share defined" if samba_ok else (err.strip() or "share not found"))

    if args.active_midi:
        if midi_port:
            status, detail = active_tempo_test(midi_port)
            check("Active SysEx GET Tempo", status, detail)
        else:
            check("Active SysEx GET Tempo", SKIP, "Prodipe MIDI not detected")

    if args.active_audio:
        if audio_found:
            status, detail = active_audio_test(voices)
            check("Active USB Audio", status, detail)
        else:
            check("Active USB Audio", SKIP, "Clavinova USB Audio not detected")

    print("\nCVP Access Doctor")
    print("=" * 78)
    for name, status, detail in results:
        print(f"{status:4s}  {name:24s}  {detail}")

    fails = sum(1 for _, status, _ in results if status == FAIL)
    warns = sum(1 for _, status, _ in results if status == WARN)
    print("=" * 78)
    print(f"Result: {fails} failure(s), {warns} warning(s)")
    if not args.active_midi:
        print("MIDI test: stop cvp-access.service, then add --active-midi.")
    if not args.active_audio:
        print("Audio test: add --active-audio to play a short generated prompt.")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
