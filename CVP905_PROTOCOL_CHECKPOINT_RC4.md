# CVP-905 — checkpoint protocole RC4

Teste sur Yamaha CVP-905 firmware 1.03.

## Section Control valide

```text
F0 43 7E 00 ss 7F F7

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

## Registration Recall valide

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

XX=00..07 correspond a Registration 1..8.

## Split Point famille 51

Style Split Point :

```text
F0 43 73 01 51 00 00 00 03 10 00 dd F7
```

Left Split Point :

```text
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

Le candidat 10 02 pour Fingering Type n'a produit aucun effet.

## Fingering Type dans .rgt / .ssu

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Dans GPm : Style Split | Left Split | Fingering Type.
L'ordre de stockage .rgt ne se transpose pas directement en adresses MIDI 51.

## CSP EVENTS / XG

EVENTS est valide sur CVP-905 et le XG Parameter Request fonctionne.
Les campagnes EVENTS et XG standard n'ont pas donne de candidat Fingering reproductible.

## Sniff panneau

Les changements manuels Split/Fingering ne sont pas retransmis en SysEx exploitable sur MIDI OUT.

## Recherche en cours

Scan GET read-only :

```text
Property : 00..0F / 00..0F / 00..7F / 01
Index    : 20..7F
```

Aucun SET CSP inconnu.
