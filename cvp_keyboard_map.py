#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import tomllib
from pathlib import Path

STYLE_PARTS = {
    1: "Rythme 1", 2: "Rythme 2", 3: "Basse", 4: "Accord 1",
    5: "Accord 2", 6: "Pad", 7: "Phrase 1", 8: "Phrase 2",
}

ACTION_LABELS = {
    "layer_toggle": "Layer / Dual",
    "left_toggle": "Left",
    "announce_tempo": "Annonce tempo",
    "announce_transpose": "Annonce transpose",
    "announce_style_name": "Nom du Style",
    "announce_song_name": "Nom du Song",
    "announce_song_length": "Longueur du Song",
    "sync_start_toggle": "Syncro Start ON / OFF",
    "guide_toggle": "Guide ON / OFF",
    "stream_lights_toggle": "Stream Lights ON / OFF",
    "metronome_toggle": "Métronome ON / OFF",
    "song_play_pause": "Lecture / Pause",
    "song_stop": "Stop Song",
    "song_position": "Annonce position",
    "song_measure_previous": "Mesure −1",
    "song_measure_next": "Mesure +1",
    "song_measure_previous_5": "Mesure −5",
    "song_measure_next_5": "Mesure +5",
    "song_goto_measure": "Aller à la mesure",
    "song_loop_point_a": "Point A",
    "song_loop_point_b": "Point B",
    "song_loop_toggle": "Boucle A/B",
    "style_start_stop": "Style Start / Stop",
    "voice_volume_up": "Vol. guide vocal +",
    "voice_volume_down": "Vol. guide vocal −",
    "style_volume_up": "Vol. Style +5 (ancien raccourci)",
    "style_volume_down": "Vol. Style −5 (ancien raccourci)",
    "restart": "Redémarrer CVP Access",
}

PUBLIC_ACTION_CATALOG = [
    ("style_intro", "Intro Style 1..3", "style_intro:1..3"),
    ("style_main", "Main Style A..D", "style_main:1..4"),
    ("style_fill", "Fill Style A..D", "style_fill:1..4"),
    ("style_break", "Break Style", "style_break"),
    ("style_ending", "Ending Style 1..3", "style_ending:1..3"),
    ("registration_recall", "Registration Memory 1..8", "registration_recall:1..8"),
    ("stream_lights_toggle", "Stream Lights ON / OFF", "stream_lights_toggle"),
]

KEY_LABELS = {
    "ESC": "Échap", "TAB": "Tab", "SPACE": "Espace", "ENTER": "Entrée",
    "BACKSPACE": "Retour arrière", "TOP1": "& / 1", "TOP2": "é / 2",
    "TOP3": '" / 3', "TOP4": "' / 4", "TOP5": "( / 5", "TOP6": "- / 6",
    "TOP7": "è / 7", "TOP8": "_ / 8", "TOP9": "ç / 9", "TOP0": "à / 0",
    "RPAREN": ") / °", "EQUAL": "= / +", "CARET": "^ / ¨", "DOLLAR": "$ / £",
    "U_GRAVE": "ù / %", "ASTERISK": "* / µ", "COMMA": ", / ?",
    "SEMICOLON": "; / .", "COLON": ": / /", "EXCLAMATION": "! / §", "LESS": "< / >",
    "UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→", "PAGEUP": "Page ↑",
    "PAGEDOWN": "Page ↓", "HOME": "Origine", "END": "Fin", "INSERT": "Inser", "DELETE": "Suppr",
}

MOD_LABELS = {
    "SHIFT": "Maj", "CTRL": "Ctrl", "ALT": "Alt",
    "ALTGR": "AltGr", "META": "Cmd", "CAPS": "Caps",
}
MOD_ORDER = ("CAPS", "CTRL", "ALT", "ALTGR", "META", "SHIFT")

