# CVP Access — catalogue maître des fonctions Yamaha

Matériel de référence principal : **Yamaha CVP-905, firmware 1.03**.

Dernière consolidation : **1 septembre 2026 — CVP Access 1.5.1-RC3**.

Les résultats Genos 1 sont explicitement marqués et ne constituent pas une validation CVP.

## Statuts

- **VALIDÉE** : test matériel exploitable sur CVP-905.
- **GET VALIDÉ** : lecture CVP validée, écriture non revendiquée.
- **PARTIELLE** : validée seulement sur certains indexes/aspects.
- **NON RÉSOLUE** : fonction recherchée mais commande/propriété non établie.
- **CLÔTURÉE DIRECT** : recherche de commande MIDI directe arrêtée pour le projet courant.
- **NON APPLICABLE / DANGEREUX** : ne pas exposer au runtime.
- **VALIDÉ GENOS / NON TESTÉ CVP** : résultat matériel Genos uniquement.

## Identification CVP

| Fonction | Signature | Statut |
|---|---|---|
| Modèle | `0F 01 18 01 \| 00` | GET VALIDÉ — CVP-905 |
| Firmware | `0F 01 0B 01 \| 00` | GET VALIDÉ — 1.03 |

Format texte Yamaha observé sur Song/Style :

```text
1 octet masque + jusqu'à 7 octets de données
```

L’ancienne hypothèse d’une longueur 14-bit en tête ne doit plus être utilisée pour ces propriétés.

## Song

| Fonction | Signature | Statut |
|---|---|---|
| Play / Pause / Stop | `04 00 05 01 \| 00` | VALIDÉE — `00/01/02` |
| Position mesure/temps | `04 00 0A 01 \| 00` | VALIDÉE |
| Longueur | `04 00 1B 01 \| 00` | GET VALIDÉ |
| Chemin / nom du Song | `04 00 01 01 \| 00` | GET VALIDÉ |
| Boucle A/B | `04 00 0D 01 \| 00` | VALIDÉE GET/SET |
| Présence pistes | `04 01 00 01 \| 10..1F` | GET VALIDÉ |
| Parties pédagogiques | `04 00 0E 01 \| 00..02` | VALIDÉE GET/SET |
| Partie index `03` | `04 00 0E 01 \| 03` | NON APPLICABLE — SET naïf -> `0x31` |
| Affectation auto | `04 00 10 01 \| 00` | VALIDÉE GET/SET |
| Sélection directe Song | — | NON RÉSOLUE |

Exemple :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

Le runtime 1.5.1 utilise `cvp_song_151.py` pour le décodage corrigé.

Le fichier historique `cvp_song.py` peut encore contenir l’ancien décodeur et ne doit pas être pris comme source de vérité pour ce point.

## Mixer / parties clavier CVP

Indexes principaux connus :

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
| Volume | `0C 00 00 01` | VALIDÉ sur principaux indexes |
| Pan | `0C 00 03 01` | VALIDÉ sur principaux indexes |
| Reverb send | `0C 00 04 01` | VALIDÉ sur principaux indexes |
| Voice MIDI / identité | `02 00 01 01` | GET VALIDÉ — Main/Layer/Left ; décodage 4×7 bits validé |
| Voice preset/path | `02 00 00 01` | GET EMPTY sur CVP-905 |

Active Wave `44` n’est pas un booléen simple : SET naïf -> `0x31`.

## Voice Name CVP-905 — VALIDÉ RC3

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

Réponses physiquement observées :

```text
Main  : 03 30 00 00
Layer : 00 20 42 31
Left  : 03 20 0E 04
```

Décodage :

```python
packed = (b0 << 21) | (b1 << 14) | (b2 << 7) | b3
msb = (packed >> 16) & 0xFF
lsb = (packed >> 8) & 0xFF
program = (packed & 0xFF) + 1
```

Correspondances validées :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

Statut :

```text
lecture CSP             : VALIDÉE
indexes Main/Layer/Left : VALIDÉS
décodage 4 × 7 bits     : VALIDÉ
table complète Yamaha   : À FAIRE
```

Voir :

```text
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
```

## Tempo / transpose

| Fonction | Signature | Statut |
|---|---|---|
| Tempo | `08 00 00 01 \| 00` | VALIDÉE |
| Transpose | `0A 00 00 01 \| 02` | VALIDÉE |

## Style — CVP runtime

| Fonction | Mécanisme | Statut |
|---|---|---|
| Chemin / nom / source | `06 00 00 01 \| 00` | GET VALIDÉ — PRESET/USER/USB1 |
| Volume global | `0C 00 00 01 \| 51` | VALIDÉE |
| Mute 8 parties | `F0 43 73 01 51 05 00 00 08 ... F7` | VALIDÉE |
| Start / Stop | `06 00 03 01 \| 00` | VALIDÉE |
| Sync Start | `06 00 07 01 \| 00` | VALIDÉE GET/SET |
| Intro 1/2/3 | Section Control `00/01/02` | VALIDÉE |
| Main A/B/C/D | Section Control `08..0B` | VALIDÉE |
| Fill A/B/C/D | Section Control `10..13` | VALIDÉE |
| Break | Section Control `18` | VALIDÉE |
| Ending 1/2/3 | Section Control `20..22` | VALIDÉE |
| Sélection directe Style | — | NON RÉSOLUE sur CVP ; VALIDÉE sur Genos uniquement |

Chemins observés :

```text
PRESET:/STYLE/Pop&Rock/Pop/Cool 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/80s 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/Up-tempo 8Beat.T308.prs
USER:/STYLE/80sMajestyRock.T548.prs
USB1:/training.T310.sty
```

Section Control :

