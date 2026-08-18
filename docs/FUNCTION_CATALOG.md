# CVP Access — catalogue maître des fonctions Yamaha / ConPianist

Ce catalogue est volontairement plus large que `KEY_ACTIONS.md`.

Matériel de référence actuel : **Yamaha CVP-905, firmware 1.03**.

- **VALIDÉE** : fonction testée sur le CVP-905 réel et exploitable.
- **PARTIELLE** : propriété validée sur certains indexes ou seulement en GET.
- **GET À TESTER** : propriété connue mais pas encore validée sur le CVP réel.
- **SET À TESTER** : écriture concevable mais à ne pas exposer au clavier avant validation.
- **NON RÉSOLUE CVP-905** : signature connue mais non corrélée au réglage affiché ou format non compris.
- **SPÉCIFIQUE / NON APPLICABLE CVP-905** : fonction pouvant exister sur d'autres Yamaha mais absente ou différente sur le CVP-905.

Une fonction ne passe dans `KEY_ACTIONS.md` qu'après validation **et implémentation**.

## Identification

| Fonction | Signature / mécanisme | Statut CVP-905 |
|---|---|---|
| Modèle du piano | `0F 01 18 01` | GET VALIDÉ — données = `CVP-905` après décodage Yamaha 7-bit |
| Version firmware | `0F 01 0B 01` | GET VALIDÉ — `1.03` |

Le décodage texte actuel du probe doit encore être corrigé : les chaînes Yamaha sont organisées en groupes de 7 caractères précédés d'un octet de masque, et non par une longueur 14-bit en tête.

## Song / transport

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Play / Pause / Stop | `04 00 05 01` | **VALIDÉE** — `00=Stop`, `01=Play`, `02=Pause` |
| Position mesure + temps | `04 00 0A 01` | **GET VALIDÉ** — 4 octets = mesure 14-bit + temps 14-bit ; SET direct à confirmer formellement |
| Longueur du morceau | `04 00 1B 01` | GET VALIDÉ — attention : sans Song, renvoie quand même `1:1` |
| Nom du morceau | `04 00 01 01` | GET VALIDÉ — décodage texte à corriger |
| Boucle A/B | `04 00 0D 01` | **GET/SET VALIDÉS** |
| Reset Song | `04 00 00 01` | SET À TESTER |
| Présence piste 1–16 | `04 01 00 01`, indexes `10..1F` | GET VALIDÉ — sans Song : pistes absentes ; avec Song de test : pistes présentes |

### Structure validée de la boucle A/B

Le GET/SET de `04 00 0D 01`, index `00`, utilise 9 octets :

```text
byte 0      : 00 = boucle OFF / 01 = boucle ON
bytes 1-2   : mesure A, 14-bit
bytes 3-4   : temps A, 14-bit
bytes 5-6   : mesure B, 14-bit
bytes 7-8   : temps B, 14-bit
```

Exemple matériel validé : boucle mesures **15 à 16**, temps 1 :

```text
01 00 0F 00 01 00 10 00 01
```

Comportement important du CVP-905 : quand la boucle est arrêtée, le piano réinitialise ses bornes à :

```text
00 00 01 00 01 00 02 00 01
```

CVP Access devra donc **mémoriser localement A et B** et les renvoyer au prochain `Loop ON`.

### Ergonomie Loop prévue dans CVP Access

Cette fonction est considérée comme importante, y compris pour un musicien voyant, car l'interface native oblige à redéfinir la boucle après son arrêt.

Actions prévues :

```text
Mesure -             : position -1 mesure
Mesure +             : position +1 mesure
Shift + Mesure -     : position -5 mesures
Shift + Mesure +     : position +5 mesures
Aller à la mesure    : saisie directe d'un numéro
Point A              : mémorise la mesure courante
Point B              : mémorise la mesure courante
Boucle ON/OFF        : réactive A/B mémorisés sans les redéfinir
```

Pour l'utilisateur, les points de boucle seront volontairement placés au **début des mesures (temps 1)** afin de garder l'usage simple.

## Pistes Song 1–16 / mixer

Indexes Song : `0x10 .. 0x1F`.

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Active / mute | `0C 00 01 01` | **VALIDÉE** |
| Volume individuel | `0C 00 00 01` | PARTIELLE — GET/SET validés sur Song 1 ; valeurs observées sur les 16 pistes |
| Pan | `0C 00 03 01` | PARTIELLE — GET/SET validés sur Song 1 |
| Réverb | `0C 00 04 01` | PARTIELLE — GET/SET validés sur Song 1 |
| Voice MIDI | `02 00 01 01` | GET VALIDÉ — valeurs 4 octets dynamiques selon la Voice ; SET non testé |

## Parties Song pédagogiques

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Parties index `00..02` ON/OFF | `04 00 0E 01` | **GET/SET VALIDÉS** |
| Index `03` | `04 00 0E 01` | NON APPLICABLE / format spécial sur CVP-905 — un SET bool naïf retourne `0x31` |
| Canal affecté aux parties | `04 00 0F 01` | GET VALIDÉ sur indexes observés ; SET non testé |
| Affectation automatique | `04 00 10 01` | **GET/SET VALIDÉS** |

## Tempo / transpose

| Fonction | Signature | Statut |
|---|---|---|
| Tempo 5–280 | `08 00 00 01` | **VALIDÉE** |
| Transpose −12..+12 | `0A 00 00 01` | **VALIDÉE** |

## Style

