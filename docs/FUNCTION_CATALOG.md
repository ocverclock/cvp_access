# CVP Access — catalogue maître des fonctions Yamaha

Matériel de référence : **Yamaha CVP-905, firmware 1.03**.

Dernière consolidation : **28 août 2026**.

Ce fichier décrit l'état **actuel** des connaissances. Les anciens scripts de recherche ne priment jamais sur ce catalogue.

Statuts :

- **VALIDÉE** : test matériel exploitable ;
- **GET VALIDÉ** : lecture validée, écriture non revendiquée ;
- **PARTIELLE** : validée seulement sur certains indexes/aspects ;
- **NON RÉSOLUE** : fonction recherchée mais commande/propriété non établie ;
- **NON APPLICABLE / DANGEREUX** : ne pas exposer au runtime.

## Identification

| Fonction | Signature | Statut |
|---|---|---|
| Modèle | `0F 01 18 01 | 00` | GET VALIDÉ — données correspondant à `CVP-905` |
| Firmware | `0F 01 0B 01 | 00` | GET VALIDÉ — `1.03` |

Le format texte Yamaha observé sur Song/Style utilise des blocs `1 octet masque + jusqu'à 7 octets de données`. L'ancienne hypothèse d'une longueur 14-bit en tête ne doit plus être utilisée pour ces propriétés.

## Song

| Fonction | Signature | Statut |
|---|---|---|
| Play / Pause / Stop | `04 00 05 01 | 00` | VALIDÉE — `00/01/02` |
| Position mesure/temps | `04 00 0A 01 | 00` | VALIDÉE |
| Longueur | `04 00 1B 01 | 00` | GET VALIDÉ |
| Chemin / nom du Song | `04 00 01 01 | 00` | GET VALIDÉ — chemin complet observé |
| Boucle A/B | `04 00 0D 01 | 00` | VALIDÉE GET/SET |
| Présence pistes | `04 01 00 01 | 10..1F` | GET VALIDÉ |
| Parties pédagogiques | `04 00 0E 01 | 00..02` | VALIDÉE GET/SET |
| Partie index `03` | `04 00 0E 01 | 03` | NON APPLICABLE / SET naïf -> `0x31` |
| Affectation auto | `04 00 10 01 | 00` | VALIDÉE GET/SET |

Exemple Song réellement observé :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

La propriété permet donc d'extraire au minimum :

```text
source
chemin
nom
extension
```

Détection « aucun Song » actuellement retenue :

```text
song_name EMPTY
ET aucune piste 1..16 présente
```

Important : `cvp_song.py` contient encore un ancien décodeur basé sur une longueur 14-bit. Il doit être corrigé pour utiliser le format par blocs observé.

Hypothèse de travail acceptée : traiter aussi `USER:` et `USB1:` comme sources Song comme pour Style, sans consacrer de campagne de validation séparée tant qu'aucune contradiction n'apparaît.

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
| Chemin / nom / source | `06 00 00 01 | 00` | GET VALIDÉ — PRESET, USER, USB1 observés |
| Volume global | `0C 00 00 01 | 51` | VALIDÉE |
| Mute 8 parties | `F0 43 73 01 51 05 00 00 08 ... F7` | VALIDÉE |
| Start / Stop | `06 00 03 01 | 00` | VALIDÉE |
| Sync Start | `06 00 07 01 | 00` | VALIDÉE GET/SET — `00=OFF`, `01=ON` |
| Intro 1/2/3 | Section Control `00/01/02` | VALIDÉE |
| Main A/B/C/D | Section Control `08..0B` | VALIDÉE |
| Fill A/B/C/D | Section Control `10..13` | VALIDÉE |
| Break | Section Control `18` | VALIDÉE |
| Ending 1/2/3 | Section Control `20..22` | VALIDÉE |

Exemples de chemin Style réellement observés :

```text
PRESET:/STYLE/Pop&Rock/Pop/Cool 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/80s 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/Up-tempo 8Beat.T308.prs
USER:/STYLE/80sMajestyRock.T548.prs
USB1:/training.T310.sty
```

La propriété `06 00 00 01 | 00` peut servir directement à l'accessibilité pour annoncer le nom et la source du Style.

Section Control :

```text
F0 43 7E 00 ss 7F F7
```

### Style — fonctions recherchées mais non résolues

| Fonction | Statut | Zones déjà testées |
|---|---|---|
| ACMP | NON RÉSOLUE | plusieurs zones CSP `06`, dont tous indexes sur `06 00 00..7F 01` |
| Auto Fill In | NON RÉSOLUE | `06 00..0F 00..7F 01 | 00` |
| Synchro Stop | NON RÉSOLUE | même zone, test effectué en mode Fingered |
| OTS Link | NON RÉSOLUE | `06 00..0F 00..7F 01 | 00` |

Détails ACMP déjà testés :

```text
06 00..0F 00..7F 01 | index 00       -> 0 changement
wide 00..0F/00..03/00..1F | index 00 -> 0 changement
06 00 00..7F 01 | index 00..7F       -> 0 changement
```

Ne pas répéter ces scans à l'identique.

Sync Start ne doit pas être confondu avec ACMP : un SET Sync Start ON n'active pas ACMP.

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

Le Fingering Type est présent dans les données Registration lorsque la catégorie Style est mémorisée, mais sa commande MIDI directe reste non résolue.

## Split Point / Fingering Type

Style Split Point VALIDÉ :

```text
F0 43 73 01 51 00 00 00 03 10 00 dd F7
```

Left Split Point VALIDÉ :

```text
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

`10 02` testé comme Fingering direct : **négatif**. Ne pas retester comme commande directe.

Valeurs de stockage `.rgt/.ssu` :

```text
03 AI Fingered
04 Fingered
0C AI Full Keyboard
```

Commande MIDI Fingering directe : **NON RÉSOLUE**.

### Campagnes Fingering terminées

Deep Weekend CSP GET-only :

```text
Blocs             : 1024/1024
Clés uniques      : 13 074 432
GET A+B           : 26 148 864
Candidats A/B     : 6
Confirmés A/B/A/B : 0
Exact 0C/03       : 0
```

Autres espaces épuisés :

```text
CSP EVENTS : 26 624 propriétés, 63 abonnements, aucun signal exploitable
XG         : 9 137 adresses, 1 936 réponses, aucun candidat reproductible
Sniff      : aucun SysEx Split/Fingering exploitable
Special Operator : ignoré
```

Ne pas répéter ces campagnes sans nouvelle hypothèse.

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
- Sniff ACMP pendant Style : aucune trame ACMP identifiable.
- Special Operator Fingering historique : ignoré par CVP-905.

Ne pas répéter ces campagnes sans nouvelle hypothèse.

## Règle `0x31`

Toute lecture `0x31` apparue après un SET supposé bool/u7 doit être considérée comme un **signal d'arrêt** et non comme une valeur valide.

## Règle de recherche

- scan large inconnu : GET-only ;
- jamais de brute-force SET ;
- SET ciblé uniquement après preuve suffisante ;
- restaurer l'état après validation ;
- consulter ce catalogue et le checkpoint RC4 avant de relancer un espace déjà testé.
