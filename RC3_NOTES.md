# CVP Access 1.5 RC3

Validation matérielle : Yamaha CVP-905 firmware 1.03.

## Fonctions validées

- Song pistes 1-16 : mute/unmute.
- Transport Song : Play/Pause/Stop.
- Navigation : +/-1, +/-5 et accès direct F3.
- Loop A/B : F4/F5/F6.
- Conservation du métronome lors d’une navigation arrière.
- Style Start/Stop : F13.
- Volume Song/MidiMaster : HOME/END, +/-1 et SHIFT +/-5.
- Volume Main : INSERT/DELETE, +/-1 et SHIFT +/-5.
- Piper asynchrone.
- Optimisation des annonces de volume.
- CTRL + touche affectée : annonce l’action sans l’exécuter.

## Protocole validé

- Metronome : 07 00 00 01 | 00
- Style Start/Stop : 06 00 03 01 | 00
- Song/MidiMaster volume : 0C 00 00 01 | 50
- Main volume : 0C 00 00 01 | 00
- Song position : 04 00 0A 01 | 00
- Song loop : 04 00 0D 01 | 00

## Recherche suspendue

Fingering Type / AI Full Keyboard : aucun candidat MIDI reproductible.
