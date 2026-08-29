# CVP-905 — checkpoint protocole RC4

État consolidé au **28 août 2026**.

Testé sur Yamaha **CVP-905 firmware 1.03** via MIDI DIN Prodipe.

Ce fichier est le checkpoint protocole actif. `CVP905_PROTOCOL_CHECKPOINT_RC3.md` reste historique ; en cas de contradiction, **RC4 prime**.

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

## Section Control — validé matériellement

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

## Registration Memory — rappel externe validé

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

`XX = 00..07` pour Registration 1..8.

Notification observée :

```text
F0 43 73 01 52 25 00 01 01 00 01 XX F7
```

`XX` est zéro-based.

## Style — propriétés CSP validées

### Chemin / nom du Style

Propriété :

```text
06 00 00 01 | 00
```

GET validé matériellement.

Valeurs observées :

```text
PRESET:/STYLE/Pop&Rock/Pop/Cool 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/80s 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/Up-tempo 8Beat.T308.prs
USER:/STYLE/80sMajestyRock.T548.prs
USB1:/training.T310.sty
```

La propriété expose donc le chemin complet, ce qui permet d'extraire le nom, la source et éventuellement la catégorie.

### Style Start / Stop

```text
06 00 03 01 | 00
```

Commande déjà validée matériellement.

### Sync Start

```text
06 00 07 01 | 00
```

Valeurs :

```text
00 = OFF
01 = ON
```

Validation :

- différentiel GET OFF/ON reproductible ;
- SET ciblé validé ;
- blink ON/OFF visible physiquement sur le panneau du CVP.

Test d'indépendance avec ACMP :

1. Sync Start passe OFF ;
2. ACMP est coupé manuellement ;
3. Sync Start repasse ON par MIDI ;
4. ACMP reste OFF.

Conclusion : **Sync Start et ACMP sont indépendants**.

## Style — recherches négatives à ne pas répéter

### ACMP

Comparaisons OFF -> ON :

```text
06 00..0F 00..7F 01 | index 00       -> 0 changement
wide 00..0F/00..03/00..1F | index 00 -> 0 changement
06 00 00..7F 01 | index 00..7F       -> 0 changement
```

Le dernier espace correspond à :

```text
128 propriétés x 128 indexes = 16 384 GET
```

Conclusion limitée : aucune propriété GET classique ACMP n'a été trouvée dans ces zones.

Ne pas refaire ces scans à l'identique.

### Auto Fill In

Zone :

```text
06 00..0F 00..7F 01 | index 00
```

Résultat :

```text
0 changement
```

### Synchro Stop

Le CVP a été placé en mode **Fingered**, condition nécessaire pour rendre Synchro Stop disponible.

Zone :

```text
06 00..0F 00..7F 01 | index 00
```

Résultat :

```text
0 changement
```

### OTS Link

Zone :

```text
06 00..0F 00..7F 01 | index 00
```

Résultat :

```text
0 changement
```

Conclusion : Auto Fill In, Synchro Stop et OTS Link restent **NON RÉSOLUS**. Ne pas refaire ces scans à l'identique.

### Sniff ACMP MIDI OUT

Test : Style en lecture et plusieurs bascules ACMP ON/OFF.

Trafic observé principalement :

```text
98 ...
99 ...
B8 ...
B9 ...
BA ...
...
BE ...
```

Une trame SysEx de tempo Style a également été observée :

```text
F0 43 7E 01 00 24 4F 40 F7
```

Aucune trame spécifique ACMP identifiable n'a été observée.

Ce résultat n'exclut pas une commande write-only, interne ou non retransmise sur MIDI OUT.

## Split Point — famille Yamaha 51

Style Split Point validé :

```text
F0 43 73 01 51 00 00 00 03 10 00 dd F7
```

Left Split Point validé séparément :

