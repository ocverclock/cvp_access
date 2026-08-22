# CVP Access — catalogue maître des fonctions Yamaha

Matériel de référence : **Yamaha CVP-905, firmware 1.03**.

Ce fichier décrit l'état **actuel** des connaissances. Les anciens scripts de recherche ne priment jamais sur ce catalogue.

Statuts :

- **VALIDÉE** : test matériel exploitable ;
- **GET VALIDÉ** : lecture validée, écriture non revendiquée ;
- **PARTIELLE** : validée seulement sur certains indexes/aspects ;
- **NON RÉSOLUE** : la propriété répond ou existe, mais sa sémantique/commande n'est pas établie ;
- **NON APPLICABLE / DANGEREUX** : ne pas exposer au runtime.

## Identification

| Fonction | Signature | Statut |
|---|---|---|
| Modèle | `0F 01 18 01 | 00` | GET VALIDÉ — données correspondant à `CVP-905` |
| Firmware | `0F 01 0B 01 | 00` | GET VALIDÉ — `1.03` |

Le décodage texte Yamaha reste à corriger : les observations correspondent à des groupes de 7 caractères avec masque, pas à une simple longueur 14-bit en tête.

## Song

| Fonction | Signature | Statut |
|---|---|---|
| Play / Pause / Stop | `04 00 05 01 | 00` | VALIDÉE — `00/01/02` |
| Position mesure/temps | `04 00 0A 01 | 00` | VALIDÉE |
| Longueur | `04 00 1B 01 | 00` | GET VALIDÉ |
| Nom du Song | `04 00 01 01 | 00` | GET brut VALIDÉ ; décodage texte à revalider |
| Boucle A/B | `04 00 0D 01 | 00` | VALIDÉE GET/SET |
| Présence pistes | `04 01 00 01 | 10..1F` | GET VALIDÉ |
| Parties pédagogiques | `04 00 0E 01 | 00..02` | VALIDÉE GET/SET |
| Partie index `03` | `04 00 0E 01 | 03` | NON APPLICABLE / SET naïf -> `0x31` |
| Affectation auto | `04 00 10 01 | 00` | VALIDÉE GET/SET |

Détection « aucun Song » actuellement retenue :

```text
song_name EMPTY
ET aucune piste 1..16 présente
```

Attention : `cvp_song.py` doit encore fiabiliser son décodeur texte.

## Song mixer / parties clavier

Indexes principaux :

```text
00 Main
01 Layer
02 Left
10..1F Song 1..16
40 Mic
41 AuxIn
44 Wave
50 MidiMaster / Song global
51 Style
```

| Fonction | Signature | Statut |
|---|---|---|
| Active Main/Layer/Left | `0C 00 01 01` | VALIDÉE |
| Active Song 1..16 | `0C 00 01 01` | VALIDÉE |
| Volume | `0C 00 00 01` | VALIDÉ sur Main/Layer/Left/Song1/Mic/AuxIn/Wave/MidiMaster/Style |
| Pan | `0C 00 03 01` | VALIDÉ sur Main/Layer/Left/Song1/Style |
| Reverb send | `0C 00 04 01` | VALIDÉ sur Main/Layer/Left/Song1/Style |
| Voice MIDI | `02 00 01 01` | GET VALIDÉ dynamiquement |
| Voice preset | `02 00 00 01` | GET EMPTY sur CVP-905 |

Active Wave `44` n'est pas un booléen simple : SET naïf a produit `0x31`.

## Tempo / transpose

| Fonction | Signature | Statut |
|---|---|---|
| Tempo | `08 00 00 01 | 00` | VALIDÉE |
| Transpose | `0A 00 00 01 | 02` | VALIDÉE |

## Style — runtime

| Fonction | Mécanisme | Statut |
|---|---|---|
| Volume global | `0C 00 00 01 | 51` | VALIDÉE |
| Mute 8 parties | `F0 43 73 01 51 05 00 00 08 ... F7` | VALIDÉE |
| Start / Stop | `06 00 03 01 | 00` | VALIDÉE |
| Intro 1/2/3 | Section Control `00/01/02` | VALIDÉE |
| Main A/B/C/D | Section Control `08..0B` | VALIDÉE |
| Fill A/B/C/D | Section Control `10..13` | VALIDÉE |
| Break | Section Control `18` | VALIDÉE |
| Ending 1/2/3 | Section Control `20..22` | VALIDÉE |

Section Control :

```text
F0 43 7E 00 ss 7F F7
```

## Registration Memory

Rappel 1..8 VALIDÉ :

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
XX = 00..07
```

Notification observée :

```text
F0 43 73 01 52 25 00 01 01 00 01 XX F7
```

## Split Point / Fingering Type

Style Split Point VALIDÉ :

```text
F0 43 73 01 51 00 00 00 03 10 00 dd F7
```

Left Split Point VALIDÉ :

```text
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

`10 02` testé comme Fingering direct : **négatif**.

Valeurs de stockage `.rgt/.ssu` :

```text
03 AI Fingered
04 Fingered
0C AI Full Keyboard
```

Commande MIDI Fingering directe : **NON RÉSOLUE**. Campagne active : scanner V2 SQLite GET-only.

## Guide Yamaha

| Fonction | Signature | Statut |
|---|---|---|
| Guide ON/OFF | `04 03 00 01 | 00` | VALIDÉE GET/SET |
| Guide Type | `04 03 01 01 | 00` | VALIDÉE GET/SET sur valeurs testées |

Ce Guide est la fonction pédagogique Yamaha, pas le Voice Guide d'accessibilité.

## Piano Room / piano

| Fonction | Signature | Statut |
|---|---|---|
| Lid | `02 02 07 01` | VALIDÉE |
| Environment | `02 02 03 01` | VALIDÉE |
| VRM | `02 02 00 01` | VALIDÉE |
| Damper Resonance | `02 02 01 01` | VALIDÉE |
| String Resonance | `02 02 02 01` | VALIDÉE |
| Key-Off Sampling | `02 02 06 01` | TIMEOUT / NON RÉSOLUE |
| Brightness | `0C 00 0B 01` | NON RÉSOLUE ; SET naïf -> `0x31` |
| Touch Curve | `00 00 00 01` | NON RÉSOLUE |
| Fixed Curve | `00 00 01 01` | NON RÉSOLUE |
| Fixed Velocity | `00 00 02 01` | NON RÉSOLUE |
| Master Tune | `03 00 00 01` | NON RÉSOLUE |

## Stream Lights

| Fonction | Signature | Statut |
|---|---|---|
| Stream Lights ON/OFF | `04 02 00 01 | 00` | VALIDÉE GET/SET |
| Stream Speed | `04 02 02 01 | 00` | NON APPLICABLE / SET naïf -> `0x31` |

## Réverb globale

`0C 01 00 01 | 00` : GET VALIDÉ dynamiquement. SET non testé.

## EVENTS / XG / sniff — conclusions de recherche

- CSP EVENTS : fonctionnel sur plusieurs propriétés connues, mais pas de signal Fingering exploitable après rappel Registration.
- XG documenté : 9 137 adresses testées, 1 936 répondantes, aucun candidat Fingering.
- Sniff passif panneau : pas de SysEx exploitable pour Split/Fingering.
- Special Operator Fingering historique : ignoré par CVP-905.

Ne pas répéter ces campagnes sans nouvelle hypothèse.

## Règle `0x31`

Toute lecture `0x31` apparue après un SET supposé bool/u7 doit être considérée comme un **signal d'arrêt** et non comme une valeur valide.