```text
F0 43 7E 00 ss 7F F7
```

## Style — fonctions fermées / ouvertes

| Fonction | Statut | Remarque |
|---|---|---|
| ACMP | CLÔTURÉE DIRECT | workaround Registration validé |
| Auto Fill In | CLÔTURÉE DIRECT | documentation panel-only + scan négatif |
| Synchro Stop | CLÔTURÉE DIRECT | documentation panel-only + scan négatif |
| OTS Link | NON RÉSOLUE | zone CSP `06` déjà négative |

Scans ACMP déjà terminés :

```text
06 00..0F 00..7F 01 | index 00
wide 00..0F/00..03/00..1F | index 00
06 00 00..7F 01 | index 00..7F
```

Ne pas les répéter.

## Registration Memory

Rappel 1..8 VALIDÉ :

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
XX = 00..07
```

Notification :

```text
F0 43 73 01 52 25 00 01 01 00 01 XX F7
```

### ACMP dans `.rgt` — VALIDÉ

```text
GPm07 payload[2]

00 = ACMP OFF
7F = ACMP ON
```

Un Registration minimal identique sauf ACMP a restauré correctement ON/OFF sans changement de Style, Fingering ou Voice.

### Fingering dans `.rgt` — VALIDÉ

```text
GPm07 payload[8]

03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

### Parties Style dans `.rgt` — VALIDÉ

```text
GPm08 data[7]

bit0 Rhythm1
bit1 Rhythm2
bit2 Bass
bit3 Chord1
bit4 Chord2
bit5 Pad
bit6 Phrase1
bit7 Phrase2
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

`10 02` testé comme Fingering direct : **NÉGATIF**.

Commande MIDI Fingering directe : **CLÔTURÉE pour la recherche actuelle**.

Workaround : Registration Memory.

### Campagnes Fingering épuisées

```text
CSP Deep Weekend : 13 074 432 clés, aucun A/B/A/B stable
CSP EVENTS       : 26 624 propriétés, aucun signal exploitable
XG               : 9 137 adresses, 1 936 réponses, aucun candidat
Sniff passif     : aucun SysEx exploitable
Special Operator : ignoré
```

Ne pas répéter sans nouvelle preuve indépendante.

## Guide Yamaha

| Fonction | Signature | Statut |
|---|---|---|
| Guide ON/OFF | `04 03 00 01 \| 00` | VALIDÉE GET/SET |
| Guide Type | `04 03 01 01 \| 00` | VALIDÉE GET/SET sur valeurs testées |

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
| Stream Lights ON/OFF | `04 02 00 01 \| 00` | VALIDÉE GET/SET |
| Stream Speed | `04 02 02 01 \| 00` | NON APPLICABLE — SET naïf -> `0x31` |

## Réverb globale

```text
0C 01 00 01 | 00
```

GET VALIDÉ dynamiquement. SET non testé.

# Genos 1 — pont de recherche

**Tout ce bloc est VALIDÉ GENOS / NON TESTÉ CVP sauf indication contraire.**

## Liaison XG

Universal Device Inquiry et XG Master Volume ont confirmé la liaison SysEx bidirectionnelle.

Le CSP moderne CVP `F0 43 73 01 52 25 26 ...` ne répond pas sur Genos 1.

## Voice XG — GET + SET VALIDÉS Genos

Mapping :

```text
Right1 -> 08 01
Right2 -> 08 02
Right3 -> 08 03
Left   -> 08 04
```

Paramètres :

```text
08 nn 01 = Bank Select MSB
08 nn 02 = Bank Select LSB
08 nn 03 = Program Number
```

GET :

```text
F0 43 30 4C 08 nn pp F7
```

SET :

```text
F0 43 10 4C 08 nn 01 MSB F7
F0 43 10 4C 08 nn 02 LSB F7
F0 43 10 4C 08 nn 03 PC  F7
```

Les quatre parties ont été validées par différentiel puis restauration/relecture.

Exemples :

```text
Right1  104/21/1  CFX ConcertGrand
Right2    8/47/50 KinoStrings
Right3    8/49/2  SteelAcousticFinger
Left      8/41/21 70sSuitcaseClean
```

## Style direct select — VALIDÉ Genos

```text
F0 43 73 01 51 05 00 03 04 00 00 HH LL F7
```

Encodage :

```text
HH = StyleNumber // 128
LL = StyleNumber % 128
```

Validations matérielles :

```text
00 00 -> Party Polka
10 11 -> Viennese Waltz
1C 71 -> AcousticBlues
```

Lecture directe du Style courant : **NON RÉSOLUE sur Genos**.

## External Controller Genos

Validé :

```text
Canal 16 CC#0 -> Style Start/Stop
BF 00 7F / BF 00 00

Canal 16 CC#5 -> Fingered/Fingered On Bass
BF 05 7F / BF 05 00
```

Valeurs internes observées :

```text
External Controller:
0x17 = Sync Stop
0x27 = Fingered/Fingered On Bass

Assignable/.ssu:
0x28 = Fingered
0x8E = ACMP
```

L’extrapolation `0x8D = ACMP External Controller` a produit un `.msu` rejeté : **hypothèse invalide**.

ACMP n’est pas exposé dans External Controller Genos 1.

Voir `docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md`.

## Règle `0x31`

Toute lecture `0x31` apparue après un SET supposé bool/u7 doit être traitée comme **signal d’arrêt**.

## Règle de recherche

- scan large inconnu : GET-only ;
- jamais de brute-force SET ;
- SET ciblé uniquement avec preuve suffisante ;
- restaurer l’état après validation ;
- ne jamais promouvoir un résultat Genos au statut CVP sans test CVP.
