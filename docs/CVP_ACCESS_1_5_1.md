# CVP Access 1.5.1 — consolidation technique

## Objectif

La 1.5 avait modernisé le clavier et la configuration, tout en important
directement `cvp_access_v1.4.1.py` comme moteur Yamaha.

La 1.5.1 commence la séparation propre du protocole sans casser le runtime.

## Architecture transitoire

```text
cvp_access_v1.5.py (VERSION 1.5.1-RC1-dev)
        |
        +-- cvp_midi.py            API MIDI publique
        +-- cvp_song.py            Song
        +-- cvp_style.py           Style
        +-- cvp_voice.py           Voice
        +-- cvp_registration.py    Registration
        +-- cvp_yamaha.py          codecs/utilitaires Yamaha
        |
        `-- cvp_access_v1.4.1.py   moteur historique temporaire
```

## Changements

### API MIDI

`MidiService` fournit :
- `start()` / `stop()`
- `drain()`
- `send()`
- `csp_get()`
- `csp_set_u7()` / `csp_set_raw()`
- `xg_get()`
- `xg_set()`
- `recall_registration()`

Les futurs outils de reverse engineering doivent utiliser cette API au lieu
de manipuler `midi_queue` directement.

### Texte Yamaha

Correction du décodeur Song.

Ancienne hypothèse supprimée :

```text
2 premiers octets = longueur 14-bit
```

Format physiquement observé sur CVP-905 :

```text
[masque bits hauts] [jusqu'à 7 octets]
[masque bits hauts] [jusqu'à 7 octets]
...
```

### Registration

Contrôleur dédié utilisant la commande CVP validée :

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

### Style

Centralisation :
- chemin/nom/source GET ;
- Sync Start GET/SET ;
- Section Control ;
- mute des huit parties.

La sélection directe du Style par numéro reste verrouillée :
**VALIDÉE GENOS / NON VALIDÉE CVP**.

### Voice

La propriété CVP `02 00 01 01` reste disponible en lecture brute.

Les helpers XG Right1/2/3/Left sont présents pour la recherche mais restent
verrouillés : **VALIDÉS GENOS / NON VALIDÉS CVP**.

## Compatibilité

Le fichier d'entrée reste `cvp_access_v1.5.py` afin de ne pas casser systemd,
l'installateur et l'updater actuels.

`cvp_access_v1.4.1.py` reste nécessaire pendant cette étape.
