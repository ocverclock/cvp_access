# CVP Access — catalogue maître des fonctions Yamaha / ConPianist

Ce catalogue est volontairement plus large que `KEY_ACTIONS.md`.

- **VALIDÉE** : fonction testée sur le matériel CVP et utilisable dans CVP Access.
- **PARTIELLE** : propriété déjà validée sur certains indexes seulement.
- **GET À TESTER** : propriété connue et présente dans le probe read-only, mais pas encore validée sur le CVP réel.
- **SET À TESTER** : écriture connue/concevable mais à ne pas exposer au clavier avant validation.
- **SPÉCIFIQUE** : dépend d'un modèle ou d'un usage particulier.

Une fonction ne passe dans `KEY_ACTIONS.md` qu'après validation et implémentation.

## Identification

| Fonction | Signature / mécanisme | Statut |
|---|---|---|
| Modèle du piano | `0F 01 18 01` | GET À TESTER |
| Version firmware | `0F 01 0B 01` | GET À TESTER |

## Song / transport

| Fonction | Signature | Statut |
|---|---|---|
| Play / Pause / Stop | `04 00 05 01` | VALIDÉE |
| Position mesure + temps | `04 00 0A 01` | VALIDÉE |
| Longueur du morceau | `04 00 1B 01` | GET À TESTER |
| Nom du morceau | `04 00 01 01` | GET À TESTER |
| Boucle | `04 00 0D 01` | GET/SET À TESTER |
| Reset Song | `04 00 00 01` | SET À TESTER |
| Présence piste 1–16 | `04 01 00 01`, indexes `10..1F` | GET À TESTER |

## Pistes Song 1–16 / mixer

Indexes Song : `0x10 .. 0x1F`.

| Fonction | Signature | Statut |
|---|---|---|
| Active / mute | `0C 00 01 01` | VALIDÉE |
| Volume individuel | `0C 00 00 01` | PARTIELLE — propriété volume validée sur Style |
| Pan | `0C 00 03 01` | GET/SET À TESTER |
| Réverb | `0C 00 04 01` | GET/SET À TESTER |
| Voice MIDI | `02 00 01 01` | GET/SET À TESTER |

## Parties Song pédagogiques

| Fonction | Signature | Statut |
|---|---|---|
| Right / Left / Backing ON/OFF | `04 00 0E 01` | GET/SET À TESTER |
| Canal affecté aux parties | `04 00 0F 01` | GET/SET À TESTER |
| Affectation automatique | `04 00 10 01` | GET/SET À TESTER |

ConPianist contient une ambiguïté historique sur l'index Backing ; le probe teste volontairement `0,1,2,3`.

## Tempo / transpose

| Fonction | Signature | Statut |
|---|---|---|
| Tempo 5–280 | `08 00 00 01` | VALIDÉE |
| Transpose −12..+12 | `0A 00 00 01` | VALIDÉE |

## Style

| Fonction | Mécanisme | Statut |
|---|---|---|
| Volume global Style | `0C 00 00 01`, index `51` | VALIDÉE |
| Mute 8 parties Style | `F0 43 73 01 51 05 00 00 08 ... F7` | VALIDÉE sur ordre RHY1/RHY2/BASS/CHD1/CHD2/PAD/PHR1/PHR2 |

Le GET individuel des 8 mutes Style n'est pas encore validé ; CVP Access conserve un cache déterministe.

## Parties clavier Main / Layer / Left

Indexes : Main `00`, Layer `01`, Left `02`.

| Fonction | Signature | Statut |
|---|---|---|
| Layer Active | `0C 00 01 01`, index `01` | VALIDÉE |
| Left Active | `0C 00 01 01`, index `02` | VALIDÉE |
| Main Active | `0C 00 01 01`, index `00` | GET/SET À TESTER |
| Voice preset | `02 00 00 01` | GET/SET À TESTER |
| Octave | `0C 00 12 01` | GET/SET À TESTER |
| Split point | `09 00 00 01` | GET/SET À TESTER |

## Guide Yamaha

Ce Guide est la fonction pédagogique Yamaha, pas le Voice Guide d'accessibilité.

| Fonction | Signature | Statut |
|---|---|---|
| Guide ON/OFF | `04 03 00 01` | GET/SET À TESTER |
| Type de Guide | `04 03 01 01` | GET/SET À TESTER |

Modes connus : Correct Key, Any Key, Your Tempo.

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

Propriétés candidates : Volume, Active, Pan, Reverb suivant l'index et la compatibilité du modèle.

## Réverb globale

| Fonction | Signature | Statut |
|---|---|---|
| Type de réverb | `0C 01 00 01` | GET/SET À TESTER |

## Piano Room / réglages piano

| Fonction | Signature | Statut |
|---|---|---|
| Lid / couvercle virtuel | `02 02 07 01` | GET/SET À TESTER |
| Environment | `02 02 03 01` | GET/SET À TESTER |
| Brightness / timbre | `0C 00 0B 01` | GET/SET À TESTER |
| Touch Curve | `00 00 00 01` | GET/SET À TESTER |
| Fixed Curve | `00 00 01 01` | GET/SET À TESTER |
| Fixed Velocity | `00 00 02 01` | GET/SET À TESTER |
| Master Tune | `03 00 00 01` | GET/SET À TESTER |
| VRM | `02 02 00 01` | GET/SET À TESTER |
| Damper Resonance | `02 02 01 01` | GET/SET À TESTER |
| String Resonance | `02 02 02 01` | GET/SET À TESTER |
| Key-Off Sampling | `02 02 06 01` | GET/SET À TESTER |

## Stream Lights

Principalement pertinent pour les modèles CSP compatibles.

| Fonction | Signature | Statut |
|---|---|---|
| Stream Lights ON/OFF | `04 02 00 01` | GET/SET À TESTER / SPÉCIFIQUE |
| Vitesse Stream Lights | `04 02 02 01` | GET/SET À TESTER / SPÉCIFIQUE |

## Local Control

ConPianist utilise également le MIDI standard :

```text
CC 122 = Local Control
0   = OFF
127 = ON
```

Statut : **À TESTER** avant exposition comme action clavier.

## Protocole d'échange

Actions Yamaha/CSP connues :

```text
GET       01 00
SET       01 01
INFO      00 00
RESPONSE  00 01
EVENTS    02 00
RESET     04 01
```

`EVENTS` est une piste importante pour une future synchronisation en temps réel sans multiplier les GET.

## Procédure de validation

Avant de créer une nouvelle action clavier :

```text
propriété connue
    ↓
GET via docs/cvp_probe_readonly.py
    ↓
réponse DATA
    ↓
interprétation / test fonctionnel
    ↓
SET prudent si nécessaire
    ↓
GET de vérification
    ↓
statut VALIDÉE
    ↓
implémentation Python
    ↓
ajout KEY_ACTIONS
    ↓
affectable dans keyboard.toml
```
