#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import sys
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
    "voice_volume_up": "Voix +",
    "voice_volume_down": "Voix −",
    "style_volume_up": "Volume Style +",
    "style_volume_down": "Volume Style −",
    "restart": "Redémarrer CVP Access",
}

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

MOD_LABELS = {"SHIFT": "Maj", "CTRL": "Ctrl", "ALT": "Alt", "ALTGR": "AltGr", "META": "Cmd", "CAPS": "Caps"}
MOD_ORDER = ("CAPS", "CTRL", "ALT", "ALTGR", "META", "SHIFT")

ROWS = [
    [("ESC", 1.25)] + [(f"F{i}", 1) for i in range(1, 14)],
    [("TOP1",1),("TOP2",1),("TOP3",1),("TOP4",1),("TOP5",1),("TOP6",1),("TOP7",1),("TOP8",1),("TOP9",1),("TOP0",1),("RPAREN",1),("EQUAL",1),("BACKSPACE",2)],
    [("TAB",1.5),("A",1),("Z",1),("E",1),("R",1),("T",1),("Y",1),("U",1),("I",1),("O",1),("P",1),("CARET",1),("DOLLAR",1)],
    [("CAPSLOCK",1.8),("Q",1),("S",1),("D",1),("F",1),("G",1),("H",1),("J",1),("K",1),("L",1),("M",1),("U_GRAVE",1),("ASTERISK",1),("ENTER",1.8)],
    [("SHIFT_L",2),("LESS",1),("W",1),("X",1),("C",1),("V",1),("B",1),("N",1),("COMMA",1),("SEMICOLON",1),("COLON",1),("EXCLAMATION",1),("SHIFT_R",2)],
    [("CTRL_L",1.4),("META",1.3),("ALT",1.3),("SPACE",6.2),("ALTGR",1.3),("CTRL_R",1.4)],
]
NAV_KEYS = [("INSERT","Inser"),("HOME","Origine"),("PAGEUP","Page ↑"),("DELETE","Suppr"),("END","Fin"),("PAGEDOWN","Page ↓")]


def normalize_combo(combo: str):
    parts = [p.strip().upper() for p in combo.split("+") if p.strip()]
    if not parts:
        raise ValueError("combinaison vide")
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
        sign = "+" if param > 0 else "−"
        return f"Volume Song {sign}{abs(param)}"
    if name == "main_volume_change" and param is not None:
        sign = "+" if param > 0 else "−"
        return f"Volume Main {sign}{abs(param)}"
    return ACTION_LABELS.get(name, name.replace("_", " "))


def group_for(raw: str):
    name, _ = parse_action(raw)
    if name.startswith("song_") or name in {"announce_tempo", "announce_transpose"}:
        return "song"
    if name.startswith("style_") or name in {"layer_toggle", "left_toggle"}:
        return "style"
    if name.startswith("voice_") or name.startswith("main_volume"):
        return "voice"
    if name == "restart":
        return "system"
    return "other"


def load_config(path: Path):
    with path.open("rb") as f:
        data = tomllib.load(f)
    general = data.get("general", {}) if isinstance(data.get("general", {}), dict) else {}
    keys = data.get("keys", {})
    if not isinstance(keys, dict):
        raise ValueError("[keys] absent ou invalide")
    bindings = {}
    for combo, action in keys.items():
        if not isinstance(combo, str) or not isinstance(action, str):
            continue
        mods, key = normalize_combo(combo)
        bindings.setdefault(key, []).append((mods, action.strip()))
    for key in bindings:
        bindings[key].sort(key=lambda x: (len(x[0]), x[0], x[1]))
    return general, bindings


def render_key(key, bindings, grow=1.0, printed_label=None):
    specials = {
        "CAPSLOCK": ("Caps Lock", "Couche secondaire"),
        "SHIFT_L": ("Maj", "Modificateur"), "SHIFT_R": ("Maj", "Modificateur"),
        "CTRL_L": ("Ctrl", "Modificateur"), "CTRL_R": ("Ctrl", "Modificateur"),
        "META": ("Cmd", "Modificateur"), "ALT": ("Alt", "Modificateur"), "ALTGR": ("AltGr", "Modificateur"),
    }
    if key in specials:
        label, desc = specials[key]
        return f'<div class="key special" style="flex-grow:{grow}"><div class="keyname">{html.escape(label)}</div><div class="specialtext">{html.escape(desc)}</div></div>'
    label = printed_label or KEY_LABELS.get(key, key)
    items = bindings.get(key, [])
    group = group_for(items[0][1]) if items else "unused"
    body = []
    for mods, action in items:
        mod = ""
        if mods:
            mod = '<span class="mod">' + html.escape(" + ".join(MOD_LABELS.get(m,m) for m in mods)) + '</span>'
        body.append(mod + '<span class="function">' + html.escape(human_action(action)) + '</span>' + '<span class="technical">' + html.escape(action) + '</span>')
    content = ''.join(f'<div class="binding">{x}</div>' for x in body) if body else '<div class="unusedmark">—</div>'
    return f'<div class="key {group}" style="flex-grow:{grow}"><div class="keyname">{html.escape(label)}</div>{content}</div>'


