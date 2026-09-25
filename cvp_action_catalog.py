#!/usr/bin/env python3
"""Single action catalogue for CVP Access keyboard configuration.

This module is deliberately hardware-free so it can be imported by the runtime,
keyboard map generator, Web editor, verifier and maintenance tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ActionSpec:
    parameter_required: bool = False
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    description: str = ""


@dataclass(frozen=True)
class ActionMeta:
    label: str
    category: str
    description: str
    spec: ActionSpec = ActionSpec()
    ui_values: tuple[int, ...] = ()
    public: bool = True
    deprecated: bool = False
    synonyms: tuple[str, ...] = ()


def _m(
    label,
    category,
    description,
    *,
    parameter_required=False,
    minimum=None,
    maximum=None,
    ui_values=(),
    public=True,
    deprecated=False,
    synonyms=(),
):
    return ActionMeta(
        label=label,
        category=category,
        description=description,
        spec=ActionSpec(parameter_required, minimum, maximum, description),
        ui_values=tuple(ui_values),
        public=public,
        deprecated=deprecated,
        synonyms=tuple(synonyms),
    )


ACTION_CATALOG = {
    "song_track_toggle": _m(
        "Piste Song — Mute / Unmute", "song", "Bascule ON/OFF d'une piste Song",
        parameter_required=True, minimum=1, maximum=16, ui_values=range(1, 17),
        synonyms=("piste", "mute", "unmute"),
    ),
    "song_track_solo": _m(
        "Solo piste Song", "song", "Active une piste Song et coupe les quinze autres",
        parameter_required=True, minimum=1, maximum=16, ui_values=range(1, 17),
        synonyms=("solo", "piste"),
    ),
    "song_all_tracks_on": _m(
        "Toutes les pistes Song ON", "song", "Active les seize pistes Song",
        synonyms=("toutes pistes", "all tracks"),
    ),
    "song_play_pause": _m("Lecture / Pause", "song", "Lecture / pause du Song"),
    "song_stop": _m("Stop Song", "song", "Stop du Song"),
    "song_position": _m("Annonce position", "song", "Annonce mesure et temps"),
    "song_measure_previous": _m("Mesure -1", "song", "Recule le Song d'une mesure"),
    "song_measure_next": _m("Mesure +1", "song", "Avance le Song d'une mesure"),
    "song_measure_previous_5": _m("Mesure -5", "song", "Recule le Song de cinq mesures"),
    "song_measure_next_5": _m("Mesure +5", "song", "Avance le Song de cinq mesures"),
    "song_goto_measure": _m("Aller à la mesure", "song", "Saisie directe d'une mesure"),
    "song_loop_point_a": _m("Point A", "song", "Mémorise le point A à la mesure courante"),
    "song_loop_point_b": _m("Point B", "song", "Mémorise le point B à la mesure courante"),
    "song_loop_toggle": _m("Boucle A/B", "song", "Active ou désactive la boucle A/B"),
    "song_volume_change": _m(
        "Volume Song", "song", "Modifie le volume Song / MidiMaster",
        parameter_required=True, minimum=-5, maximum=5, ui_values=(-5, -1, 1, 5),
        synonyms=("volume midi",),
    ),
    "announce_song_name": _m("Nom du Song", "information", "Annonce le Song actuellement chargé"),
    "announce_song_length": _m("Longueur du Song", "information", "Annonce la longueur du Song"),
    "announce_tempo": _m("Annonce tempo", "information", "Annonce le tempo courant"),
    "announce_transpose": _m("Annonce transpose", "information", "Annonce le transpose courant"),

    "style_part_toggle": _m(
        "Partie Style — Mute / Unmute", "style", "Bascule ON/OFF d'une partie Style",
        parameter_required=True, minimum=1, maximum=8, ui_values=range(1, 9),
        synonyms=("partie style", "mute style"),
    ),
    "style_all_parts_on": _m("Toutes les parties Style ON", "style", "Active les huit parties Style"),
    "style_start_stop": _m("Style Start / Stop", "style", "Démarre ou arrête le Style"),
    "style_intro": _m(
        "Intro Style", "style", "Sélectionne une Intro Style",
        parameter_required=True, minimum=1, maximum=3, ui_values=range(1, 4),
    ),
    "style_main": _m(
        "Main Style", "style", "Sélectionne une variation Main Style",
        parameter_required=True, minimum=1, maximum=4, ui_values=range(1, 5),
        synonyms=("main a", "main b", "main c", "main d"),
    ),
    "style_fill": _m(
        "Fill Style", "style", "Déclenche un Fill Style",
        parameter_required=True, minimum=1, maximum=4, ui_values=range(1, 5),
    ),
    "style_ending": _m(
        "Ending Style", "style", "Déclenche un Ending Style",
        parameter_required=True, minimum=1, maximum=3, ui_values=range(1, 4),
    ),
    "style_break": _m("Break Style", "style", "Déclenche le Break Style"),
    "style_volume_change": _m(
        "Volume Style", "style", "Modifie le volume Style",
        parameter_required=True, minimum=-5, maximum=5, ui_values=(-5, -1, 1, 5),
    ),
    "style_volume_up": _m(
        "Volume Style + (ancien)", "style", "Augmente le volume Style",
        deprecated=True,
    ),
    "style_volume_down": _m(
        "Volume Style - (ancien)", "style", "Diminue le volume Style",
        deprecated=True,
    ),
    "announce_style_name": _m("Nom du Style", "information", "Annonce le Style actuellement sélectionné"),
    "sync_start_toggle": _m("Syncro Start ON / OFF", "style", "Active ou désactive Syncro Start"),
    "metronome_toggle": _m("Métronome ON / OFF", "style", "Active ou désactive le métronome"),

    "layer_toggle": _m("Layer / Dual ON / OFF", "keyboard", "Bascule Layer / Dual"),
    "left_toggle": _m("Left ON / OFF", "keyboard", "Bascule Left"),
    "announce_main_voice_name": _m("Nom du son Main", "keyboard", "Annonce le nom du son Main"),
    "announce_layer_voice_name": _m("Nom du son Layer", "keyboard", "Annonce le nom du son Layer"),
    "announce_left_voice_name": _m("Nom du son Left", "keyboard", "Annonce le nom du son Left"),
    "main_volume_change": _m(
        "Volume Main", "keyboard", "Modifie le volume Main",
        parameter_required=True, minimum=-5, maximum=5, ui_values=(-5, -1, 1, 5),
    ),

    "guide_toggle": _m("Guide Yamaha ON / OFF", "accessibility", "Active ou désactive Guide"),
    "stream_lights_toggle": _m("Stream Lights ON / OFF", "accessibility", "Active ou désactive Stream Lights"),
    "voice_guide_mute_toggle": _m("Guide vocal CVP Access ON / OFF", "accessibility", "Coupe ou réactive le guide vocal"),
    "voice_volume_up": _m("Volume guide vocal +", "accessibility", "Augmente le volume du guide vocal"),
    "voice_volume_down": _m("Volume guide vocal -", "accessibility", "Diminue le volume du guide vocal"),

    "registration_recall": _m(
        "Registration Memory", "registration", "Rappelle une Registration Memory",
        parameter_required=True, minimum=1, maximum=8, ui_values=range(1, 9),
        synonyms=("registration", "mémoire"),
    ),

    "restart": _m("Relancer CVP Access", "system", "Quitte CVP Access pour redémarrage systemd"),
}

ACTION_SPECS = {name: meta.spec for name, meta in ACTION_CATALOG.items()}

CATEGORY_LABELS = {
    "song": "Song",
    "style": "Style",
    "keyboard": "Parties clavier / Voices",
    "information": "Informations",
    "accessibility": "Guide / accessibilité",
    "registration": "Registration",
    "system": "Système",
}


def action_text(name: str, parameter: Optional[int] = None) -> str:
    meta = ACTION_CATALOG.get(name)
    if meta is None:
        return name.replace("_", " ")

    if parameter is None:
        return meta.label

    if name in {"song_track_toggle", "song_track_solo"}:
        prefix = "Piste Song" if name == "song_track_toggle" else "Solo piste"
        return f"{prefix} {parameter}"

    if name == "style_part_toggle":
        style_parts = {
            1: "Rythme 1", 2: "Rythme 2", 3: "Basse", 4: "Accord 1",
            5: "Accord 2", 6: "Pad", 7: "Phrase 1", 8: "Phrase 2",
        }
        return style_parts.get(parameter, f"Partie Style {parameter}")

    if name in {"song_volume_change", "style_volume_change", "main_volume_change"}:
        sign = "+" if parameter > 0 else "-"
        return f"{meta.label} {sign}{abs(parameter)}"

    if name in {"style_main", "style_fill"} and 1 <= parameter <= 4:
        letter = "ABCD"[parameter - 1]
        return f"{meta.label.split()[0]} {letter}"

    if name == "style_intro":
        return f"Intro {parameter}"
    if name == "style_ending":
        return f"Ending {parameter}"
    if name == "registration_recall":
        return f"Registration {parameter}"

    return f"{meta.label} {parameter}"


def action_help(name: str, parameter: Optional[int] = None) -> str:
    if name == "song_track_toggle":
        return f"Piste {parameter} du Song, activer ou couper."
    if name == "song_track_solo":
        return f"Solo piste {parameter}."
    if name == "style_part_toggle":
        return f"{action_text(name, parameter)}, activer ou couper."
    if name in {"song_volume_change", "style_volume_change", "main_volume_change"}:
        label = ACTION_CATALOG[name].label
        direction = "Augmenter" if (parameter or 0) > 0 else "Diminuer"
        return f"{direction} {label.lower()} de {abs(parameter or 0)}."
    if name in {"style_intro", "style_main", "style_fill", "style_ending", "registration_recall"}:
        return action_text(name, parameter) + "."
    meta = ACTION_CATALOG.get(name)
    if meta and meta.description:
        return meta.description + "."
    return action_text(name, parameter) + "."


def public_catalog():
    items = []
    for name, meta in ACTION_CATALOG.items():
        if not meta.public:
            continue
        items.append(
            {
                "id": name,
                "label": meta.label,
                "description": meta.description,
                "category": meta.category,
                "category_label": CATEGORY_LABELS.get(meta.category, meta.category),
                "parameter_required": meta.spec.parameter_required,
                "minimum": meta.spec.minimum,
                "maximum": meta.spec.maximum,
                "values": list(meta.ui_values),
                "deprecated": meta.deprecated,
                "synonyms": list(meta.synonyms),
            }
        )
    return items
