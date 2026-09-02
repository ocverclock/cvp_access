# CVP Access 1.5.1 — actions clavier RC3

## Principe

Le clavier est une interface d’accessibilité complémentaire au Yamaha CVP-905.

Les fonctions de protocole validées peuvent rester disponibles dans le catalogue sans être attribuées au clavier.

## Aide vocale CTRL

```text
CTRL + touche
```

annonce la fonction de la touche **sans exécuter l’action**.

Exemples :

```text
CTRL + W
-> annonce l'aide du nom Style
-> ne lit pas le Style

CTRL + N
-> annonce l'aide du nom Voice Main
-> ne lit pas la Voice
```

La couche Caps Lock expérimentale de RC1 n’est plus utilisée dans le layout 1.5.1.

## Layout principal

### Parties Style / clavier

| Touche | Action |
|---|---|
| 1 | mute Rythme 1 |
| 2 | mute Rythme 2 |
| 3 | mute Basse |
| 4 | mute Accord 1 |
| 5 | mute Accord 2 |
| 6 | mute Pad |
| 7 | mute Phrase 1 |
| 8 | mute Phrase 2 |
| 9 | Layer / Dual |
| 0 | Left |

### Pistes Song

| Touches | Action |
|---|---|
| A Z E R T Y U I | pistes Song 1 à 8 |
| Q S D F G H J K | pistes Song 9 à 16 |

### Informations et accessibilité

| Touche | Action |
|---|---|
| W | annonce le nom du Style courant |
| X | annonce le nom du Song chargé |
| C | annonce la longueur du Song |
| V | Syncro Start ON/OFF |
| B | Guide ON/OFF |
| N | annonce le nom de la Voice Main |
| , | annonce le nom de la Voice Layer |
| ; | annonce le nom de la Voice Left |
| F7 | Métronome ON/OFF |

Sans Song chargé, `X` et `C` annoncent :

```text
Pas de Song chargé.
```

## Voice Main / Layer / Left

Propriété :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Affectations TOML :

```toml
"N" = "announce_main_voice_name"
"COMMA" = "announce_layer_voice_name"
"SEMICOLON" = "announce_left_voice_name"
```

La synthèse prononce uniquement le nom du son.

Exemple :

```text
N
-> CFX Concert Grand
```

et non :

```text
Main CFX Concert Grand
```

Voices de validation RC3 :

```text
108/0/1   = CFX Concert Grand
8/33/50   = Seattle Strings
104/7/5   = Suitcase Soft
```

La table locale des noms reste partielle en RC3.

## Song

| Touche | Action |
|---|---|
| Espace | lecture / pause |
| Entrée | stop |
| P | annonce position |
| ← / → | mesure -1 / +1 |
| Maj + ← / → | mesure -5 / +5 |
| F3 | aller à une mesure |
| F4 | point de boucle A |
| F5 | point de boucle B |
| F6 | boucle A/B |

## Volumes

| Touche | Action |
|---|---|
| ↑ / ↓ | Vol. guide vocal + / - |
| Page ↑ / Page ↓ | Volume Style +1 / -1 |
| Maj + Page ↑ / Page ↓ | Volume Style +5 / -5 |
| Origine / Fin | Volume Song +1 / -1 |
| Maj + Origine / Fin | Volume Song +5 / -5 |
| Inser / Suppr | Volume Main +1 / -1 |
| Maj + Inser / Suppr | Volume Main +5 / -5 |

## Actions disponibles mais non attribuées

Ces actions restent implémentées et documentées sans affectation par défaut :

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights ON/OFF
```

Elles doivent apparaître dans la section :

```text
Actions disponibles mais non attribuées
```

de la map clavier.

## Synthèse vocale

Mode :

```text
hybrid
```

Politique :

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> cache
```

Piper est préchargé au démarrage.

La RC3 corrige également l’arrêt du worker Piper afin qu’un arrêt systemd normal, y compris pendant le préchargement, ne nécessite plus de SIGKILL.

## Terminologie utilisateur

```text
Syncro Start
Vol. guide vocal
Pas de Song chargé.
```

Identifiant interne conservé :

```text
sync_start_toggle
```

Les documents protocole peuvent conserver le terme Yamaha officiel `Sync Start`.

## Règle de sécurité

Une signature de protocole connue n’est pas automatiquement une commande utilisateur sûre.

Restent notamment hors attribution directe :

```text
Guide Type
Stream Lights Speed
Global Reverb SET
sélection directe Style CVP
ACMP direct
Fingering direct
```

ACMP et Fingering utilisent les mécanismes Registration déjà validés.

Les résultats Genos ne sont jamais considérés comme validés CVP sans test physique sur CVP-905.
