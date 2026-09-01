#!/usr/bin/env python3
"""Speech policy for CVP Access: asynchronous pregenerated/hybrid/runtime Piper."""

from __future__ import annotations

import atexit
import hashlib
import json
import os
import queue
import subprocess
import tempfile
import threading
from pathlib import Path


STYLE_LABELS = [
    "Rythme 1", "Rythme 2", "Basse", "Accord 1",
    "Accord 2", "Pad", "Phrase 1", "Phrase 2",
]


class SpeechManager:
    """Synthèse/lecture dans un thread dédié pour ne pas bloquer le clavier."""

    def __init__(self, core, speech_config):
        self.core = core
        self.config = speech_config
        self.worker = None
        self.temp_files = []

        self.worker_script = Path(__file__).resolve().with_name(
            "cvp_piper_worker.py"
        )
        self.piper_python = Path(
            os.environ.get(
                "CVP_PIPER_PYTHON",
                Path.home() / ".local/share/cvp-access/piper-env/bin/python",
            )
        )
        self.model = Path(
            os.environ.get(
                "CVP_PIPER_MODEL",
                Path.home() / "piper-voices" / f"{speech_config.voice}.onnx",
            )
        )
        self.cache_dir = Path.home() / ".cache/cvp-access/tts"
        if self.config.cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.voice_metadata = self.core.VOICE_DIR / ".cvp_voice_generation.json"
        self.static_profile_matches = self._check_static_profile()
        self._profile_warning_printed = False

        self.speech_queue = queue.Queue(maxsize=16)

        # Générations utilisées pour rendre obsolètes les anciennes annonces
        # d'une même famille (par exemple Volume Song 81, 82, 83...).
        self._replace_generation = {}
        self._replace_lock = threading.Lock()

        self._closing = False
        self.speech_thread = threading.Thread(
            target=self._speech_loop,
            daemon=True,
            name="cvp-speech",
        )
        self.speech_thread.start()

        # CVP Access : précharge Piper au démarrage.
        # Évite que la première annonce dynamique fasse attendre
        # l'utilisateur pendant le chargement du modèle.
        if self.config.mode in {"hybrid", "runtime"}:
            print("Préchargement Piper...")
            self._ensure_worker()

        atexit.register(self.close)

    def _check_static_profile(self):
        if self.voice_metadata.is_file():
            try:
                data = json.loads(
                    self.voice_metadata.read_text(encoding="utf-8")
                )
                return (
                    data.get("voice") == self.config.voice
                    and float(data.get("length_scale"))
                    == float(self.config.length_scale)
                )
            except Exception:
                return False

        return (
            self.config.voice == "fr_FR-siwis-medium"
            and abs(float(self.config.length_scale) - 0.85) < 1e-9
        )

    def _warn_profile_mismatch(self):
        if self._profile_warning_printed:
            return
        self._profile_warning_printed = True
        print(
            "Banque WAV ignorée : profil Piper différent du TOML. "
            "Utilisation de Piper dynamique / régénération recommandée."
        )

    def _stop_piper_worker(self):
        if self.worker is not None and self.worker.poll() is None:
            try:
                self.worker.stdin.close()
            except Exception:
                pass
            try:
                self.worker.terminate()
                self.worker.wait(timeout=1)
            except Exception:
                try:
                    self.worker.kill()
                except Exception:
                    pass
        self.worker = None

    def close(self):
        if self._closing:
            return
        self._closing = True

        try:
            self.speech_queue.put_nowait(None)
        except queue.Full:
            pass

        self._stop_piper_worker()

        for path in self.temp_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        self.temp_files.clear()

    def _enqueue(self, item):
        if self._closing:
            return False

        try:
            self.speech_queue.put_nowait(item)
            return True
        except queue.Full:
            # Une annonce ancienne est moins utile que la dernière commande.
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                pass

            try:
                self.speech_queue.put_nowait(item)
                return True
            except queue.Full:
                return False

    def _new_replace_generation(self, replace_key):
        if replace_key is None:
            return None

        with self._replace_lock:
            generation = (
                self._replace_generation.get(
                    replace_key,
                    0,
                )
                + 1
            )
            self._replace_generation[
                replace_key
            ] = generation

        return generation

    def _is_current_generation(
        self,
        replace_key,
        generation,
    ):
        if replace_key is None:
            return True

        with self._replace_lock:
            return (
                self._replace_generation.get(
                    replace_key
                )
                == generation
            )

    def speak(
        self,
        text: str,
        wav_path: Path | None = None,
        replace_key: str | None = None,
    ):
        generation = self._new_replace_generation(
            replace_key
        )

        return self._enqueue(
            (
                "speak",
                text,
                Path(wav_path) if wav_path is not None else None,
                replace_key,
                generation,
            )
        )

    def speak_sequence(
        self,
        text: str,
        files,
        replace_key: str | None = None,
    ):
        generation = self._new_replace_generation(
            replace_key
        )

        return self._enqueue(
            (
                "sequence",
                text,
                [Path(p) for p in files],
                replace_key,
                generation,
            )
        )

    def _speech_loop(self):
        while True:
            item = self.speech_queue.get()

            try:
                if item is None:
                    return

                kind = item[0]

                if kind == "speak":
                    (
                        _,
                        text,
                        wav_path,
                        replace_key,
                        generation,
                    ) = item

                    # Une annonce plus récente de la même famille existe :
                    # on ignore instantanément celle-ci.
                    if not self._is_current_generation(
                        replace_key,
                        generation,
                    ):
                        continue

                    self._speak_now(
                        text,
                        wav_path,
                    )

                elif kind == "sequence":
                    (
                        _,
                        text,
                        files,
                        replace_key,
                        generation,
                    ) = item

                    if not self._is_current_generation(
                        replace_key,
                        generation,
                    ):
                        continue

                    self._speak_sequence_now(
                        text,
                        files,
                    )

            except Exception as exc:
                print("Erreur thread vocal :", exc)

            finally:
                self.speech_queue.task_done()

    def _play_wav(self, path: Path):
        if not path.is_file():
            return False

        scaled = self.core.create_scaled_wav(
            path,
            self.core.voice_volume,
        )
        if (
            not self.config.cache
            and path in self.temp_files
            and scaled != path
            and scaled not in self.temp_files
        ):
            self.temp_files.append(Path(scaled))

        self.core.start_audio(scaled)
        return True

    def _ensure_worker(self):
        if self.worker is not None and self.worker.poll() is None:
            return True

        if not self.piper_python.is_file():
            print("Piper runtime absent :", self.piper_python)
            return False

        if (
            not self.model.is_file()
            or not Path(str(self.model) + ".json").is_file()
        ):
            print("Modèle Piper absent, téléchargement :", self.config.voice)
            self.model.parent.mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                [
                    str(self.piper_python),
                    "-m",
                    "piper.download_voices",
                    self.config.voice,
                    "--data-dir",
                    str(self.model.parent),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0 or not self.model.is_file():
                print("Téléchargement Piper impossible :", result.stderr.strip())
                return False

        if not self.worker_script.is_file():
            print("Worker Piper absent :", self.worker_script)
            return False

        self.worker = subprocess.Popen(
            [
                str(self.piper_python),
                str(self.worker_script),
                "--model",
                str(self.model),
                "--length-scale",
                str(self.config.length_scale),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        line = self.worker.stdout.readline()
        if not line:
            error = self.worker.stderr.read().strip()
            print("Piper runtime non démarré :", error or "réponse vide")
            self._stop_piper_worker()
            return False

        try:
            status = json.loads(line)
        except json.JSONDecodeError:
            print("Réponse Piper invalide :", line.strip())
            self._stop_piper_worker()
            return False

        if not status.get("ready"):
            print("Piper runtime non prêt :", status.get("error", "inconnu"))
            self._stop_piper_worker()
            return False

        print("Piper runtime chargé :", self.config.voice)
        return True

    def _runtime_output(self, text: str):
        if self.config.cache:
            key = "|".join(
                [
                    self.config.voice,
                    str(self.config.length_scale),
                    text,
                ]
            )
            digest = hashlib.sha256(
                key.encode("utf-8")
            ).hexdigest()[:24]
            return self.cache_dir / f"tts_{digest}.wav"

        fd, name = tempfile.mkstemp(
            prefix="cvp-access-tts-",
            suffix=".wav",
        )
        os.close(fd)

        path = Path(name)
        path.unlink(missing_ok=True)
        self.temp_files.append(path)
        return path

    def _synthesize(self, text: str):
        output = self._runtime_output(text)

        if output.is_file():
            return output

        if not self._ensure_worker():
            return None

        request = json.dumps(
            {
                "text": text,
                "output": str(output),
            },
            ensure_ascii=False,
        )

        try:
            self.worker.stdin.write(request + "\n")
            self.worker.stdin.flush()
            line = self.worker.stdout.readline()
            response = json.loads(line)
        except Exception as exc:
            print("Erreur communication Piper :", exc)
            self._stop_piper_worker()
            return None

        if not response.get("ok"):
            print(
                "Erreur synthèse Piper :",
                response.get("error", "inconnue"),
            )
            return None

        return output if output.is_file() else None

    def _speak_now(self, text: str, wav_path: Path | None = None):
        mode = self.config.mode

        if mode in {"pregenerated", "hybrid"} and wav_path is not None:
            if self.static_profile_matches:
                if self._play_wav(Path(wav_path)):
                    return True
            elif Path(wav_path).is_file():
                self._warn_profile_mismatch()

        if mode == "pregenerated":
            if not self.static_profile_matches:
                self._warn_profile_mismatch()
            elif wav_path is not None:
                print("WAV absent :", wav_path)
            return False

        output = self._synthesize(text)

        if output is None:
            if mode == "hybrid" and wav_path is not None:
                return self._play_wav(Path(wav_path))
            return False

        return self._play_wav(output)

    def _speak_sequence_now(self, text: str, files):
        files = [Path(p) for p in files]

        if self.config.mode in {"pregenerated", "hybrid"}:
            if (
                self.static_profile_matches
                and files
                and all(p.is_file() for p in files)
            ):
                self.core.play_voice_sequence(files)
                return True

            if (
                not self.static_profile_matches
                and any(p.is_file() for p in files)
            ):
                self._warn_profile_mismatch()

        if self.config.mode == "pregenerated":
            missing = [str(p) for p in files if not p.is_file()]
            if missing:
                print("Fragments WAV absents :", ", ".join(missing))
            return False

        return self._speak_now(text)


def install_speech_hooks(core, speech_config):
    """Installe toutes les annonces sans modifier le moteur MIDI/SysEx."""

    manager = SpeechManager(core, speech_config)
    voice_dir = core.VOICE_DIR

    def announce_track(track, active):
        state = "on" if active else "off"
        text = f"Piste {track} {'activée' if active else 'coupée'}."
        return manager.speak(
            text,
            voice_dir / f"piste_{track:02d}_{state}.wav",
        )

    def announce_tempo(tempo):
        return manager.speak(
            f"Tempo {tempo}.",
            voice_dir / "tempo" / f"tempo_{tempo:03d}.wav",
        )

    def announce_transpose(value):
        if value < 0:
            name = f"transpose_m{abs(value):02d}.wav"
            text = f"Transpose moins {abs(value)}."
        elif value > 0:
            name = f"transpose_p{value:02d}.wav"
            text = f"Transpose plus {value}."
        else:
            name = "transpose_000.wav"
            text = "Transpose zéro."

        return manager.speak(
            text,
            voice_dir / "transpose" / name,
        )

    def announce_volume():
        value = core.voice_volume
        return manager.speak(
            f"Volume guide vocal {value} pour cent.",
            voice_dir / "volume" / f"volume_{value:03d}.wav",
            replace_key="voice_volume",
        )

    def announce_style_volume(value):
        return manager.speak(
            f"Accompagnement {value}.",
            voice_dir / "style_volume" / f"style_volume_{value:03d}.wav",
            replace_key="style_volume",
        )

    def announce_song_volume(value):
        return manager.speak(
            f"Volume Song {value}.",
            voice_dir / "song_volume" / f"song_volume_{value:03d}.wav",
            replace_key="song_volume",
        )

    def announce_main_volume(value):
        return manager.speak(
            f"Volume Main {value}.",
            voice_dir / "main_volume" / f"main_volume_{value:03d}.wav",
            replace_key="main_volume",
        )

    def announce_style_part(part, active):
        state = "on" if active else "off"
        label = STYLE_LABELS[part]
        stem = core.STYLE_PART_NAMES[part]
        return manager.speak(
            f"{label} {'activé' if active else 'désactivé'}.",
            voice_dir / "style_part" / f"{stem}_{state}.wav",
        )

    def announce_style_play_state(active):
        return manager.speak(
            "Style démarré." if active else "Style arrêté.",
            voice_dir
            / "style_transport"
            / ("start.wav" if active else "stop.wav"),
        )

    def announce_action_help(text):
        return manager.speak(
            text,
            replace_key="action_help",
        )

    def announce_voice_part(name, active):
        state = "on" if active else "off"
        label = "Dual" if name == "layer" else "Left"
        return manager.speak(
            f"{label} {'activé' if active else 'désactivé'}.",
            voice_dir / "voice_part" / f"{name}_{state}.wav",
        )

    def announce_song_state(state):
        mapping = {
            core.SONG_STOP: ("Arrêt", "stop.wav"),
            core.SONG_PLAY: ("Lecture", "lecture.wav"),
            core.SONG_PAUSE: ("Pause", "pause.wav"),
        }
        item = mapping.get(state)
        if item is None:
            return False

        text, filename = item
        return manager.speak(
            text,
            voice_dir / "transport" / filename,
        )

    def announce_song_position(measure, beat):
        files = [voice_dir / "words" / "mesure.wav"]

        if 0 <= measure <= 100:
            files.append(
                voice_dir / "numbers" / f"number_{measure:03d}.wav"
            )

        files.append(voice_dir / "words" / "temps.wav")

        if 0 <= beat <= 100:
            files.append(
                voice_dir / "numbers" / f"number_{beat:03d}.wav"
            )

        return manager.speak_sequence(
            f"Mesure {measure}, temps {beat}.",
            files,
        )

    def announce_measure(measure):
        return manager.speak(f"Mesure {measure}.")

    def announce_no_song():
        return manager.speak(
            "Pas de Song chargé.",
            voice_dir / "song" / "no_song.wav",
        )

    def announce_song_detection_error():
        return manager.speak(
            "Impossible de vérifier le Song.",
            voice_dir / "song" / "detection_error.wav",
        )

    def announce_goto_measure_prompt():
        return manager.speak(
            "Saisir le numéro de mesure puis Entrée.",
            voice_dir / "song" / "goto_prompt.wav",
        )

    def announce_goto_measure_cancelled():
        return manager.speak(
            "Saisie mesure annulée.",
            voice_dir / "song" / "goto_cancelled.wav",
        )

    def announce_invalid_measure():
        return manager.speak(
            "Mesure invalide.",
            voice_dir / "song" / "invalid_measure.wav",
        )

    def announce_loop_point_a(measure):
        return manager.speak(f"Point A mesure {measure}.")

    def announce_loop_point_b(measure):
        return manager.speak(f"Point B mesure {measure}.")

    def announce_loop_point_a_missing():
        return manager.speak(
            "Point A non défini.",
            voice_dir / "song" / "loop_a_missing.wav",
        )

    def announce_loop_point_b_invalid():
        return manager.speak(
            "Point B invalide.",
            voice_dir / "song" / "loop_b_invalid.wav",
        )

    def announce_loop_points_missing():
        return manager.speak(
            "Points A et B non définis.",
            voice_dir / "song" / "loop_points_missing.wav",
        )

    def announce_loop_state(active, point_a, point_b):
        if active:
            text = (
                f"Boucle activée de la mesure "
                f"{point_a} à la mesure {point_b}."
            )
        else:
            text = "Boucle désactivée."
        return manager.speak(text)

    core.announce_track = announce_track
    core.announce_tempo = announce_tempo
    core.announce_transpose = announce_transpose
    core.announce_volume = announce_volume
    core.announce_style_volume = announce_style_volume
    core.announce_song_volume = announce_song_volume
    core.announce_main_volume = announce_main_volume
    core.announce_style_part = announce_style_part
    core.announce_style_play_state = announce_style_play_state
    core.announce_action_help = announce_action_help
    core.announce_voice_part = announce_voice_part
    core.announce_song_state = announce_song_state
    core.announce_song_position = announce_song_position
    core.announce_measure = announce_measure
    core.announce_no_song = announce_no_song
    core.announce_song_detection_error = announce_song_detection_error
    core.announce_goto_measure_prompt = announce_goto_measure_prompt
    core.announce_goto_measure_cancelled = announce_goto_measure_cancelled
    core.announce_invalid_measure = announce_invalid_measure
    core.announce_loop_point_a = announce_loop_point_a
    core.announce_loop_point_b = announce_loop_point_b
    core.announce_loop_point_a_missing = announce_loop_point_a_missing
    core.announce_loop_point_b_invalid = announce_loop_point_b_invalid
    core.announce_loop_points_missing = announce_loop_points_missing
    core.announce_loop_state = announce_loop_state

    return manager
