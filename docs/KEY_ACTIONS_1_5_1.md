# CVP Access 1.5.1 — actions clavier RC2

## Principe

Le clavier est une interface d'accessibilité complémentaire au CVP-905. Les commandes déjà facilement accessibles sur le panneau du CVP ne sont pas dupliquées sans raison. Les fonctions de protocole validées peuvent rester disponibles dans le catalogue sans être attribuées au clavier.

## Aide vocale CTRL

`CTRL + touche` annonce la fonction de la touche **sans l'exécuter**.

Exemples :

- `CTRL + W` : annonce « Nom du Style » ;
- `CTRL + V` : annonce « Active ou désactive Syncro Start » ;
- `CTRL + Page ↑` : annonce « Augmenter le volume Style de 1 ».

La couche `Caps Lock` n'est plus utilisée dans le layout RC2.

## Layout principal

### Parties Style

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
| F7 | Métronome ON/OFF |

Si aucun Song n'est chargé, `X` et `C` annoncent **« Pas de Song chargé. »**

### Song

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

### Volumes

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

Ces actions restent implémentées et documentées mais ne sont volontairement pas affectées au clavier RC2 :

- Intro Style 1..3 ;
- Main Style A..D ;
- Fill Style A..D ;
- Break Style ;
- Ending Style 1..3 ;
- Registration Memory 1..8 ;
- Stream Lights ON/OFF.

Elles apparaissent dans la section **« Actions disponibles mais non attribuées »** de la map clavier.

## Synthèse vocale

Le mode par défaut reste `hybrid`.

- les WAV pré-générés sont joués immédiatement ;
- les phrases dynamiques sont mises en cache ;
- Piper est préchargé au démarrage afin d'éviter le délai important de la première synthèse ;
- les noms de Style et de Song déjà rencontrés sont réutilisés depuis le cache.

Le terme utilisateur est **« Syncro Start »**. L'identifiant interne reste `sync_start_toggle`. La documentation protocole Yamaha conserve le nom officiel **Sync Start**.

## Règle de sécurité

Une signature de protocole connue n'est pas automatiquement une commande utilisateur sûre.

Restent notamment hors attribution directe :

- Guide Type ;
- Piano Lid / Environment / VRM / Resonance lorsque la sémantique utilisateur n'est pas suffisamment consolidée ;
- Stream Lights Speed ;
- global Reverb : GET seulement ;
- Voice Name CVP : identité lisible non résolue ;
- sélection directe Style : validée Genos uniquement ;
- ACMP et Fingering direct : recherches clôturées, workaround Registration.
