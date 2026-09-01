#!/usr/bin/env python3
"""CVP Access 1.5.1 - compléments vocaux.

Réutilise le gestionnaire hybride existant et ajoute :
- aide CTRL pré-générable par hash ;
- annonces booléennes communes ;
- annonces de valeurs/noms dynamiques.
"""

from __future__ import annotations

import hashlib

import cvp_speech as legacy_speech


def canonical_help(text: str) -> str:
    text = " ".join(str(text).strip().split())
    if text and text[-1] not in ".!?":
        text += "."
    return text


def help_filename(text: str) -> str:
    canonical = canonical_help(text)
    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:20]
    return f"help_{digest}.wav"


def install_speech_hooks(core, speech_config):
    manager = legacy_speech.install_speech_hooks(
        core,
        speech_config,
    )

    voice_dir = core.VOICE_DIR

    def announce_action_help(text):
        canonical = canonical_help(text)
        return manager.speak(
            canonical,
            voice_dir / "help" / help_filename(canonical),
            replace_key="action_help",
        )

    def announce_boolean_state(label, enabled, stem):
        state = "on" if enabled else "off"
        text = (
            f"{label} activé."
            if enabled
            else f"{label} désactivé."
        )
        return manager.speak(
            text,
            voice_dir / "state" / f"{stem}_{state}.wav",
            replace_key=f"state_{stem}",
        )

    def announce_named_value(label, value):
        return manager.speak(
            f"{label} {value}.",
            replace_key=f"named_{label}",
        )

    def announce_value(value, *, key="value"):
        return manager.speak(
            f"{value}.",
            replace_key=f"value_{key}",
        )

    def announce_song_length(measures):
        return manager.speak(
            f"Longueur du Song, {measures} mesures.",
            replace_key="song_length",
        )

    core.announce_action_help = announce_action_help
    core.announce_boolean_state = announce_boolean_state
    core.announce_named_value = announce_named_value
    core.announce_value = announce_value
    core.announce_song_length = announce_song_length

    return manager
