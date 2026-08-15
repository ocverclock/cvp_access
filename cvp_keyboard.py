#!/usr/bin/env python3
"""
CVP Access - configurable keyboard router.

This module translates evdev key events into a fixed catalogue of CVP Access
actions.  The TOML file can select actions, but can never execute Python code.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from evdev import ecodes


# ---------------------------------------------------------------------------
# AZERTY logical names -> Linux evdev physical codes
# ---------------------------------------------------------------------------
#
# Linux evdev key codes use physical/QWERTY-style names.  CVP Access exposes
# names printed on a French AZERTY keyboard instead.
#
KEY_NAME_TO_CODE = {
    # AZERTY first letter row
    "A": ecodes.KEY_Q,
    "Z": ecodes.KEY_W,
    "E": ecodes.KEY_E,
    "R": ecodes.KEY_R,
    "T": ecodes.KEY_T,
    "Y": ecodes.KEY_Y,
    "U": ecodes.KEY_U,
    "I": ecodes.KEY_I,
    "O": ecodes.KEY_O,
    "P": ecodes.KEY_P,

    # AZERTY second letter row
    "Q": ecodes.KEY_A,
    "S": ecodes.KEY_S,
    "D": ecodes.KEY_D,
    "F": ecodes.KEY_F,
    "G": ecodes.KEY_G,
    "H": ecodes.KEY_H,
    "J": ecodes.KEY_J,
    "K": ecodes.KEY_K,
    "L": ecodes.KEY_L,
    "M": ecodes.KEY_SEMICOLON,

    # AZERTY third letter row
    "W": ecodes.KEY_Z,
    "X": ecodes.KEY_X,
    "C": ecodes.KEY_C,
    "V": ecodes.KEY_V,
    "B": ecodes.KEY_B,
    "N": ecodes.KEY_N,

    # Physical top row.  On French AZERTY:
    # TOP1=&/1 TOP2=é/2 TOP3="/3 TOP4='/4 TOP5=(/5
    # TOP6=-/6 TOP7=è/7 TOP8=_/8 TOP9=ç/9 TOP0=à/0
    "TOP1": ecodes.KEY_1,
    "TOP2": ecodes.KEY_2,
    "TOP3": ecodes.KEY_3,
    "TOP4": ecodes.KEY_4,
    "TOP5": ecodes.KEY_5,
    "TOP6": ecodes.KEY_6,
    "TOP7": ecodes.KEY_7,
    "TOP8": ecodes.KEY_8,
    "TOP9": ecodes.KEY_9,
    "TOP0": ecodes.KEY_0,

    # Remaining French AZERTY printable keys
    "RPAREN": ecodes.KEY_MINUS,          # ) / °
    "EQUAL": ecodes.KEY_EQUAL,           # = / +
    "CARET": ecodes.KEY_LEFTBRACE,       # ^ / ¨
    "DOLLAR": ecodes.KEY_RIGHTBRACE,     # $ / £
    "U_GRAVE": ecodes.KEY_APOSTROPHE,    # ù / %
    "ASTERISK": ecodes.KEY_BACKSLASH,    # * / µ
    "COMMA": ecodes.KEY_M,               # , / ?
    "SEMICOLON": ecodes.KEY_COMMA,       # ; / .
    "COLON": ecodes.KEY_DOT,             # : / /
    "EXCLAMATION": ecodes.KEY_SLASH,     # ! / §
    "LESS": ecodes.KEY_102ND,            # < / >

    # Function keys
    **{f"F{i}": getattr(ecodes, f"KEY_F{i}") for i in range(1, 13)},

    # Navigation / common keys
    "ESC": ecodes.KEY_ESC,
    "TAB": ecodes.KEY_TAB,
    "SPACE": ecodes.KEY_SPACE,
    "ENTER": ecodes.KEY_ENTER,
    "BACKSPACE": ecodes.KEY_BACKSPACE,
    "PRINT": ecodes.KEY_SYSRQ,
    "SCROLLLOCK": ecodes.KEY_SCROLLLOCK,
    "PAUSE": ecodes.KEY_PAUSE,
    "NUMLOCK": ecodes.KEY_NUMLOCK,
    "UP": ecodes.KEY_UP,
    "DOWN": ecodes.KEY_DOWN,
    "LEFT": ecodes.KEY_LEFT,
    "RIGHT": ecodes.KEY_RIGHT,
    "PAGEUP": ecodes.KEY_PAGEUP,
    "PAGEDOWN": ecodes.KEY_PAGEDOWN,
    "HOME": ecodes.KEY_HOME,
    "END": ecodes.KEY_END,
    "INSERT": ecodes.KEY_INSERT,
    "DELETE": ecodes.KEY_DELETE,

    # Numeric keypad
    "KP0": ecodes.KEY_KP0,
    "KP1": ecodes.KEY_KP1,
    "KP2": ecodes.KEY_KP2,
    "KP3": ecodes.KEY_KP3,
    "KP4": ecodes.KEY_KP4,
    "KP5": ecodes.KEY_KP5,
    "KP6": ecodes.KEY_KP6,
    "KP7": ecodes.KEY_KP7,
    "KP8": ecodes.KEY_KP8,
    "KP9": ecodes.KEY_KP9,
    "KPENTER": ecodes.KEY_KPENTER,
    "KPPLUS": ecodes.KEY_KPPLUS,
    "KPMINUS": ecodes.KEY_KPMINUS,
    "KPDOT": ecodes.KEY_KPDOT,
    "KPSLASH": ecodes.KEY_KPSLASH,
    "KPASTERISK": ecodes.KEY_KPASTERISK,
}

# Friendly aliases accepted in configuration files.
KEY_ALIASES = {
    "1": "TOP1",
    "2": "TOP2",
    "3": "TOP3",
    "4": "TOP4",
    "5": "TOP5",
    "6": "TOP6",
    "7": "TOP7",
    "8": "TOP8",
    "9": "TOP9",
    "0": "TOP0",
    "AMPERSAND": "TOP1",
    "E_ACUTE": "TOP2",
    "QUOTE": "TOP3",
    "APOSTROPHE": "TOP4",
    "LPAREN": "TOP5",
    "MINUS": "TOP6",
    "E_GRAVE": "TOP7",
    "UNDERSCORE": "TOP8",
    "C_CEDILLA": "TOP9",
    "A_GRAVE": "TOP0",
    "&": "TOP1",
    "É": "TOP2",
    '"': "TOP3",
    "'": "TOP4",
    "(": "TOP5",
    "-": "TOP6",
    "È": "TOP7",
    "_": "TOP8",
    "Ç": "TOP9",
    "À": "TOP0",
    ")": "RPAREN",
    "=": "EQUAL",
    "^": "CARET",
    "$": "DOLLAR",
    "Ù": "U_GRAVE",
    "*": "ASTERISK",
    ",": "COMMA",
    ";": "SEMICOLON",
    ":": "COLON",
    "!": "EXCLAMATION",
    "<": "LESS",
    "RETURN": "ENTER",
    "PGUP": "PAGEUP",
    "PGDN": "PAGEDOWN",
    "DEL": "DELETE",
    "INS": "INSERT",
}

CODE_TO_KEY_NAME = {}
for _name, _code in KEY_NAME_TO_CODE.items():
    # The canonical name is the first explicit logical name.
    CODE_TO_KEY_NAME.setdefault(_code, _name)


# ---------------------------------------------------------------------------
# Modifiers
# ---------------------------------------------------------------------------

MODIFIER_CODES = {
    ecodes.KEY_LEFTSHIFT: "SHIFT",
    ecodes.KEY_RIGHTSHIFT: "SHIFT",
    ecodes.KEY_LEFTCTRL: "CTRL",
    ecodes.KEY_RIGHTCTRL: "CTRL",
    ecodes.KEY_LEFTALT: "ALT",
    ecodes.KEY_RIGHTALT: "ALTGR",
    ecodes.KEY_LEFTMETA: "META",
    ecodes.KEY_RIGHTMETA: "META",
}

MODIFIER_ORDER = ("CTRL", "ALT", "ALTGR", "SHIFT", "META", "CAPS")
VALID_MODIFIERS = set(MODIFIER_ORDER)


# ---------------------------------------------------------------------------
# Action catalogue
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ActionSpec:
    parameter_required: bool = False
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    description: str = ""


ACTION_SPECS = {
    "song_track_toggle": ActionSpec(
        True, 1, 16, "Bascule ON/OFF d'une piste Song"
    ),
    "style_part_toggle": ActionSpec(
        True, 1, 8, "Bascule ON/OFF d'une partie Style"
    ),
    "layer_toggle": ActionSpec(description="Bascule Layer / Dual"),
    "left_toggle": ActionSpec(description="Bascule Left"),
    "announce_tempo": ActionSpec(description="Annonce le tempo courant"),
    "announce_transpose": ActionSpec(description="Annonce le transpose courant"),
    "song_play_pause": ActionSpec(description="Lecture / pause du Song"),
    "song_stop": ActionSpec(description="Stop du Song"),
    "song_position": ActionSpec(description="Annonce mesure et temps"),
    "voice_volume_up": ActionSpec(description="Augmente le volume vocal"),
    "voice_volume_down": ActionSpec(description="Diminue le volume vocal"),
    "style_volume_up": ActionSpec(description="Augmente le volume Style"),
    "style_volume_down": ActionSpec(description="Diminue le volume Style"),
    "restart": ActionSpec(description="Quitte CVP Access pour redémarrage systemd"),
}


@dataclass(frozen=True)
class ActionInvocation:
    name: str
    parameter: Optional[int] = None

    @property
    def text(self) -> str:
        if self.parameter is None:
            return self.name
        return f"{self.name}:{self.parameter}"


@dataclass(frozen=True)
class SpeechConfig:
    mode: str = "hybrid"
    generation: str = "configured"
    cache: bool = True
    voice: str = "fr_FR-siwis-medium"
    length_scale: float = 0.85


@dataclass
class KeyboardConfig:
    bindings: dict[str, ActionInvocation]
    source: Path
    caps_lock_layer: bool = True
    caps_fallback_to_base: bool = True
    speech: SpeechConfig = SpeechConfig()
    issues: list[str] | None = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


# Exact built-in fallback reproducing v1.4.1.
BUILTIN_BINDINGS = {
    "TOP1": "style_part_toggle:1",
    "TOP2": "style_part_toggle:2",
    "TOP3": "style_part_toggle:3",
    "TOP4": "style_part_toggle:4",
    "TOP5": "style_part_toggle:5",
    "TOP6": "style_part_toggle:6",
    "TOP7": "style_part_toggle:7",
    "TOP8": "style_part_toggle:8",
    "TOP9": "layer_toggle",
    "TOP0": "left_toggle",

    "A": "song_track_toggle:1",
    "Z": "song_track_toggle:2",
    "E": "song_track_toggle:3",
    "R": "song_track_toggle:4",
    "T": "song_track_toggle:5",
    "Y": "song_track_toggle:6",
    "U": "song_track_toggle:7",
    "I": "song_track_toggle:8",

    "Q": "song_track_toggle:9",
    "S": "song_track_toggle:10",
    "D": "song_track_toggle:11",
    "F": "song_track_toggle:12",
    "G": "song_track_toggle:13",
    "H": "song_track_toggle:14",
    "J": "song_track_toggle:15",
    "K": "song_track_toggle:16",

    "F1": "announce_tempo",
    "F2": "announce_transpose",
    "SPACE": "song_play_pause",
    "ENTER": "song_stop",
    "P": "song_position",
    "UP": "voice_volume_up",
    "DOWN": "voice_volume_down",
    "PAGEUP": "style_volume_up",
    "PAGEDOWN": "style_volume_down",
    "ESC": "restart",
}


def parse_action(value: str) -> ActionInvocation:
    value = value.strip()
    if not value:
        raise ValueError("action vide")

    if ":" in value:
        name, raw_parameter = value.split(":", 1)
        name = name.strip().lower()
        raw_parameter = raw_parameter.strip()
        try:
            parameter = int(raw_parameter)
        except ValueError as exc:
            raise ValueError(
                f"paramètre non numérique dans {value!r}"
            ) from exc
    else:
        name = value.lower()
        parameter = None

    spec = ACTION_SPECS.get(name)
    if spec is None:
        raise ValueError(f"action inconnue {name!r}")

    if spec.parameter_required and parameter is None:
        raise ValueError(f"{name} demande un paramètre")

    if not spec.parameter_required and parameter is not None:
        raise ValueError(f"{name} n'accepte pas de paramètre")

    if parameter is not None:
        if spec.minimum is not None and parameter < spec.minimum:
            raise ValueError(
                f"{name}:{parameter} inférieur à {spec.minimum}"
            )
        if spec.maximum is not None and parameter > spec.maximum:
            raise ValueError(
                f"{name}:{parameter} supérieur à {spec.maximum}"
            )

    return ActionInvocation(name, parameter)


def normalize_key_name(name: str) -> str:
    name = name.strip().upper().replace(" ", "")
    name = KEY_ALIASES.get(name, name)
    if name not in KEY_NAME_TO_CODE:
        raise ValueError(f"touche inconnue {name!r}")
    return name


def normalize_combo(combo: str) -> str:
    parts = [part.strip().upper() for part in combo.split("+") if part.strip()]
    if not parts:
        raise ValueError("combinaison vide")

    raw_key = parts[-1]
    raw_modifiers = parts[:-1]

    modifiers = []
    for modifier in raw_modifiers:
        if modifier not in VALID_MODIFIERS:
            raise ValueError(f"modificateur inconnu {modifier!r}")
        if modifier in modifiers:
            raise ValueError(f"modificateur dupliqué {modifier!r}")
        modifiers.append(modifier)

    key_name = normalize_key_name(raw_key)
    ordered = [m for m in MODIFIER_ORDER if m in modifiers]
    return "+".join(ordered + [key_name])


def _parse_bindings(raw_bindings: dict) -> tuple[dict[str, ActionInvocation], list[str]]:
    bindings: dict[str, ActionInvocation] = {}
    issues: list[str] = []

    for raw_combo, raw_action in raw_bindings.items():
        if not isinstance(raw_combo, str):
            issues.append(f"clé TOML non textuelle: {raw_combo!r}")
            continue
        if not isinstance(raw_action, str):
            issues.append(f"{raw_combo}: l'action doit être du texte")
            continue

        try:
            combo = normalize_combo(raw_combo)
            invocation = parse_action(raw_action)
        except ValueError as exc:
            issues.append(f"{raw_combo}: {exc}")
            continue

        if combo in bindings:
            issues.append(
                f"{raw_combo}: combinaison dupliquée après normalisation ({combo})"
            )
            continue

        bindings[combo] = invocation

    return bindings, issues


def builtin_config() -> KeyboardConfig:
    parsed, issues = _parse_bindings(BUILTIN_BINDINGS)
    return KeyboardConfig(
        bindings=parsed,
        source=Path("<builtin-v1.4.1>"),
        caps_lock_layer=True,
        caps_fallback_to_base=True,
        issues=issues,
    )


def read_config_file(path: Path) -> KeyboardConfig:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    general = data.get("general", {})
    speech_raw = data.get("speech", {})
    keys = data.get("keys", {})

    if not isinstance(general, dict):
        raise ValueError("[general] doit être une table TOML")
    if not isinstance(speech_raw, dict):
        raise ValueError("[speech] doit être une table TOML")
    if not isinstance(keys, dict):
        raise ValueError("[keys] doit être une table TOML")

    bindings, issues = _parse_bindings(keys)

    format_version = general.get("format_version", 1)
    if format_version not in {1, 2}:
        issues.append("general.format_version non supporté (valeurs connues : 1 ou 2)")

    layout = general.get("layout", "azerty")
    if layout != "azerty":
        issues.append("general.layout : seule la valeur azerty est supportée actuellement")

    caps_lock_layer = general.get("caps_lock_layer", True)
    caps_fallback_to_base = general.get("caps_fallback_to_base", True)

    if not isinstance(caps_lock_layer, bool):
        issues.append("general.caps_lock_layer doit être true ou false")
        caps_lock_layer = True

    if not isinstance(caps_fallback_to_base, bool):
        issues.append("general.caps_fallback_to_base doit être true ou false")
        caps_fallback_to_base = True

    mode = speech_raw.get("mode", "hybrid")
    if mode not in {"pregenerated", "hybrid", "runtime"}:
        issues.append("speech.mode doit être pregenerated, hybrid ou runtime")
        mode = "hybrid"

    generation = speech_raw.get("generation", "configured")
    if generation not in {"configured", "core", "all"}:
        issues.append("speech.generation doit être configured, core ou all")
        generation = "configured"

    cache = speech_raw.get("cache", True)
    if not isinstance(cache, bool):
        issues.append("speech.cache doit être true ou false")
        cache = True

    voice = speech_raw.get("voice", "fr_FR-siwis-medium")
    if not isinstance(voice, str) or not voice.strip():
        issues.append("speech.voice doit être un nom de voix Piper non vide")
        voice = "fr_FR-siwis-medium"
    else:
        voice = voice.strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", voice):
            issues.append("speech.voice contient des caractères non autorisés")
            voice = "fr_FR-siwis-medium"

    length_scale = speech_raw.get("length_scale", 0.85)
    if not isinstance(length_scale, (int, float)) or isinstance(length_scale, bool):
        issues.append("speech.length_scale doit être un nombre")
        length_scale = 0.85
    else:
        length_scale = float(length_scale)
        if not 0.25 <= length_scale <= 3.0:
            issues.append("speech.length_scale doit être compris entre 0.25 et 3.0")
            length_scale = 0.85

    speech = SpeechConfig(
        mode=mode,
        generation=generation,
        cache=cache,
        voice=voice,
        length_scale=length_scale,
    )

    if not bindings:
        issues.append("aucune affectation clavier valide")

    return KeyboardConfig(
        bindings=bindings,
        source=path,
        caps_lock_layer=caps_lock_layer,
        caps_fallback_to_base=caps_fallback_to_base,
        speech=speech,
        issues=issues,
    )


def load_keyboard_config(
    path: Path,
    fallback_path: Optional[Path] = None,
) -> KeyboardConfig:
    """
    Runtime loader.

    A malformed TOML file never prevents CVP Access from starting:
    - active config is tried first;
    - optional default file is tried next;
    - built-in v1.4.1 mapping is the final safety net.

    Individual invalid bindings are skipped and reported, while valid bindings
    remain usable.
    """
    candidates = [path]
    if fallback_path is not None and fallback_path != path:
        candidates.append(fallback_path)

    failures = []

    for candidate in candidates:
        if not candidate.is_file():
            failures.append(f"{candidate}: fichier absent")
            continue

        try:
            config = read_config_file(candidate)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
            failures.append(f"{candidate}: {exc}")
            continue

        if config.bindings:
            if failures:
                config.issues = failures + (config.issues or [])
            return config

        failures.extend(config.issues or [])

    config = builtin_config()
    config.issues = failures + (config.issues or [])
    return config


class KeyRouter:
    """Stateful evdev router for modifiers and the Caps Lock action layer."""

    def __init__(self, keyboard, config: KeyboardConfig):
        self.keyboard = keyboard
        self.config = config
        self.pressed_modifier_codes: set[int] = set()
        self.caps_active = False

        # CVP Access owns Caps Lock as an action-layer switch.  Resetting it at
        # startup makes behaviour deterministic after a service restart.
        if self.config.caps_lock_layer:
            self._set_caps_led(False)

    def _set_caps_led(self, enabled: bool):
        try:
            self.keyboard.set_led(ecodes.LED_CAPSL, 1 if enabled else 0)
        except (AttributeError, OSError):
            pass

    def _combo_for(self, key_name: str, include_caps: bool = True) -> str:
        modifiers = {
            MODIFIER_CODES[code]
            for code in self.pressed_modifier_codes
            if code in MODIFIER_CODES
        }
        if include_caps and self.caps_active:
            modifiers.add("CAPS")
        ordered = [m for m in MODIFIER_ORDER if m in modifiers]
        return "+".join(ordered + [key_name])

    def process_event(self, event) -> Optional[ActionInvocation]:
        if event.type != ecodes.EV_KEY:
            return None

        modifier = MODIFIER_CODES.get(event.code)
        if modifier is not None:
            if event.value == 1:
                self.pressed_modifier_codes.add(event.code)
            elif event.value == 0:
                self.pressed_modifier_codes.discard(event.code)
            return None

        if (
            event.code == ecodes.KEY_CAPSLOCK
            and self.config.caps_lock_layer
        ):
            if event.value == 1:
                self.caps_active = not self.caps_active
                self._set_caps_led(self.caps_active)
                print(
                    "Couche CAPS :",
                    "ON" if self.caps_active else "OFF"
                )
            return None

        # 0 = release, 1 = press, 2 = auto-repeat.
        # Long press / repeat actions are deliberately not implemented yet.
        if event.value != 1:
            return None

        key_name = CODE_TO_KEY_NAME.get(event.code)
        if key_name is None:
            return None

        combo = self._combo_for(key_name, include_caps=True)
        invocation = self.config.bindings.get(combo)

        if (
            invocation is None
            and self.caps_active
            and self.config.caps_fallback_to_base
        ):
            combo = self._combo_for(key_name, include_caps=False)
            invocation = self.config.bindings.get(combo)

        if invocation is not None:
            print(f"Touche {combo} -> {invocation.text}")

        return invocation


def check_config(path: Path) -> int:
    if not path.is_file():
        print(f"FAIL  Configuration absente : {path}")
        return 1

    try:
        config = read_config_file(path)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"FAIL  Configuration TOML : {exc}")
        return 1

    if config.issues:
        print(f"FAIL  Configuration : {len(config.issues)} erreur(s)")
        for issue in config.issues:
            print(f"      - {issue}")
        return 1

    print(f"OK    Configuration TOML : {path}")
    print(f"OK    Affectations        : {len(config.bindings)}")
    print(
        "OK    Couche CAPS        : "
        + ("active" if config.caps_lock_layer else "inactive")
    )
    print(
        "OK    Fallback CAPS      : "
        + ("oui" if config.caps_fallback_to_base else "non")
    )
    print(f"OK    Voix Piper         : {config.speech.voice}")
    print(f"OK    Mode vocal         : {config.speech.mode}")
    print(f"OK    Génération WAV     : {config.speech.generation}")
    print(f"OK    Cache Piper        : {'oui' if config.speech.cache else 'non'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a CVP Access keyboard TOML configuration"
    )
    parser.add_argument(
        "--check",
        metavar="FILE",
        type=Path,
        help="validate FILE and exit",
    )
    args = parser.parse_args()

    if args.check is not None:
        return check_config(args.check)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
