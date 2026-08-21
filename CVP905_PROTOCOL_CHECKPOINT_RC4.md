# CVP-905 — checkpoint protocole RC4

Testé sur Yamaha CVP-905 firmware 1.03.

Ce document complète `CVP905_PROTOCOL_CHECKPOINT_RC3.md`.

## Section Control — validé matériellement

Format :

```text
F0 43 7E 00 ss 7F F7
```

Valeurs `ss` confirmées sur CVP-905 :

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

Les commandes ont été testées une à une sur le CVP-905.

## Registration Memory — rappel externe validé

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

```text
00 Registration 1
01 Registration 2
02 Registration 3
03 Registration 4
04 Registration 5
05 Registration 6
06 Registration 7
07 Registration 8
```

Notification observée lors d’un changement / rappel de Registration :

```text
F0 43 73 01 52 25 00 01 01 00 01 XX F7
```

`XX` est zéro-based.

## Split Point — famille Yamaha 51

Style Split Point validé :

```text
F0 43 73 01 51 00 00 00 03 10 00 dd F7
```

L’adresse `10 00` agit sur le Style Split Point.

Left Split Point validé séparément :

```text
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

Les contraintes de l’interface Split/Fingering peuvent forcer les deux splits
à se déplacer ensemble selon le mode actif.

Le candidat suivant a été testé pour Fingering Type :

```text
F0 43 73 01 51 00 00 00 03 10 02 dd F7
```

Résultat : aucun changement observé.

## Fingering Type — stockage Registration / System Setup

Les fichiers `.rgt` et `.ssu` confirment le codage :

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Dans le bloc `GPm` étudié, l’ordre observé est :

```text
Style Split | Left Split | Fingering Type
```

Exemple :

```text
... 36 37 03 ...
```

L’ordre de stockage `.rgt` ne se transpose donc pas directement en identifiants
de commandes MIDI famille `51`.

Le contrôle MIDI direct du Fingering Type reste non résolu.

## CSP EVENTS — validé

Format utilisé :

```text
F0 43 73 01 52 25 26 02 00 PP PP PP PP F7
```

Le CVP-905 accepte l’abonnement EVENTS sur plusieurs propriétés connues.

Après abonnement sur Tempo, une modification manuelle a produit un `INFO`
spontané valide.

Le rappel d’une Registration n’a cependant pas généré d’INFO exploitable
permettant d’identifier Fingering Type.

## XG Parameter Request — validé

Format :

```text
F0 43 3n 4C hh mm ll F7
```

Test de contrôle validé :

```text
00 00 04 = Master Volume
```

Le scan des zones XG documentées a obtenu 1 936 adresses répondantes communes
entre les états testés, sans candidat reproductible pour Fingering Type.

## Sniff passif du panneau

Les changements manuels de Split Point / Fingering ne sont pas retransmis
sous forme de SysEx Yamaha exploitable sur MIDI OUT.

Cette piste est abandonnée.

## Recherche en cours

Scan GET read-only de l’espace CSP restant :

```text
Property-ID : 00..0F / 00..0F / 00..7F / 01
Indexes     : 20..7F
```

Comparaison automatique :

```text
REG5 AI Full Keyboard
-> REG6 AI Fingered
-> REG5
-> REG6
```

Aucun SET CSP inconnu n’est utilisé.
