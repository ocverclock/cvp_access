# CVP-905 — checkpoint protocole RC3

Testé sur Yamaha CVP-905 firmware 1.03.

## Validé GET + SET

### Métronome
- `07 00 00 01 | 00`
- `00` OFF / `01` ON
- conservation automatique sur LEFT, SHIFT+LEFT et F3 vers l'arrière.

### Style Start / Stop
- `06 00 03 01 | 00`
- `00` STOP / `01` START
- affectation : F13.

### Volume Song / MidiMaster
- `0C 00 00 01 | 50`
- GET + SET validés.
- UI 80 = `0x50`, UI 90 = `0x5A`.
- HOME +1, SHIFT+HOME +5, END -1, SHIFT+END -5.

### Volume Main
- `0C 00 00 01 | 00`
- GET + SET validés.
- INSERT +1, SHIFT+INSERT +5, DELETE -1, SHIFT+DELETE -5.

### Song position
- `04 00 0A 01 | 00`
- mesure 14-bit + temps 14-bit.

### Song Loop A/B
- `04 00 0D 01 | 00`
- mémoire A/B locale conservée quand Loop passe OFF.

## Fingering Type
Recherche MIDI suspendue. Aucun candidat reproductible, y compris avec
ACMP + Style actifs. À reprendre plutôt par diff Registration/Backup.
