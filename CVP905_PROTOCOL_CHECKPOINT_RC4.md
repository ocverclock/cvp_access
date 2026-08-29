# CVP-905 — checkpoint protocole RC4

État consolidé au **29 août 2026**.

Testé sur Yamaha **CVP-905 firmware 1.03** via MIDI DIN Prodipe.

Ce fichier est le checkpoint protocole actif. `CVP905_PROTOCOL_CHECKPOINT_RC3.md` reste historique ; en cas de contradiction, **RC4 prime**.

## Convention de statut

- **VALIDÉ** : test matériel reproductible sur CVP-905.
- **GET VALIDÉ** : lecture confirmée, écriture non revendiquée.
- **NON RÉSOLU** : mécanisme encore recherché.
- **CLÔTURÉ DIRECT** : recherche de commande MIDI directe arrêtée pour le projet actuel.
- **NÉGATIF** : espace/méthode testé sans candidat exploitable.
- **GENOS UNIQUEMENT** : ne pas considérer comme preuve CVP.

## CSP moderne

Header :

```text
F0 43 73 01 52 25 26
```

Actions observées :

```text
GET    01 00
SET    01 01
INFO   00 00
EVENTS 02 00
```

Format SET u7 simple utilisé par le runtime :

```text
HEADER
01 01
Property-ID (4 octets)
index
01 00
00 01
value
F7
```

## Section Control — VALIDÉ

Format :

```text
F0 43 7E 00 ss 7F F7
```

Valeurs confirmées :

```text
00 Intro 1
01 Intro 2
02 Intro 3

08 Main A
09 Main B
0A Main C
0B Main D

10 Fill A
11 Fill B
12 Fill C
13 Fill D

18 Break

20 Ending 1
21 Ending 2
22 Ending 3
```

## Registration Memory — rappel externe VALIDÉ

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

`XX=00..07` pour Registration 1..8.

Notification observée :

```text
F0 43 73 01 52 25 00 01 01 00 01 XX F7
```

## Style — propriétés CSP VALIDÉES

### Chemin / nom du Style — GET VALIDÉ

```text
06 00 00 01 | 00
```

Valeurs observées :

```text
PRESET:/STYLE/Pop&Rock/Pop/Cool 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/80s 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/Up-tempo 8Beat.T308.prs
USER:/STYLE/80sMajestyRock.T548.prs
USB1:/training.T310.sty
```

### Style Start / Stop — VALIDÉ

```text
06 00 03 01 | 00
```

### Sync Start — VALIDÉ GET/SET

```text
06 00 07 01 | 00

00 = OFF
01 = ON
```

Différentiel GET reproductible et SET ciblé validé physiquement.

Sync Start et ACMP sont indépendants : réactiver Sync Start par MIDI ne réactive pas ACMP.

### Mute des 8 parties Style — VALIDÉ

```text
F0 43 73 01 51 05 00 00 08
Rhy1 Rhy2 Bass Chd1 Chd2 Pad Phr1 Phr2
F7
```

```text
00 = OFF
01 = ON
```

## Split Point — famille Yamaha 51

Style Split Point VALIDÉ :

```text
F0 43 73 01 51 00 00 00 03 10 00 dd F7
```

Left Split Point VALIDÉ :

```text
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

Le codage exact de la note `dd` reste à documenter proprement.

Candidat Fingering direct :

```text
F0 43 73 01 51 00 00 00 03 10 02 dd F7
```

Résultat : **NÉGATIF**. Aucun changement de Fingering Type. Ne pas retester `10 02` comme commande Fingering.

## ACMP — recherche directe CLÔTURÉE

### Scans CSP négatifs

OFF -> ON :

```text
06 00..0F 00..7F 01 | index 00       -> 0 changement
wide 00..0F/00..03/00..1F | index 00 -> 0 changement
06 00 00..7F 01 | index 00..7F       -> 0 changement
```

Le dernier espace correspond à :

```text
128 propriétés x 128 indexes = 16 384 GET
```

### Sniff MIDI OUT ACMP — NÉGATIF

Style en lecture et plusieurs bascules ACMP ON/OFF.

Trafic principalement :

```text
98 ...
99 ...
B8 ...
B9 ...
...
BE ...
```

Une trame tempo Style a été observée :

```text
F0 43 7E 01 00 24 4F 40 F7
```

Aucune trame spécifique ACMP identifiable.

### Stockage Registration ACMP — VALIDÉ

Dans `.rgt` :

```text
GPm07 payload[2]