def generate(config_path: Path, output_path: Path):
    general, bindings = load_config(config_path)
    rows_html = []
    for row in ROWS:
        rows_html.append('<div class="keyboard-row">' + ''.join(render_key(k, bindings, g) for k,g in row) + '</div>')
    nav = ''.join(render_key(k, bindings, printed_label=label) for k,label in NAV_KEYS)
    arrows = '<div class="arrow-grid"><div></div>' + render_key("UP", bindings) + '<div></div>' + render_key("LEFT", bindings) + render_key("DOWN", bindings) + render_key("RIGHT", bindings) + '</div>'
    mapped = sum(len(v) for v in bindings.values())
    caps = bool(general.get("caps_lock_layer", True))
    fallback = bool(general.get("caps_fallback_to_base", True))
    css = '''
@page{size:A4 landscape;margin:6mm}*{box-sizing:border-box}body{margin:0;padding:12px;font-family:Arial,Helvetica,sans-serif;color:#171717;background:#fff}.header{display:flex;justify-content:space-between;gap:18px;margin-bottom:10px}h1{margin:0;font-size:22px}.subtitle{margin-top:3px;font-size:11px;color:#555}.stats{font-size:10px;text-align:right;line-height:1.35}.layout{display:grid;grid-template-columns:minmax(0,1fr) 205px;gap:10px}.keyboard-row{display:flex;gap:3px;margin-bottom:3px}.key{flex-basis:0;min-width:0;min-height:66px;padding:4px;border:1px solid #777;border-radius:5px;background:#fafafa;overflow:hidden}.keyname{font-size:10px;font-weight:700;margin-bottom:3px}.binding{margin-top:2px;line-height:1.08}.function{display:block;font-size:8.5px;font-weight:700}.technical{display:block;margin-top:1px;font-size:6.5px;color:#666;overflow-wrap:anywhere}.mod{display:inline-block;margin-bottom:2px;padding:1px 3px;border:1px solid #777;border-radius:3px;font-size:6.5px;font-weight:700}.unusedmark{color:#bbb;font-size:9px}.special{background:#efefef}.specialtext{font-size:8px;color:#555}.song{background:#eef5ff;border-bottom:4px solid #3973b7}.style{background:#f0f8f0;border-bottom:4px solid #57945a}.voice{background:#f6f1fa;border-bottom:4px solid #8663a8}.system{background:#fbf4ec;border-bottom:4px solid #b77a39}.unused{background:#fbfbfb;color:#aaa}.side h2{margin:0 0 5px;font-size:12px}.nav-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px}.nav-grid .key,.arrow-grid .key{min-height:66px}.arrow-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;margin-top:8px}.callout{margin-top:9px;padding:7px;border:1px solid #999;border-radius:5px;font-size:9px;line-height:1.3}.legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;font-size:9px}.legend-item{display:inline-flex;align-items:center;gap:4px}.swatch{width:11px;height:11px;border:1px solid #777}.swatch.song{background:#eef5ff}.swatch.style{background:#f0f8f0}.swatch.voice{background:#f6f1fa}.swatch.system{background:#fbf4ec}.footer{margin-top:6px;font-size:8px;color:#666}@media print{body{padding:0;print-color-adjust:exact;-webkit-print-color-adjust:exact}}@media(max-width:900px){.layout{grid-template-columns:1fr}.side{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
'''
    document = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CVP Access — Carte clavier</title><style>{css}</style></head><body>
<div class="header"><div><h1>CVP Access — Carte des commandes</h1><div class="subtitle">Générée directement depuis {html.escape(str(config_path))}</div></div><div class="stats">{mapped} affectation(s)<br>Caps Lock : {"couche secondaire" if caps else "normal"}<br>Fallback Caps : {"oui" if fallback else "non"}</div></div>
<div class="layout"><section>{''.join(rows_html)}</section><aside class="side"><div><h2>Navigation</h2><div class="nav-grid">{nav}</div>{arrows}</div><div><div class="callout"><strong>Aller à la mesure</strong><br>Appuyer sur la touche indiquée, saisir le numéro de mesure avec les chiffres, puis Entrée.<br>Retour arrière : corriger.<br>Échap : annuler.</div><div class="callout"><strong>Boucle A/B</strong><br>Point A : début de boucle.<br>Point B : fin de boucle.<br>Boucle A/B : activation / désactivation.</div></div></aside></div>
<div class="legend"><span class="legend-item"><i class="swatch song"></i>Song / information / navigation</span><span class="legend-item"><i class="swatch style"></i>Style / parties clavier</span><span class="legend-item"><i class="swatch voice"></i>Retour vocal</span><span class="legend-item"><i class="swatch system"></i>Système</span></div>
<div class="footer">Le gros libellé est destiné à l'accompagnateur. Le petit texte gris est le nom technique utilisé dans keyboard.toml. Cette page est générée automatiquement : modifier keyboard.toml, puis relancer le générateur.</div>
</body></html>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return mapped


def default_config():
    for candidate in [Path("/etc/cvp-access/keyboard.toml"), Path("config/default.toml"), Path("keyboard.toml")]:
        if candidate.is_file():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(description="Génère la carte visuelle du clavier CVP Access.")
    parser.add_argument("--config", type=Path, help="keyboard.toml à lire")
    parser.add_argument("--output", type=Path, help="HTML de sortie")
    args = parser.parse_args()
    config = args.config or default_config()
    if config is None or not config.is_file():
        print("Aucun keyboard.toml trouvé. Utiliser --config CHEMIN.", file=sys.stderr)
        return 2
    output = args.output or config.with_name("keyboard-map.html")
    try:
        mapped = generate(config.resolve(), output.resolve())
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print("Impossible de générer la carte :", exc, file=sys.stderr)
        return 1
    print("Carte clavier générée :", output)
    print("Affectations :", mapped)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