| Fonction | Mécanisme | Statut |
|---|---|---|
| Volume global Style | `0C 00 00 01`, index `51` | **VALIDÉE** |
| Mute 8 parties Style | `F0 43 73 01 51 05 00 00 08 ... F7` | **VALIDÉE** sur ordre RHY1/RHY2/BASS/CHD1/CHD2/PAD/PHR1/PHR2 |

Le GET individuel des 8 mutes Style n'est pas encore validé ; CVP Access conserve un cache déterministe.

## Parties clavier Main / Layer / Left

Indexes : Main `00`, Layer `01`, Left `02`.

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Main Active | `0C 00 01 01`, index `00` | **GET/SET VALIDÉS** |
| Layer Active | `0C 00 01 01`, index `01` | **VALIDÉE** |
| Left Active | `0C 00 01 01`, index `02` | **VALIDÉE** |
| Voice preset | `02 00 00 01` | GET EMPTY sur CVP-905 |
| Voice MIDI | `02 00 01 01`, indexes `00/01/02` | **GET VALIDÉ dynamiquement** sur Main / Layer / Left |
| Octave | `0C 00 12 01` | SPÉCIFIQUE / NON APPLICABLE CVP-905 — option absente, SET non testé |
| Split point | `09 00 00 01` | NON RÉSOLUE CVP-905 |

## Guide Yamaha

Ce Guide est la fonction pédagogique Yamaha, pas le Voice Guide d'accessibilité.

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Guide ON/OFF | `04 03 00 01` | **GET/SET VALIDÉS** |
| Type de Guide | `04 03 01 01` | **GET/SET VALIDÉS** sur valeurs testées |

## Mixer / entrées supplémentaires

Indexes connus :

```text
00 Main
01 Layer
02 Left
10..1F Song 1..16
40 Mic
41 AuxIn
44 Wave
50 MidiMaster
51 Style
```

Validations CVP-905 :

- **Volume GET/SET** : Main, Layer, Left, Song 1, Mic, AuxIn, Wave, MidiMaster.
- **Pan GET/SET** : Main, Layer, Left, Song 1, Style.
- **Reverb send GET/SET** : Main, Layer, Left, Song 1, Style.
- **Active GET/SET** : Main et Mic.
- `Active` index Wave `44` **n'est pas un booléen simple** sur CVP-905 : tentative `01→00` a provoqué une lecture `0x31`, puis `0x07` après redémarrage. Ne pas écrire cette propriété comme booléen.
- Active MidiMaster et Style n'ont pas été testés en SET, par prudence.

## Réverb globale

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Type de réverb | `0C 01 00 01` | **GET VALIDÉ dynamiquement** ; SET non testé |

Exemples observés :

```text
00 04 22
00 04 21
00 02 05
```

## Piano Room / réglages piano

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Lid / couvercle virtuel | `02 02 07 01` | **GET/SET VALIDÉS** |
| Environment | `02 02 03 01` | **GET/SET VALIDÉS** |
| Brightness / timbre | `0C 00 0B 01` | NON RÉSOLUE — GET répond, SET naïf a produit `0x31` |
| Touch Curve | `00 00 00 01` | NON RÉSOLUE — pas de corrélation fiable avec le réglage écran CVP-905 |
| Fixed Curve | `00 00 01 01` | NON RÉSOLUE CVP-905 |
| Fixed Velocity | `00 00 02 01` | NON RÉSOLUE CVP-905 |
| Master Tune | `03 00 00 01` | NON RÉSOLUE — GET répond sur 2 octets mais ne suit pas le réglage écran testé |
| VRM | `02 02 00 01` | **GET/SET VALIDÉS** |
| Damper Resonance | `02 02 01 01` | **GET/SET VALIDÉS** |
| String Resonance | `02 02 02 01` | **GET/SET VALIDÉS** |
| Key-Off Sampling | `02 02 06 01` | TIMEOUT sur CVP-905 |

## Stream Lights

Principalement pertinent pour les modèles CSP compatibles.

| Fonction | Signature | Statut CVP-905 |
|---|---|---|
| Stream Lights ON/OFF | `04 02 00 01` | **GET/SET VALIDÉS** |
| Vitesse Stream Lights | `04 02 02 01` | SPÉCIFIQUE / NON APPLICABLE CVP-905 — SET naïf a produit `0x31` |

## Valeur `0x31` : drapeau d'alerte

Plusieurs SET supposés bool/u7 sur des propriétés non applicables ou mal interprétées ont conduit à une lecture `0x31` :

- Active Wave index `44` ;
- partie pédagogique index `03` ;
- Stream Speed ;
- Brightness.

Sur CVP-905, l'apparition de `0x31` après un SET doit être traitée comme **un signal d'arrêt du test**.

## Détection « aucun Song chargé »

Le champ longueur du Song n'est pas suffisant : sans Song chargé, le CVP renvoie quand même `mesure 1 / temps 1`.

Le meilleur critère observé à ce stade est :

```text
song_name = EMPTY
ET
present tracks 1..16 = false
```

Cette détection doit encore être intégrée au runtime afin que Play/Pause annonce **« Aucun Song chargé »** au lieu d'envoyer une commande inutile.

## Local Control

```text
CC 122 = Local Control
0   = OFF
127 = ON
```

Statut : **À TESTER** avant exposition comme action clavier.

## Protocole d'échange

```text
GET       01 00
SET       01 01
INFO      00 00
RESPONSE  00 01
EVENTS    02 00
RESET     04 01
```

`EVENTS` reste une piste pour une future synchronisation en temps réel. Sur le CVP-905 testé, certaines modifications d'écran n'ont produit aucun SysEx spontané observable via la liaison actuelle.
