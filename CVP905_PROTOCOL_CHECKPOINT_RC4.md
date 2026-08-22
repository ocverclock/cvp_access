# CVP-905 — checkpoint protocole RC4

État consolidé au **22 août 2026**.

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

Résultat : **aucun changement de Fingering Type**. Ne pas retester comme commande directe.

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

## CSP EVENTS — résultat

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

Le rappel Registration n'a produit aucun INFO spontané permettant d'identifier le Fingering Type. Un rappel Registration n'est donc **pas** un trigger EVENTS fiable pour cette recherche.

## XG Parameter Request — résultat

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

Ne pas répéter ce scan.

## Sniff passif du panneau — abandonné

Les changements manuels de Split/Fingering ne sont pas retransmis sous forme de SysEx Yamaha exploitable sur MIDI OUT. Même des changements de Split connus ne sont pas renvoyés.

Cette piste est considérée épuisée.

## Ancien Special Operator Fingering

Commande historique testée :

```text
F0 43 73 01 11 00 40 dd F7
```

Ignorée par le CVP-905. Ne pas retester.

## Song Name — GET brut validé, décodage à corriger

Propriété :

```text
04 00 01 01 | 00
```

Observations matérielles :

- sans Song : réponse `EMPTY` ;
- avec Song : réponse `DATA` ;
- la propriété est donc utile pour la détection de Song chargé.

**Attention :** le décodeur texte actuel de `cvp_song.py` suppose encore une longueur 14-bit en tête. Les observations modèle/firmware montrent plutôt un encodage Yamaha par groupes de 7 caractères précédés d'un masque. Le GET est validé, mais le décodage texte doit être revalidé avant de considérer le nom lisible comme fiable.

## Campagne Fingering large — V2 SQLite

Scanner actif :

```text
docs/cvp_find_fingering_indexes_20_7f_v2.py
```

Espace :

```text
Property-ID : 00..0F / 00..0F / 00..7F / 01
Indexes     : 20..7F
256 blocs
12 288 GET par bloc
```

Comparaison automatique :

```text
A  = REG5 / AI Full Keyboard
B1 = REG6 / AI Fingered
A2 = REG5
B2 = REG6
```

Le résultat exact recherché reçoit un drapeau spécial :

```text
0C -> 03
```

### Migration V1 -> V2 du 22 août 2026

La V1 stockait tout le baseline dans un JSON géant. Sur Raspberry 1 Go :

```text
fingering_idx20_7f_report.json : ~137 MiB
Python avant OOM                : ~710 MiB RSS
arrêt noyau                     : code 137 / OOM killer
```

Migration streaming V2 :

```text
1 951 899 réponses baseline récupérées
159 blocs valides repris
4 blocs legacy sans réponse rejetés :
09:0F, 0A:00, 0A:01, 0A:02
```

Ces quatre blocs sont automatiquement rescannés.

Premières mesures V2 :

```text
RSS max : ~27-28 MiB
bloc    : ~1,3 min
```

La campagne tourne sous `cvp-fingering-scan.service` avec reprise automatique après crash/reboot et conflit explicite avec `cvp-access.service`.

**Résultat final Fingering : encore en attente.** Ne conclure ni positif ni négatif avant la fin A/B/A/B.

## Règles pour les prochaines recherches

- Ne pas refaire les scans XG, EVENTS, passive sniff ou Special Operator listés ci-dessus.
- Ne pas utiliser un vieux script expérimental comme preuve ; consulter ce checkpoint et `docs/FUNCTION_CATALOG.md`.
- Pour un SET inconnu : test ciblé et restaurable uniquement, jamais brute force.
