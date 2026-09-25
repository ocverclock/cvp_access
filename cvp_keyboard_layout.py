#!/usr/bin/env python3
"""Shared AZERTY keyboard presentation metadata for CVP Access."""

from __future__ import annotations

KEY_LABELS = {
    "ESC": "Échap", "TAB": "Tab", "SPACE": "Espace", "ENTER": "Entrée",
    "BACKSPACE": "Retour arrière",
    "TOP1": "& / 1", "TOP2": "é / 2", "TOP3": "\" / 3", "TOP4": "' / 4",
    "TOP5": "( / 5", "TOP6": "- / 6", "TOP7": "è / 7", "TOP8": "_ / 8",
    "TOP9": "ç / 9", "TOP0": "à / 0", "RPAREN": ") / °", "EQUAL": "= / +",
    "CARET": "^ / ¨", "DOLLAR": "$ / £", "U_GRAVE": "ù / %", "ASTERISK": "* / µ",
    "COMMA": ", / ?", "SEMICOLON": "; / .", "COLON": ": / /",
    "EXCLAMATION": "! / §", "LESS": "< / >", "UP": "↑", "DOWN": "↓",
    "LEFT": "←", "RIGHT": "→", "PAGEUP": "Page ↑", "PAGEDOWN": "Page ↓",
    "HOME": "Origine", "END": "Fin", "INSERT": "Inser", "DELETE": "Suppr",
}

MOD_LABELS = {
    "SHIFT": "Maj", "CTRL": "Ctrl", "ALT": "Alt",
    "ALTGR": "AltGr", "META": "Cmd", "CAPS": "Caps",
}

# Canonical normalization order used by runtime, map and Web editor.
MODIFIER_ORDER = ("CTRL", "ALT", "ALTGR", "SHIFT", "META", "CAPS")
EDITOR_LAYERS = (
    ("", "Simple"),
    ("SHIFT", "Maj"),
    ("ALT", "Alt"),
    ("ALTGR", "AltGr"),
    ("META", "Cmd"),
)

ROWS = [
    [("ESC", 1.25)] + [(f"F{i}", 1) for i in range(1, 17)],
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
    ("UP","↑"),("LEFT","←"),("DOWN","↓"),("RIGHT","→"),
]

RESERVED_KEYS = {
    "F14": "Morceau précédent / Recorder",
    "F15": "Dictaphone MIDI",
    "F16": "Morceau suivant / Recorder",
}

NON_ASSIGNABLE_LAYOUT_KEYS = {
    "CAPSLOCK", "SHIFT_L", "SHIFT_R", "CTRL_L", "CTRL_R", "META", "ALT", "ALTGR",
}

def printed_label(key: str) -> str:
    return KEY_LABELS.get(key, key)

def editor_keys():
    keys = []
    for row in ROWS:
        current = []
        for key, width in row:
            current.append(
                {
                    "key": key,
                    "label": printed_label(key),
                    "width": width,
                    "assignable": key not in NON_ASSIGNABLE_LAYOUT_KEYS,
                    "reserved": key in RESERVED_KEYS,
                    "reserved_label": RESERVED_KEYS.get(key, ""),
                }
            )
        keys.append(current)
    return keys
