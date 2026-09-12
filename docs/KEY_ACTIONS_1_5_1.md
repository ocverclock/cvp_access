# CVP Access 1.5.1 — actions clavier RC3

Consolidation : **12 septembre 2026**.

## Principe

Le clavier est une interface d’accessibilité complémentaire au Yamaha CVP-905. Les fonctions de protocole validées peuvent rester disponibles dans le catalogue sans être attribuées au clavier.

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

CTRL + ALT + E
-> annonce « Solo piste 3 »
-> ne modifie aucune piste
```

La couche Caps Lock expérimentale de RC1 n’est plus utilisée dans le layout 1.5.1.

## Layout principal

### Parties Style / clavier

| Touche | Action |
|---|---|
| 1 | mute/unmute Rythme 1 |
| 2 | mute/unmute Rythme 2 |
| 3 | mute/unmute Basse |
| 4 | mute/unmute Accord 1 |
| 5 | mute/unmute Accord 2 |
| 6 | mute/unmute Pad |
| 7 | mute/unmute Phrase 1 |
| 8 | mute/unmute Phrase 2 |
| 9 | Layer / Dual |
| 0 | Left |
| `) / °` | force les 8 parties Style sur ON |

Nom interne de la touche `) / °` :

```text
RPAREN
```

Terminologie vocale :

```text
OFF -> « Mute Rythme 1 », « Mute Basse », etc.
ON  -> « Rythme 1 activé », « Basse activée », etc.
```

Le raccourci `) / °` n’est pas un toggle : il force toujours les 8 parties sur ON.

### Pistes Song — commandes normales

| Touches | Action |
|---|---|
| A Z E R T Y U I | pistes Song 1 à 8, toggle ON/OFF |
| Q S D F G H J K | pistes Song 9 à 16, toggle ON/OFF |
| L | force les 16 pistes Song sur ON |

L n’est pas un toggle : il sert notamment à sortir rapidement d’un Solo.

### Pistes Song — mode Solo ALT

| Touche | Action |
|---|---|
| ALT + A | Solo piste 1 |
| ALT + Z | Solo piste 2 |
| ALT + E | Solo piste 3 |
| ALT + R | Solo piste 4 |
| ALT + T | Solo piste 5 |
| ALT + Y | Solo piste 6 |
| ALT + U | Solo piste 7 |
| ALT + I | Solo piste 8 |
| ALT + Q | Solo piste 9 |
| ALT + S | Solo piste 10 |
| ALT + D | Solo piste 11 |
| ALT + F | Solo piste 12 |
| ALT + G | Solo piste 13 |
| ALT + H | Solo piste 14 |
| ALT + J | Solo piste 15 |
| ALT + K | Solo piste 16 |

Comportement Solo :

1. la piste sélectionnée est mise sur ON ;
2. les 15 autres sont mises sur OFF ;
3. les 16 états sont relus pour vérification ;
4. une seule annonce `Solo piste N` est prononcée.

Les annonces `Solo piste 1` à `Solo piste 16` sont pré-générées en WAV.

### Informations et accessibilité

| Touche | Action |
|---|---|
| W | annonce le nom du Style courant |
| X | annonce le nom du Song chargé |
| C | annonce la longueur du Song |
| V | Syncro Start ON/OFF |
| B | Guide Yamaha ON/OFF |
| M | mute/réactivation du guide vocal CVP Access |
| N | annonce le nom de la Voice Main |
| , | annonce le nom de la Voice Layer |
| ; | annonce le nom de la Voice Left |
| F7 | Métronome ON/OFF |

Important :

```text
Guide Yamaha (B) != guide vocal CVP Access (M)
```

M coupe uniquement la sortie vocale de CVP Access : WAV et Piper. Le volume mémorisé reste inchangé.

Sans Song chargé, les actions Song concernées annoncent :

```text
Pas de Song chargé.
```

## Song transport et navigation

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

Les annonces de mesure utilisent des fragments WAV pré-générés jusqu’à la mesure 150.

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

## Affectations TOML essentielles

```toml
"RPAREN" = "style_all_parts_on"
"L" = "song_all_tracks_on"

"ALT+A" = "song_track_solo:1"
"ALT+Z" = "song_track_solo:2"
"ALT+E" = "song_track_solo:3"
"ALT+R" = "song_track_solo:4"
"ALT+T" = "song_track_solo:5"
"ALT+Y" = "song_track_solo:6"
"ALT+U" = "song_track_solo:7"
"ALT+I" = "song_track_solo:8"
"ALT+Q" = "song_track_solo:9"
"ALT+S" = "song_track_solo:10"
"ALT+D" = "song_track_solo:11"
"ALT+F" = "song_track_solo:12"
"ALT+G" = "song_track_solo:13"
"ALT+H" = "song_track_solo:14"
"ALT+J" = "song_track_solo:15"
"ALT+K" = "song_track_solo:16"

"M" = "voice_guide_mute_toggle"
```

L’upgrade ajoute ces bindings uniquement si les combinaisons sont libres. Une personnalisation existante doit être conservée et signalée comme conflit.

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

Touches :

```text
N = Main
, = Layer
; = Left
```

La synthèse prononce uniquement le nom du son. La table locale des noms reste partielle.

## Actions disponibles mais non attribuées

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights ON/OFF
```

Elles doivent apparaître dans la section `Actions disponibles mais non attribuées` de la map clavier.

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

Piper est préchargé au démarrage. La lecture audio est sérialisée afin d’éviter les coupures/craquements entre annonces rapides.

## État de validation

Validé physiquement sur CVP-905 : navigation Song, F3, boucles, transport et correctifs métronome associés.

À confirmer physiquement après déploiement du HEAD courant :

```text
M = mute guide vocal
libellés Style « Mute ... »
L = toutes pistes Song ON
) / ° = toutes parties Style ON
ALT + piste = Solo Song
```

## Terminologie utilisateur

```text
Syncro Start
Guide Yamaha
Guide vocal
Vol. guide vocal
Mute Rythme 1
Solo piste 1
Pas de Song chargé.
```

## Règle de sécurité

Une signature de protocole connue n’est pas automatiquement une commande utilisateur sûre. Restent notamment hors attribution directe : Guide Type, Stream Lights Speed, Global Reverb SET, sélection directe Style CVP, ACMP direct et Fingering direct.

Les résultats Genos ne sont jamais considérés comme validés CVP sans test physique sur CVP-905.