ROWS = [
    [("ESC", 1.25)] + [(f"F{i}", 1) for i in range(1, 14)],
    [("TOP1",1),("TOP2",1),("TOP3",1),("TOP4",1),("TOP5",1),("TOP6",1),
     ("TOP7",1),("TOP8",1),("TOP9",1),("TOP0",1),("RPAREN",1),("EQUAL",1),("BACKSPACE",2)],
    [("TAB",1.5),("A",1),("Z",1),("E",1),("R",1),("T",1),("Y",1),("U",1),("I",1),
     ("O",1),("P",1),("CARET",1),("DOLLAR",1)],
    [("CAPSLOCK",1.8),("Q",1),("S",1),("D",1),("F",1),("G",1),("H",1),("J",1),
     ("K",1),("L",1),("M",1),("U_GRAVE",1),("ASTERISK",1),("ENTER",1.8)],
    [("SHIFT_L",2),("LESS",1),("W",1),("X",1),("C",1),("V",1),("B",1),("N",1),
     ("COMMA",1),("SEMICOLON",1),("COLON",1),("EXCLAMATION",1),("SHIFT_R",2)],
    [("CTRL_L",1.5),("META",1.2),("ALT",1.2),("SPACE",6.0),("ALTGR",1.2),("CTRL_R",1.5)],
]

NAV_KEYS = [
    ("INSERT","Inser"),("HOME","Origine"),("PAGEUP","Page ↑"),
    ("DELETE","Suppr"),("END","Fin"),("PAGEDOWN","Page ↓"),
]


def normalize_combo(combo: str):
    parts = [p.strip().upper() for p in combo.split("+") if p.strip()]
    key = parts[-1]
    mods = tuple(m for m in MOD_ORDER if m in parts[:-1])
    return mods, key


def parse_action(raw: str):
    raw = raw.strip()
    if ":" not in raw:
        return raw, None
    name, value = raw.split(":", 1)
    try:
        return name, int(value)
    except ValueError:
        return name, None


def human_action(raw: str):
    name, param = parse_action(raw)
    if name == "song_track_toggle":
        return f"Piste Song {param}"
    if name == "style_part_toggle":
        return STYLE_PARTS.get(param, f"Partie Style {param}")
    if name == "song_volume_change" and param is not None:
        return f"Vol. Song {'+' if param > 0 else '−'}{abs(param)}"
    if name == "main_volume_change" and param is not None:
        return f"Vol. Main {'+' if param > 0 else '−'}{abs(param)}"
    if name == "style_volume_change" and param is not None:
        return f"Vol. Style {'+' if param > 0 else '−'}{abs(param)}"
    if name == "style_intro":
        return f"Intro {param}"
    if name == "style_main":
        return f"Main {'ABCD'[(param or 1)-1]}"
    if name == "style_fill":
        return f"Fill {'ABCD'[(param or 1)-1]}"
    if name == "style_ending":
        return f"Ending {param}"
    if name == "style_break":
        return "Break"
    if name == "registration_recall":
        return f"Registration {param}"
    return ACTION_LABELS.get(name, name.replace("_", " "))


def group_for(raw: str):
    name, _ = parse_action(raw)
    if name.startswith("song_") or name in {
        "announce_tempo", "announce_transpose",
        "announce_song_name", "announce_song_length"
    }:
        return "song"
    if name.startswith("style_") or name in {
        "announce_style_name", "sync_start_toggle",
        "guide_toggle", "metronome_toggle",
        "layer_toggle", "left_toggle"
    }:
        return "style"
    if name.startswith("voice_") or name.startswith("main_volume"):
        return "voice"
    if name == "restart":
        return "system"
    return "other"


def load_config(path: Path):
    with path.open("rb") as f:
        data = tomllib.load(f)
    general = data.get("general", {})
    keys = data.get("keys", {})
    bindings = {}
    for combo, action in keys.items():
        if not isinstance(combo, str) or not isinstance(action, str):
            continue
        mods, key = normalize_combo(combo)
        bindings.setdefault(key, []).append((mods, action.strip()))
    for key in bindings:
        bindings[key].sort(key=lambda x: (len(x[0]), x[0], x[1]))
    return general, bindings, keys


