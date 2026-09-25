#!/usr/bin/env python3
"""Accessible MIDI recorder for CVP Access 1.6.x.

The recorder never opens the MIDI input device itself. It receives copies of
already parsed channel messages from the permanent CVP Access MIDI receiver.

Initial 1.6 scope:
- channel 1 recording;
- F14/F16 accessible recording selection;
- F15 short/long record/play state machine;
- Standard MIDI File type 0 output;
- fixed tempo captured when arming;
- selection shared with the maintenance Web portal;
- playback through ALSA aplaymidi.
"""

from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import mido
from evdev import ecodes


STATE_IDLE = "idle"
STATE_ARMED = "armed"
STATE_RECORDING = "recording"
STATE_PLAYING = "playing"


class RecorderController:
    def __init__(
        self,
        core,
        port,
        *,
        recordings_dir: Path,
        long_press_seconds: float = 1.2,
        navigation_hold_seconds: float = 0.8,
    ):
        self.core = core
        self.port = port
        self.recordings_dir = Path(recordings_dir)
        self.selection_file = self.recordings_dir / ".cvp-selection.json"
        self.long_press_seconds = float(long_press_seconds)
        self.navigation_hold_seconds = float(navigation_hold_seconds)

        self.lock = threading.RLock()
        self.state = STATE_IDLE
        self.events: list[tuple[float, bytes]] = []
        self.recording_started_at: float | None = None
        self.recording_tempo_bpm = 120
        self.active_notes: set[int] = set()

        self.key_pressed = False
        self.long_press_fired = False
        self.press_generation = 0
        self.press_timer: threading.Timer | None = None

        self.navigation_pressed = {}
        self.navigation_long_fired = {}
        self.navigation_generation = {}
        self.navigation_timers = {}
        self.navigation_cues = {}

        self.play_process: subprocess.Popen | None = None
        self.play_generation = 0
        self.playback_port_cache: str | None = None

        # Rapid F14/F16 navigation must not glob/sort the directory for every
        # keystroke. Refresh periodically so Samba/Web file changes still
        # become visible without restarting the service.
        self.recording_files_cache: tuple[Path, ...] = ()
        self.recording_files_cache_at = 0.0
        self.recording_files_cache_seconds = 2.0

        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_selection()

    # ------------------------------------------------------------------
    # Announcements
    # ------------------------------------------------------------------

    def _speak(self, text: str):
        print(f"Recorder : {text}")

        fixed = {
            "Enregistrement prêt.": "announce_recorder_ready",
            "Enregistrement annulé.": "announce_recorder_cancelled",
            "Aucun enregistrement disponible.": "announce_recorder_no_recording",
            "Lecture.": "announce_recorder_play",
            "Lecture arrêtée.": "announce_recorder_play_stopped",
            "Lecture terminée.": "announce_recorder_play_finished",
            "Sortie MIDI de lecture introuvable.": "announce_recorder_output_missing",
            "Erreur pendant la sauvegarde.": "announce_recorder_save_error",
        }

        hook = fixed.get(text)
        if hook:
            announcer = getattr(self.core, hook, None)
            if callable(announcer):
                try:
                    announcer()
                    return
                except Exception as exc:
                    print("Recorder : erreur annonce :", exc)

        announcer = getattr(self.core, "announce_action_help", None)
        if callable(announcer):
            try:
                announcer(text)
            except Exception as exc:
                print("Recorder : erreur annonce :", exc)

    def _stop_feedback_now(self):
        print("Recorder : Stop.")
        announcer = getattr(
            self.core,
            "announce_recorder_stop_now",
            None,
        )
        if callable(announcer):
            try:
                announcer()
                return
            except Exception as exc:
                print("Recorder : erreur annonce Stop :", exc)

        self._speak("Stop.")

    # ------------------------------------------------------------------
    # Selection / filenames
    # ------------------------------------------------------------------

    def _recording_files(self, *, refresh=False):
        now = time.monotonic()

        with self.lock:
            if (
                not refresh
                and self.recording_files_cache
                and (
                    now - self.recording_files_cache_at
                    < self.recording_files_cache_seconds
                )
            ):
                return list(self.recording_files_cache)

        files = tuple(
            sorted(
                (
                    path
                    for path in self.recordings_dir.glob("*.mid")
                    if path.is_file()
                ),
                key=lambda path: path.name,
            )
        )

        with self.lock:
            self.recording_files_cache = files
            self.recording_files_cache_at = now

        return list(files)

    def _invalidate_recording_files_cache(self):
        with self.lock:
            self.recording_files_cache = ()
            self.recording_files_cache_at = 0.0

    def _read_selected_name(self):
        try:
            data = json.loads(
                self.selection_file.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return None

        name = data.get("selected")
        if not isinstance(name, str):
            return None

        if Path(name).name != name:
            return None

        path = self.recordings_dir / name
        return name if path.is_file() else None

    def _write_selected_name(self, name: str):
        if Path(name).name != name:
            return False

        target = self.recordings_dir / name
        if not target.is_file():
            return False

        tmp = self.selection_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"selected": name}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        tmp.chmod(0o664)
        tmp.replace(self.selection_file)
        return True

    def _ensure_selection(self):
        selected = self._read_selected_name()
        if selected:
            return selected

        files = self._recording_files()
        if not files:
            return None

        name = files[-1].name
        try:
            self._write_selected_name(name)
        except OSError:
            pass
        return name

    def selected_path(self):
        name = self._read_selected_name()
        if not name:
            name = self._ensure_selection()
        return self.recordings_dir / name if name else None

    def _navigate_selection(self, delta):
        files = self._recording_files()
        if not files:
            self._speak("Aucun enregistrement disponible.")
            return False

        selected = self._read_selected_name()
        names = [path.name for path in files]

        if selected in names:
            index = names.index(selected)
        else:
            index = len(names) - 1

        index = (index + int(delta)) % len(names)
        name = names[index]

        if not self._write_selected_name(name):
            return False

        print("Recorder : sélection", name)
        return True

    def _play_navigation_cue(self, cue):
        player = getattr(
            self.core,
            "play_recorder_navigation_cue",
            None,
        )
        if callable(player):
            try:
                player(cue)
            except Exception as exc:
                print("Recorder : erreur son navigation :", exc)

    def _announce_selected_recording(self):
        path = self.selected_path()
        if path is None:
            self._speak("Aucun enregistrement disponible.")
            return

        match = re.match(
            r"^(\d{4})-(\d{2})-(\d{2})_(\d{3,})\.mid$",
            path.name,
            re.IGNORECASE,
        )
        if match is None:
            self._speak(path.stem)
            return

        _year, month, day, number = (
            int(value)
            for value in match.groups()
        )

        print(
            "Recorder : morceau sélectionné",
            path.name,
        )

        announcer = getattr(
            self.core,
            "announce_recorder_selection_now",
            None,
        )
        if callable(announcer):
            try:
                announcer(
                    day,
                    month,
                    number,
                )
                return
            except Exception as exc:
                print(
                    "Recorder : erreur annonce sélection :",
                    exc,
                )

        self._speak(
            f"{day} {self._month_name(month)}, "
            f"numéro {number}."
        )

    def _next_recording_path(self):
        prefix = datetime.now().strftime("%Y-%m-%d")
        used = set()
        pattern = re.compile(
            rf"^{re.escape(prefix)}_(\d{{3,}})\.mid$",
            re.IGNORECASE,
        )

        for path in self.recordings_dir.glob(f"{prefix}_*.mid"):
            match = pattern.match(path.name)
            if match:
                used.add(int(match.group(1)))

        number = 1
        while number in used:
            number += 1

        return self.recordings_dir / f"{prefix}_{number:03d}.mid", number

    # ------------------------------------------------------------------
    # F14 / F15 / F16 controls
    # ------------------------------------------------------------------

    def handle_key_event(self, event, *, help_requested=False):
        if event.type != ecodes.EV_KEY:
            return False

        navigation = {
            ecodes.KEY_F14: (-1, "previous", "Morceau précédent"),
            ecodes.KEY_F16: (1, "next", "Morceau suivant"),
        }

        if event.code in navigation:
            delta, cue, label = navigation[event.code]

            if help_requested:
                if event.value == 1:
                    self._speak(
                        f"{label}. Maintenir pour annoncer "
                        "le morceau sélectionné."
                    )
                return True

            if event.value == 1:
                self._navigation_key_down(
                    event.code,
                    delta,
                    cue,
                )
            elif event.value == 0:
                self._navigation_key_up(event.code)
            # Autorepeat is consumed and ignored.
            return True

        if event.code != ecodes.KEY_F15:
            return False

        # CTRL keeps the global CVP Access accessibility convention:
        # announce the function without executing it.
        if help_requested:
            if event.value == 1:
                self._speak(
                    "Dictaphone MIDI. Appui court : lecture, arrêt, "
                    "annulation ou sauvegarde selon l'état. "
                    "Appui long : préparer un nouvel enregistrement."
                )
            return True

        # value=1 press, value=2 autorepeat, value=0 release.
        if event.value == 1:
            self._key_down()
        elif event.value == 0:
            self._key_up()
        # Autorepeat is deliberately consumed and ignored.

        return True

    def _navigation_key_down(self, code, delta, cue):
        with self.lock:
            if self.navigation_pressed.get(code):
                return

            state = self.state
            if state in {STATE_ARMED, STATE_RECORDING}:
                return

            self.navigation_pressed[code] = True
            self.navigation_long_fired[code] = False
            generation = self.navigation_generation.get(code, 0) + 1
            self.navigation_generation[code] = generation

        if state == STATE_PLAYING:
            self.stop_playback(announce=False)

        if not self._navigate_selection(delta):
            with self.lock:
                self.navigation_pressed[code] = False
            return

        with self.lock:
            self.navigation_cues[code] = cue

        timer = threading.Timer(
            self.navigation_hold_seconds,
            self._fire_navigation_long_press,
            args=(code, generation),
        )
        timer.daemon = True

        with self.lock:
            if not self.navigation_pressed.get(code):
                return
            self.navigation_timers[code] = timer

        timer.start()

    def _navigation_key_up(self, code):
        with self.lock:
            self.navigation_pressed[code] = False
            timer = self.navigation_timers.pop(code, None)
            long_fired = self.navigation_long_fired.get(code, False)
            cue = self.navigation_cues.pop(code, None)

        if timer is not None:
            timer.cancel()

        # Appui court : retour sonore au relâchement.
        # Appui long : aucune sonnerie, seule l'annonce du morceau est lue.
        if not long_fired and cue is not None:
            self._play_navigation_cue(cue)

    def _fire_navigation_long_press(self, code, generation):
        with self.lock:
            if (
                not self.navigation_pressed.get(code)
                or generation
                != self.navigation_generation.get(code)
                or self.navigation_long_fired.get(code)
            ):
                return

            self.navigation_long_fired[code] = True

        self._announce_selected_recording()

    def _key_down(self):
        with self.lock:
            if self.key_pressed:
                return

            self.key_pressed = True
            self.long_press_fired = False
            self.press_generation += 1
            generation = self.press_generation

            timer = threading.Timer(
                self.long_press_seconds,
                self._fire_long_press,
                args=(generation,),
            )
            timer.daemon = True
            self.press_timer = timer
            timer.start()

    def _key_up(self):
        short_press = False

        with self.lock:
            if not self.key_pressed:
                return

            self.key_pressed = False
            timer = self.press_timer
            self.press_timer = None

            if timer is not None:
                timer.cancel()

            if not self.long_press_fired:
                short_press = True

        if short_press:
            self.handle_short_press()

    def _fire_long_press(self, generation):
        with self.lock:
            if (
                not self.key_pressed
                or generation != self.press_generation
                or self.long_press_fired
            ):
                return

            self.long_press_fired = True

        self.handle_long_press()

    def handle_long_press(self):
        with self.lock:
            state = self.state

        if state == STATE_PLAYING:
            self.stop_playback(announce=False)
            self.arm()
            return

        if state == STATE_IDLE:
            self.arm()
            return

        if state == STATE_ARMED:
            self._speak("Enregistrement déjà prêt.")
            return

        if state == STATE_RECORDING:
            self._speak("Enregistrement en cours.")

    def handle_short_press(self):
        with self.lock:
            state = self.state

        if state == STATE_ARMED:
            self.cancel_arm()
        elif state == STATE_RECORDING:
            self.stop_and_save()
        elif state == STATE_PLAYING:
            self.stop_playback()
        else:
            self.play_selected()

    # ------------------------------------------------------------------
    # Record state
    # ------------------------------------------------------------------

    def arm(self):
        # Tempo query must happen outside the MIDI receiver callback. The
        # receiver thread remains free to receive the Yamaha SysEx response.
        tempo = None
        getter = getattr(self.core, "get_tempo", None)
        if callable(getter):
            try:
                tempo = getter(self.port)
            except Exception as exc:
                print("Recorder : lecture tempo impossible :", exc)

        if not isinstance(tempo, (int, float)) or not 20 <= tempo <= 300:
            tempo = 120

        with self.lock:
            self.events = []
            self.active_notes.clear()
            self.recording_started_at = None
            self.recording_tempo_bpm = int(round(tempo))
            self.state = STATE_ARMED

        self._speak("Enregistrement prêt.")

    def cancel_arm(self):
        with self.lock:
            if self.state != STATE_ARMED:
                return
            self.state = STATE_IDLE
            self.events = []
            self.active_notes.clear()
            self.recording_started_at = None

        self._speak("Enregistrement annulé.")

    def on_midi_message(self, packet: bytes, timestamp: float):
        if not packet:
            return

        status = packet[0]
        if status >= 0xF0:
            return

        channel = (status & 0x0F) + 1
        if channel != 1:
            return

        command = status & 0xF0
        note_on = (
            command == 0x90
            and len(packet) >= 3
            and packet[2] > 0
        )

        with self.lock:
            if self.state == STATE_ARMED:
                if not note_on:
                    return

                self.state = STATE_RECORDING
                self.recording_started_at = timestamp
                self.events = []
                self.active_notes.clear()
                print(
                    "Recorder : enregistrement démarré "
                    f"(tempo {self.recording_tempo_bpm})"
                )

            if self.state != STATE_RECORDING:
                return

            start = self.recording_started_at
            if start is None:
                return

            elapsed = max(0.0, timestamp - start)
            self.events.append((elapsed, bytes(packet)))

            if command == 0x90 and len(packet) >= 3:
                note = int(packet[1])
                velocity = int(packet[2])
                if velocity > 0:
                    self.active_notes.add(note)
                else:
                    self.active_notes.discard(note)
            elif command == 0x80 and len(packet) >= 3:
                self.active_notes.discard(int(packet[1]))

    def stop_and_save(self):
        with self.lock:
            if self.state != STATE_RECORDING:
                return

            events = list(self.events)
            active_notes = sorted(self.active_notes)
            tempo_bpm = self.recording_tempo_bpm

            self.state = STATE_IDLE
            self.events = []
            self.active_notes.clear()
            self.recording_started_at = None

        if not events:
            self._speak("Enregistrement annulé.")
            return

        # Retour instantané à l'utilisateur avant toute écriture disque ou
        # annonce dynamique de date/numéro.
        self._stop_feedback_now()

        path, number = self._next_recording_path()

        try:
            self._write_midi_file(
                path,
                events,
                active_notes,
                tempo_bpm,
            )
            self._invalidate_recording_files_cache()
            self._write_selected_name(path.name)
        except Exception as exc:
            print("Recorder : erreur sauvegarde :", exc)
            self._speak("Erreur pendant la sauvegarde.")
            return

        when = datetime.now()
        print(
            "Recorder : sauvegardé",
            path.name,
        )
        announcer = getattr(
            self.core,
            "announce_recorder_saved_now",
            None,
        )
        if callable(announcer):
            try:
                announcer(
                    when.day,
                    when.month,
                    number,
                )
                return
            except Exception as exc:
                print(
                    "Recorder : erreur annonce sauvegarde :",
                    exc,
                )

        self._speak(
            "Enregistrement du "
            f"{when.day} {self._month_name(when.month)}, "
            f"numéro {number}, sauvegardé."
        )

    @staticmethod
    def _month_name(month):
        names = (
            "",
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre",
            "décembre",
        )
        return names[int(month)]

    def _write_midi_file(
        self,
        path: Path,
        events,
        active_notes,
        tempo_bpm,
    ):
        ticks_per_beat = 480
        tempo = mido.bpm2tempo(tempo_bpm)

        midi = mido.MidiFile(
            type=0,
            ticks_per_beat=ticks_per_beat,
        )
        track = mido.MidiTrack()
        midi.tracks.append(track)

        track.append(
            mido.MetaMessage(
                "track_name",
                name="CVP Access Recorder",
                time=0,
            )
        )
        track.append(
            mido.MetaMessage(
                "set_tempo",
                tempo=tempo,
                time=0,
            )
        )

        previous = 0.0

        for elapsed, packet in events:
            delta = max(0.0, elapsed - previous)
            previous = elapsed
            ticks = max(
                0,
                int(round(
                    mido.second2tick(
                        delta,
                        ticks_per_beat,
                        tempo,
                    )
                )),
            )

            try:
                message = mido.Message.from_bytes(list(packet))
            except (ValueError, TypeError) as exc:
                print("Recorder : message MIDI ignoré :", packet, exc)
                continue

            message.time = ticks
            track.append(message)

        # Guarantee a clean end even if F15 is pressed while notes/pedal are
        # still held.
        for note in active_notes:
            track.append(
                mido.Message(
                    "note_off",
                    channel=0,
                    note=note,
                    velocity=0,
                    time=0,
                )
            )

        track.append(
            mido.Message(
                "control_change",
                channel=0,
                control=64,
                value=0,
                time=0,
            )
        )
        track.append(
            mido.Message(
                "control_change",
                channel=0,
                control=123,
                value=0,
                time=0,
            )
        )
        track.append(mido.MetaMessage("end_of_track", time=0))

        tmp = path.with_suffix(".tmp")
        midi.save(tmp)
        tmp.replace(path)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _resolve_aplaymidi_port(self, *, refresh=False):
        if not refresh and self.playback_port_cache:
            return self.playback_port_cache

        try:
            proc = subprocess.run(
                ["aplaymidi", "-l"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

        candidates = []
        for line in proc.stdout.splitlines():
            match = re.match(r"^\s*(\d+:\d+)\s+(.+?)\s*$", line)
            if not match:
                continue

            port_id, label = match.groups()
            low = label.lower()
            if "midi through" in low:
                continue

            score = 0
            midi_name = str(getattr(self.core, "MIDI_NAME", "") or "").lower()
            for token in re.findall(r"[a-z0-9]+", midi_name):
                if len(token) >= 4 and token in low:
                    score += 1

            candidates.append((score, port_id, label))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (-item[0], item[1]))
        best = candidates[0]

        if best[0] == 0 and len(candidates) != 1:
            return None

        print("Recorder : sortie lecture ->", best[1], best[2])
        self.playback_port_cache = best[1]
        return best[1]

    def play_selected(self):
        path = self.selected_path()
        if path is None or not path.is_file():
            self._speak("Aucun enregistrement disponible.")
            return

        output_port = self._resolve_aplaymidi_port()
        if output_port is None:
            self._speak("Sortie MIDI de lecture introuvable.")
            return

        try:
            proc = subprocess.Popen(
                [
                    "aplaymidi",
                    "-p",
                    output_port,
                    str(path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as exc:
            print("Recorder : lecture impossible :", exc)
            self._speak("Lecture impossible.")
            return

        with self.lock:
            self.play_generation += 1
            generation = self.play_generation
            self.play_process = proc
            self.state = STATE_PLAYING

        # La relecture démarre immédiatement : pas d'annonce vocale au départ,
        # afin de ne pas retarder ni masquer les premières notes.
        thread = threading.Thread(
            target=self._wait_playback,
            args=(proc, generation),
            daemon=True,
        )
        thread.start()

    def _wait_playback(self, proc, generation):
        _, err = proc.communicate()

        with self.lock:
            if (
                generation != self.play_generation
                or self.play_process is not proc
            ):
                return

            self.play_process = None
            self.state = STATE_IDLE

        if proc.returncode == 0:
            self._speak("Lecture terminée.")
        else:
            # Le port ALSA peut avoir changé après un débranchement USB.
            # Invalider le cache : la prochaine lecture refera la détection.
            self.playback_port_cache = None
            if err:
                print("Recorder : aplaymidi :", err.strip())
            self._speak("Lecture interrompue.")

    def stop_playback(self, *, announce=True):
        with self.lock:
            proc = self.play_process
            if self.state != STATE_PLAYING or proc is None:
                return

            self.play_generation += 1
            self.play_process = None
            self.state = STATE_IDLE

        try:
            proc.terminate()
            proc.wait(timeout=1)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

        sender = getattr(self.core, "send_sysex", None)
        if callable(sender):
            try:
                sender(self.port, [0xB0, 64, 0])
                sender(self.port, [0xB0, 123, 0])
            except Exception:
                pass

        if announce:
            self._speak("Lecture arrêtée.")

    def close(self):
        with self.lock:
            timer = self.press_timer
            self.press_timer = None
            self.key_pressed = False

            navigation_timers = list(
                self.navigation_timers.values()
            )
            self.navigation_timers.clear()
            self.navigation_pressed.clear()
            self.navigation_cues.clear()

        if timer is not None:
            timer.cancel()

        for timer in navigation_timers:
            timer.cancel()

        self.stop_playback(announce=False)