```text
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

Le codage exact de la note `dd` reste à documenter proprement.

Candidat testé pour Fingering :

```text
F0 43 73 01 51 00 00 00 03 10 02 dd F7
```

Résultat : **aucun changement de Fingering Type**. Ne pas retester `10 02` comme commande directe.

## Fingering Type — stockage `.rgt` / `.ssu`

Valeurs confirmées :

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Dans le bloc `GPm` étudié :

```text
Style Split | Left Split | Fingering Type
```

Exemple :

```text
... 36 37 03 ...
```

La présence dans `.rgt` / `.ssu` ne donne pas directement l'adresse MIDI.

Registration Memory sauvegarde le Fingering Type lorsque la catégorie Style est incluse dans la mémorisation.

## CSP EVENTS — résultat Fingering

Abonnement :

```text
HEADER + 02 00 + Property-ID + F7
```

Ack observé :

```text
HEADER + 02 01 + Property-ID ...
```

Tempo, Transpose, Guide, Song Play, Active et Volume ont produit des comportements EVENTS exploitables.

Scan EVENTS Fingering large :

```text
26 624 propriétés testées
63 abonnements acceptés
```

Le rappel Registration n'a produit aucun INFO spontané permettant d'identifier le Fingering Type.

Conclusion : un rappel Registration n'est pas un trigger EVENTS fiable pour cette recherche.

**Ne pas répéter cette campagne sans nouvelle hypothèse.**

## XG Parameter Request — résultat Fingering

Format validé :

```text
F0 43 3n 4C hh mm ll F7
```

Contrôle : Master Volume `00 00 04` répond correctement.

Scan des zones XG documentées :

```text
9 137 adresses testées
1 936 adresses répondantes
aucun candidat Fingering reproductible
aucun exact 0C -> 03
```

**Ne pas répéter ce scan.**

## Sniff passif du panneau — Fingering/Split

Les changements manuels de Split/Fingering ne sont pas retransmis sous forme de SysEx Yamaha exploitable sur MIDI OUT.

Même des changements de Split connus ne sont pas renvoyés de façon exploitable.

Cette piste est considérée épuisée.

## Ancien Special Operator Fingering

Commande historique testée :

```text
F0 43 73 01 11 00 40 dd F7
```

Ignorée par le CVP-905.

**Ne pas retester.**

## Song — chemin / nom

Propriété :

```text
04 00 01 01 | 00
```

Observations matérielles :

- sans Song : réponse `EMPTY` ;
- avec Song : réponse `DATA` ;
- avec le Song **Shallow**, le chemin complet a été décodé.

Valeur observée :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

Exemple de payload brut :

```text
00 50 52 45 53 45 54 3A
00 2F 53 4F 4E 47 2F 36
00 30 20 50 6F 70 75 6C
00 61 72 2F 50 6F 70 2F
00 53 68 61 6C 6C 6F 77
00 2E 53 30 30 30 2E 6D
00 69 64
```

Décodage :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

Conclusion : le format observé est un empaquetage Yamaha par groupes de 8 octets :

```text
[masque des bits hauts] [jusqu'à 7 octets de caractères]
```

Les chaînes ASCII testées ont un masque `00`.

L'ancienne hypothèse « deux premiers octets = longueur 14-bit » est fausse pour ces réponses.

Le GET est validé ; le décodeur actuel de `cvp_song.py` doit être corrigé.

Hypothèse de travail du projet, acceptée pour gagner du temps : appliquer aussi aux Songs les préfixes `PRESET:`, `USER:` et `USB1:` observés sur les Styles. Seul `PRESET:` a été physiquement observé sur un Song à ce jour.

## Campagne Fingering Deep Weekend — résultat final

La campagne massive GET-only est **terminée**.

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

Conclusion :

**Aucune propriété CSP GET de l'espace exploré ne reflète de façon reproductible le changement AI Full Keyboard <-> AI Fingered.**

Ne pas relancer cette campagne sans nouvelle hypothèse.

Scanner final utilisé localement :

```text
docs/cvp_find_fingering_deep_weekend.py
```

Artefacts locaux :

```text
fingering_deep_weekend.sqlite3
fingering_deep_weekend_report.json
```

Ces gros artefacts restent locaux et ne sont pas une source de vérité GitHub.

## Synthèse des zones Fingering épuisées

```text
CSP Deep Weekend   -> négatif
CSP EVENTS         -> négatif
XG documenté       -> négatif
Sniff passif       -> négatif
51 / 10 02         -> négatif comme commande directe
Special Operator   -> ignoré
```

Cela ne prouve pas l'absence d'une commande Fingering. Les pistes restantes sont notamment :

```text
structure .rgt/.ssu
rappel Registration
famille 51 sous une nouvelle hypothèse
commande write-only
protocole interne
```

## Règles pour les prochaines recherches

- Ne pas refaire les scans XG, EVENTS, Deep Weekend, passive sniff ou Special Operator listés ci-dessus sans nouvelle hypothèse.
- Ne pas refaire les scans ACMP/Auto Fill/Synchro Stop/OTS Link des zones `06` déjà documentées.
- Ne pas utiliser un vieux script expérimental comme preuve ; consulter ce checkpoint et `docs/FUNCTION_CATALOG.md`.
- Scan large inconnu : **GET-only**.
- Pour un SET inconnu : test ciblé et restaurable uniquement, jamais brute force.
- Validation SET ciblée : `GET -> SET -> GET -> restauration -> GET`.
- Toute valeur anormale `0x31` après un SET supposé bool/u7 est un signal d'arrêt.
- Arrêter `cvp-access.service` et libérer `amidi` avant les probes bruts.