def render_key(key, bindings, grow=1.0, printed_label=None):
    if key == "CAPSLOCK":
        return (
            f'<div class="key special" style="flex-grow:{grow}">'
            '<div class="keyname">Caps Lock</div>'
            '<div class="specialtext">Non attribué actuellement</div></div>'
        )
    if key in {"SHIFT_L", "SHIFT_R"}:
        return (
            f'<div class="key special" style="flex-grow:{grow}">'
            '<div class="keyname">Maj</div>'
            '<div class="specialtext">±5 quand indiqué</div></div>'
        )
    if key in {"CTRL_L", "CTRL_R"}:
        return (
            f'<div class="key ctrlkey" style="flex-grow:{grow}">'
            '<div class="keyname">CTRL</div>'
            '<div class="specialtext"><strong>AIDE VOCALE</strong><br>'
            'Ctrl + touche = annonce sa fonction sans l’exécuter</div></div>'
        )
    if key in {"META", "ALT", "ALTGR"}:
        label = {"META":"Cmd","ALT":"Alt","ALTGR":"AltGr"}[key]
        return (
            f'<div class="key special" style="flex-grow:{grow}">'
            f'<div class="keyname">{label}</div>'
            '<div class="specialtext">Modificateur</div></div>'
        )

    label = printed_label or KEY_LABELS.get(key, key)
    items = bindings.get(key, [])
    group = group_for(items[0][1]) if items else "unused"
    body = []
    for mods, action in items:
        mod = ""
        if mods:
            mod = (
                '<span class="mod">'
                + html.escape(" + ".join(MOD_LABELS.get(m, m) for m in mods))
                + '</span>'
            )
        body.append(
            mod
            + '<span class="function">' + html.escape(human_action(action)) + '</span>'
            + '<span class="technical">' + html.escape(action) + '</span>'
        )
    content = (
        "".join(f'<div class="binding">{x}</div>' for x in body)
        if body else '<div class="unusedmark">—</div>'
    )
    return (
        f'<div class="key {group}" style="flex-grow:{grow}">'
        f'<div class="keyname">{html.escape(label)}</div>{content}</div>'
    )


