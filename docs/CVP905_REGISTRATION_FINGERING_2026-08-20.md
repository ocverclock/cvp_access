# CVP-905 — Registration Memory et Fingering Type

Date : 20 août 2026

## Matériel de validation

- Yamaha CVP-905
- Firmware 1.03
- Raspberry Pi / Debian
- Interface MIDI DIN ProdipeMIDIlilo

---

# 1. Objectif initial

La recherche visait à lire et contrôler directement le paramètre :

`Split Point / Fingering Type`

avec notamment les modes :

- Fingered
- AI Fingered
- AI Full Keyboard

Le but est de rendre ces fonctions accessibles depuis CVP Access sans
navigation dans l'écran tactile du CVP.

---

# 2. Recherche d'un contrôle Fingering direct

Plusieurs pistes ont été testées.

## Protocole CSP moderne

Header utilisé par le CVP :

```text
F0 43 73 01 52 25 26