00 = ACMP OFF
7F = ACMP ON
```

Un Registration minimal avec deux mémoires identiques sauf ACMP a restauré correctement ON/OFF sans changement parasite de Style, Fingering ou Voice.

La documentation CVP consultée indique ACMP ON/OFF comme fonction de panneau.

### Décision

**ACMP direct = CLÔTURÉ pour la recherche actuelle.**

Workaround retenu : **Registration Memory**.

Ne rouvrir cette recherche qu'avec une nouvelle preuve de protocole.

## Auto Fill In — CLÔTURÉ DIRECT

Zone testée :

```text
06 00..0F 00..7F 01 | 00
```

Résultat :

```text
0 changement
```

La documentation CVP consultée indique cette fonction comme commande de panneau.

Ne pas refaire ce scan à l'identique.

## Synchro Stop — CLÔTURÉ DIRECT

Le CVP a été placé en **Fingered** avant le test.

Zone :

```text
06 00..0F 00..7F 01 | 00
```

Résultat :

```text
0 changement
```

La documentation CVP consultée indique cette fonction comme commande de panneau.

Ne pas refaire ce scan à l'identique.

## OTS Link — NON RÉSOLU

Zone déjà testée :

```text
06 00..0F 00..7F 01 | 00
```

Résultat :

```text
0 changement
```

Ne pas refaire ce scan à l'identique. Une autre famille/propriété reste possible.

## Fingering Type — stockage Registration VALIDÉ

Dans `.rgt` :

```text
GPm07 payload[8]

03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Le rappel Registration restaure le Fingering Type si la catégorie Style est incluse.

## Parties Style — stockage Registration VALIDÉ

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

## Fingering Type — campagnes directes terminées

### CSP EVENTS — NÉGATIF

Abonnement :

```text
HEADER + 02 00 + Property-ID + F7
```

Ack observé :

```text
HEADER + 02 01 + Property-ID ...
```

Plusieurs propriétés connues fonctionnent avec EVENTS, mais le Fingering n'a donné aucun signal exploitable.

Campagne :

```text
26 624 propriétés testées
63 abonnements acceptés
```

### XG Parameter Request — NÉGATIF pour Fingering

Format validé :

```text
F0 43 3n 4C hh mm ll F7
```

Contrôle Master Volume répond correctement.

Scan :

```text
9 137 adresses testées
1 936 adresses répondantes
aucun candidat Fingering reproductible
aucun exact 0C -> 03
```

### Sniff passif — NÉGATIF

Les changements manuels de Fingering/Split n'ont pas produit de SysEx exploitable permettant de retrouver le Fingering.

### Special Operator historique — NÉGATIF

```text
F0 43 73 01 11 00 40 dd F7
```

Ignoré par le CVP-905.

### Deep Weekend — TERMINÉ / NÉGATIF

États :

```text
A  = REG5 / AI Full Keyboard
B1 = REG6 / AI Fingered
A2 = REG5
B2 = REG6
```

Résultat final :

```text
Blocs             : 1024/1024
Clés uniques      : 13 074 432
GET A+B           : 26 148 864
Candidats A/B     : 6
Confirmés A/B/A   : 1
Confirmés A/B/A/B : 0
Miroirs           : 0
Stables non-miroir: 0
Exact 0C/03       : 0
```

### Décision

**Fingering direct = CLÔTURÉ pour la recherche actuelle.**