def generate(config_path: Path, output_path: Path):
    general, bindings, raw_keys = load_config(config_path)
    rows_html = [
        '<div class="keyboard-row">'
        + "".join(render_key(k, bindings, g) for k, g in row)
        + "</div>"
        for row in ROWS
    ]
    nav = "".join(render_key(k, bindings, printed_label=label) for k, label in NAV_KEYS)
    arrows = (
        '<div class="arrow-grid"><div></div>' + render_key("UP", bindings) + '<div></div>'
        + render_key("LEFT", bindings) + render_key("DOWN", bindings)
        + render_key("RIGHT", bindings) + '</div>'
    )
    assigned_names = {parse_action(v)[0] for v in raw_keys.values() if isinstance(v, str)}
    unassigned = [
        (label, technical)
        for action, label, technical in PUBLIC_ACTION_CATALOG
        if action not in assigned_names
    ]
    unassigned_html = "".join(
        '<div class="unassigned-item"><strong>'
        + html.escape(label)
        + '</strong><span>'
        + html.escape(technical)
        + '</span></div>'
        for label, technical in unassigned
    ) or '<p>Toutes les actions publiques sont attribuées.</p>'
    mapped = sum(len(v) for v in bindings.values())

    css = r'''
@page{size:A4 landscape;margin:6mm}
*{box-sizing:border-box}
body{margin:0;padding:12px;font-family:Arial,Helvetica,sans-serif;color:#171717;background:#fff}
.header{display:flex;justify-content:space-between;gap:18px;margin-bottom:7px}
h1{margin:0;font-size:22px}
.subtitle{margin-top:3px;font-size:11px;color:#555}
.stats{font-size:10px;text-align:right;line-height:1.35}
.help-banner{margin:0 0 8px;padding:7px 10px;border:2px solid #222;border-radius:6px;font-size:12px}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 205px;gap:10px}
.keyboard-row{display:flex;gap:3px;margin-bottom:3px}
.key{flex-basis:0;min-width:0;min-height:66px;padding:4px;border:1px solid #777;border-radius:5px;background:#fafafa;overflow:hidden}
.keyname{font-size:10px;font-weight:700;margin-bottom:3px}
.binding{margin-top:2px;line-height:1.08}
.function{display:block;font-size:8.5px;font-weight:700}
.technical{display:block;margin-top:1px;font-size:6.4px;color:#666;overflow-wrap:anywhere}
.mod{display:inline-block;margin-bottom:2px;padding:1px 3px;border:1px solid #777;border-radius:3px;font-size:6.5px;font-weight:700}
.unusedmark{color:#bbb;font-size:9px}
.special{background:#efefef}
.ctrlkey{background:#fff;border:2px solid #222}
.specialtext{font-size:7.8px;color:#444}
.song{background:#eef5ff;border-bottom:4px solid #3973b7}
.style{background:#f0f8f0;border-bottom:4px solid #57945a}
.voice{background:#f6f1fa;border-bottom:4px solid #8663a8}
.system{background:#fbf4ec;border-bottom:4px solid #b77a39}
.unused{background:#fbfbfb;color:#aaa}
.side h2{margin:0 0 5px;font-size:12px}
.nav-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px}
.nav-grid .key,.arrow-grid .key{min-height:66px}
.arrow-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;margin-top:8px}
.callout{margin-top:9px;padding:7px;border:1px solid #999;border-radius:5px;font-size:9px;line-height:1.3}
.unassigned{margin-top:10px;padding-top:7px;border-top:2px solid #555}
.unassigned h2{font-size:14px;margin:0 0 6px}
.unassigned-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}
.unassigned-item{padding:5px 7px;border:1px solid #aaa;border-radius:5px;font-size:9px}
.unassigned-item strong{display:block}
.unassigned-item span{display:block;margin-top:2px;color:#666;font-size:7.5px}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;font-size:9px}
.footer{margin-top:6px;font-size:8px;color:#666}
@media print{body{padding:0;print-color-adjust:exact;-webkit-print-color-adjust:exact}}
'''

    document = f'''<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CVP Access — Carte clavier</title><style>{css}</style></head>
<body>
<div class="header"><div><h1>CVP Access — Carte des commandes</h1>
<div class="subtitle">Générée depuis {html.escape(str(config_path))}</div></div>
<div class="stats">{mapped} affectation(s)<br>Layout accessibilité 1.5.1 RC2</div></div>

<div class="help-banner"><strong>CTRL = AIDE VOCALE.</strong>
Maintenir CTRL puis appuyer sur une touche attribuée :
CVP Access annonce sa fonction <strong>sans l’exécuter</strong>.</div>

<div class="layout"><section>{''.join(rows_html)}</section>
<aside class="side"><div><h2>Navigation</h2><div class="nav-grid">{nav}</div>{arrows}</div>
<div><div class="callout"><strong>Volume</strong><br>
Page ↑ / ↓ : Volume Style ±1.<br>Maj + Page ↑ / ↓ : ±5.<br>↑ / ↓ : Vol. guide vocal.</div>
<div class="callout"><strong>Informations</strong><br>
W : nom Style.<br>X : nom Song.<br>C : longueur Song.<br>
Sans Song chargé : annonce « Pas de Song chargé ».</div></div></aside></div>

<section class="unassigned"><h2>Actions disponibles mais non attribuées</h2>
<div class="unassigned-grid">{unassigned_html}</div></section>

<div class="legend">Song / informations • Style / accompagnement • Guide vocal • Système</div>
<div class="footer">Les actions non attribuées restent disponibles dans le catalogue et peuvent être affectées ultérieurement dans keyboard.toml.</div>
</body></html>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"Carte générée : {output_path}")
    print(f"Affectations : {mapped}")
    print(f"Actions publiques non attribuées : {len(unassigned)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("/etc/cvp-access/keyboard.toml"))
    parser.add_argument("--output", type=Path, default=Path("/etc/cvp-access/keyboard-map.html"))
    args = parser.parse_args()
    generate(args.config, args.output)


if __name__ == "__main__":
    main()