Workaround retenu : **Registration Memory**.

Ne pas relancer CSP Deep Weekend, EVENTS, XG, sniff ou Special Operator sans nouvelle preuve indépendante.

## Song — chemin / nom — GET VALIDÉ

```text
04 00 01 01 | 00
```

Observations :

- sans Song : `EMPTY`;
- avec Song : `DATA`;
- exemple décodé :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

Payload observé :

```text
00 50 52 45 53 45 54 3A
00 2F 53 4F 4E 47 2F 36
00 30 20 50 6F 70 75 6C
00 61 72 2F 50 6F 70 2F
00 53 68 61 6C 6C 6F 77
00 2E 53 30 30 30 2E 6D
00 69 64
```

Décodage Yamaha observé :

```text
[masque des bits hauts] [jusqu'à 7 octets de données]
```

L'ancienne hypothèse « deux premiers octets = longueur 14-bit » est fausse.

`cvp_song.py` doit être corrigé.

## Autres propriétés CVP validées

### Song

```text
04 00 05 01 | 00 = Play/Pause/Stop
04 00 0A 01 | 00 = Position
04 00 1B 01 | 00 = Longueur GET
04 00 0D 01 | 00 = Boucle A/B GET/SET
04 01 00 01 | 10..1F = présence pistes GET
04 00 0E 01 | 00..02 = parties pédagogiques GET/SET
04 00 10 01 | 00 = affectation auto GET/SET
```

### Mixer

```text
0C 00 01 01 = Active
0C 00 00 01 = Volume
0C 00 03 01 = Pan
0C 00 04 01 = Reverb send
```

### Voice CSP

```text
02 00 01 01 = Voice MIDI GET VALIDÉ dynamiquement
02 00 00 01 = Voice preset GET EMPTY sur CVP-905
```

### Tempo / Transpose

```text
08 00 00 01 | 00 = Tempo
0A 00 00 01 | 02 = Transpose
```

### Guide

```text
04 03 00 01 | 00 = Guide ON/OFF GET/SET
04 03 01 01 | 00 = Guide Type GET/SET
```

### Piano

```text
02 02 07 01 = Lid
02 02 03 01 = Environment
02 02 00 01 = VRM
02 02 01 01 = Damper Resonance
02 02 02 01 = String Resonance
```

### Stream Lights

```text
04 02 00 01 | 00 = ON/OFF GET/SET
```

## Signaux d'arrêt / non résolus

```text
Key-Off Sampling 02 02 06 01 = timeout
Brightness       0C 00 0B 01 = SET naïf -> 0x31
Touch Curve      00 00 00 01 = non résolu
Fixed Curve      00 00 01 01 = non résolu
Fixed Velocity   00 00 02 01 = non résolu
Master Tune      03 00 00 01 = non résolu
Stream Speed     04 02 02 01 = SET naïf -> 0x31
```

Toute valeur `0x31` apparue après un SET supposé bool/u7 est un **signal d'arrêt**, pas une valeur valide.

## Pont Genos 1 — GENOS UNIQUEMENT

Les recherches du 29 août sont séparées dans :

```text
docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md
```

Résultats à tester séparément sur CVP :

```text
Voice XG Right1/Right2/Right3/Left : GET + SET VALIDÉS Genos
Style select famille 51            : VALIDÉ Genos
Style identité courante GET        : NON RÉSOLU Genos
```

Ces résultats ne changent pas le statut CVP avant validation physique sur CVP-905.

## Règles pour les prochaines recherches

- ne pas refaire les scans ACMP/Fingering documentés ;
- ne pas utiliser un ancien script comme preuve ;
- scan large inconnu : **GET-only** ;
- jamais de brute-force SET ;
- SET ciblé seulement avec état restaurable ;
- validation : `GET -> SET -> GET -> restauration -> GET` ;
- valeur anormale `0x31` = arrêt ;
- arrêter `cvp-access.service` et libérer `amidi` avant les probes bruts.
