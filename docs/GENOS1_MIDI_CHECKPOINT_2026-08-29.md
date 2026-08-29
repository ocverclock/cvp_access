# Genos 1 — checkpoint MIDI du 29 août 2026

Ce document consolide les essais matériels réalisés sur un **Yamaha Genos 1** relié au Raspberry Pi par MIDI DIN Prodipe.

Objectif : identifier des mécanismes MIDI Yamaha utiles, puis tester séparément les candidats intéressants sur le CVP-905.

## Règle fondamentale

> Un résultat Genos n'est jamais considéré comme validé sur CVP-905 sans test matériel CVP séparé.

## Statuts

- **VALIDÉ** : comportement matériel reproduit sur Genos.
- **GET VALIDÉ** : lecture confirmée.
- **SET VALIDÉ** : écriture confirmée physiquement et/ou par relecture.
- **PARTIEL** : mécanisme confirmé mais données encore incomplètes.
- **NÉGATIF** : piste testée sans résultat exploitable.
- **NON RÉSOLU** : mécanisme encore recherché.

# 1. Liaison SysEx — VALIDÉ

Réglages utilisés sur Genos :

```text
Menu -> MIDI -> System

System Exclusive Message Receive  = On
System Exclusive Message Transmit = On
Clock = Internal
```

## Universal Device Inquiry

TX :

```text
F0 7E 7F 06 01 F7
```

RX :

```text
F0 7E 7F 06 02 43 00 44 42 1C 0B 00 00 01 F7
```

## XG Parameter Request — Master Volume

TX :

```text
F0 43 30 4C 00 00 04 F7
```

RX :

```text
F0 43 10 4C 00 00 04 7F F7
```

Conclusion :

```text
SysEx bidirectionnel : VALIDÉ
XG Parameter Request : VALIDÉ
```

# 2. CSP moderne CVP sur Genos — NÉGATIF

Header CVP testé :

```text
F0 43 73 01 52 25 26
```

GET testés :

```text
Style path  06 00 00 01
Song path   04 00 01 01
Voice path  02 00 00 01
Voice MIDI  02 00 01 01
```

Résultat :

```text
aucune réponse CSP
```

La liaison SysEx étant confirmée par XG et Device Inquiry, cette absence de réponse n'est pas attribuée au câblage.

Conclusion :

> Ne pas utiliser le CSP moderne CVP comme protocole de lecture Genos 1.

# 3. Voice — lecture XG VALIDÉE

Yamaha XG Multi Part :

```text
08 nn 01 = Bank Select MSB
08 nn 02 = Bank Select LSB
08 nn 03 = Program Number
```

GET :

```text
F0 43 30 4C 08 nn pp F7
```

Réponse :

```text
F0 43 10 4C 08 nn pp dd F7
```

Le Program Number est encodé `0..127` dans la trame. Les listes Yamaha l'affichent classiquement `1..128`.

## Mapping des parties clavier — VALIDÉ par différentiel

Résultat :

```text
Right1 -> 08 01
Right2 -> 08 02
Right3 -> 08 03
Left   -> 08 04
```

### Right1

Différentiel :

```text
A : MSB=104 (68), LSB=21 (15), PC brut=00
B : MSB=8   (08), LSB=66 (42), PC brut=41
```

### Right2

```text
08 02
avant : (8, 47, 49)
après : (8, 65, 48)
```

### Right3

```text
08 03
avant : (8, 49, 1)
après : (104, 25, 21)
```

### Left

```text
08 04
avant : (8, 41, 20)
après : (8, 42, 55)
```

# 4. Voice — écriture XG VALIDÉE

SET :

```text
F0 43 10 4C 08 nn 01 MSB F7
F0 43 10 4C 08 nn 02 LSB F7
F0 43 10 4C 08 nn 03 PC  F7
```

## Right1

Restauration envoyée :

```text
F0 43 10 4C 08 01 01 68 F7
F0 43 10 4C 08 01 02 15 F7
F0 43 10 4C 08 01 03 00 F7
```

Relecture exacte :

```text
F0 43 10 4C 08 01 01 68 F7
F0 43 10 4C 08 01 02 15 F7
F0 43 10 4C 08 01 03 00 F7
```

## Right2 / Right3 / Left

Valeurs restaurées :

```text
Right2  08 02 : 08 2F 31
Right3  08 03 : 08 31 01
Left    08 04 : 08 29 14
```

Relectures exactes :

```text
F0 43 10 4C 08 02 01 08 F7
F0 43 10 4C 08 02 02 2F F7
F0 43 10 4C 08 02 03 31 F7

F0 43 10 4C 08 03 01 08 F7
F0 43 10 4C 08 03 02 31 F7
F0 43 10 4C 08 03 03 01 F7

F0 43 10 4C 08 04 01 08 F7
F0 43 10 4C 08 04 02 29 F7
F0 43 10 4C 08 04 03 14 F7
```

Conclusion :

```text
Right1 Voice GET/SET : VALIDÉ
Right2 Voice GET/SET : VALIDÉ
Right3 Voice GET/SET : VALIDÉ
Left Voice GET/SET   : VALIDÉ
```

## Noms confirmés via Data List

```text
Right1  104/21/1  -> CFX ConcertGrand
Right2    8/47/50 -> KinoStrings
Right3    8/49/2  -> SteelAcousticFinger
Left      8/41/21 -> 70sSuitcaseClean
```

# 5. Style — sniff d'un changement manuel

Une capture d'un changement de Style au panneau a produit plusieurs SysEx, par exemple :

```text
F0 43 10 4C 03 14 ...
F0 43 10 4C 03 17 ...
F0 43 10 4C 02 01 ...
F0 43 7E 01 ...
F0 43 10 4C 30 ...
```

Un différentiel Style A / Style B a isolé notamment :

```text
Adresse 02 01 20
A : 41 00
B : 41 05

Adresse 03 17 00
A : 40 00
B : 53 29

Adresse 03 18 00
A : 40 00
B : 01 00

Adresse 03 1B 00
A : 53 11
B : 40 00
```

Interprétation documentée :

```text
02 01 20   = type de Chorus
03 xx ...  = paramètres / types d'Insertion Effects
43 7E 01...= Tempo Control
```

Conclusion :

> Le changement manuel de Style émet des paramètres associés au Style, mais la capture n'a pas montré directement son `Style No.`.

Ne pas utiliser ces paramètres comme identifiant de Style.

# 6. Style — sélection MIDI directe VALIDÉE

Commande :

```text
F0 43 73 01 51 05 00 03 04 00 00 HH LL F7
```

`HH LL` encode le **Style Number** sur deux octets 7-bit :

```text
HH = StyleNumber // 128
LL = StyleNumber % 128
```

## Validations matérielles

### Party Polka

```text
HH LL = 00 00
```

Résultat :

```text
Party Polka
```

### Viennese Waltz

```text
HH LL = 10 11
```

Résultat :

```text
Viennese Waltz
```

### AcousticBlues

StyleNumber connu :

```text
3697
```

Conversion :

```text
3697 // 128 = 28  = 0x1C
3697 % 128  = 113 = 0x71
```

Commande :

```text
F0 43 73 01 51 05 00 03 04 00 00 1C 71 F7
```

Résultat physique :

```text
AcousticBlues
```

Conclusion :

> La sélection directe de Style par MIDI est VALIDÉE sur Genos 1.

# 7. Table Style Name -> Style Number

Le format MIDI est résolu.

La table complète `nom -> StyleNumber` n'est pas encore consolidée dans le projet.

Des données tierces comme celles utilisées par **MixMaster** contiennent des numéros internes utiles, mais elles doivent être considérées comme données auxiliaires jusqu'à validation des entrées employées.

# 8. Lecture de l'identité du Style courant — NON RÉSOLUE

État actuel :

```text
Style sélection directe / WRITE : VALIDÉ
Style identité courante / READ  : NON RÉSOLU
```

Aucune requête XG `4C` équivalente à la lecture Voice n'a été validée pour le Style Number.

Le Style Number appartient à une autre famille Yamaha :

```text
43 73 01 51 05 00 03 04 ...
```

Piste autorisée :

> Chercher un mécanisme GET ciblé autour du bloc `51 05 00 03`, sans brute-force SET.

# 9. External Controller — VALIDÉ partiellement

Configuration Genos, canal 16 :

```text
CC#0 -> Style Start/Stop
BF 00 7F
BF 00 00
```

Validé physiquement.

```text
CC#5 -> Fingered/Fingered On Bass
BF 05 7F
BF 05 00
```

Validé physiquement.

Valeurs internes External Controller trouvées dans `.msu` :

```text
0x17 = Sync Stop
0x27 = Fingered/Fingered On Bass
```

# 10. Assignable / `.ssu`

Différentiel système :

```text
0x28 = Fingered
0x8E = ACMP
```

Une hypothèse de translation simple a proposé :

```text
External Controller ACMP = 0x8D
```

Test :

- `.msu` modifié avec `0x8D` : rejeté par le Genos ;
- fichier contrôle modifié avec une valeur External Controller connue (`0x14` Style Start/Stop) : accepté.

Conclusion :

> Les tables Assignable et External Controller ne suivent pas une simple translation numérique.

ACMP n'est pas exposé dans External Controller Genos 1.

Cette piste est fermée.

# 11. Résumé

```text
Genos SysEx bidirectionnel          VALIDÉ
XG Parameter Request                VALIDÉ
CSP moderne CVP sur Genos          NÉGATIF

Voice Right1 GET/SET               VALIDÉ
Voice Right2 GET/SET               VALIDÉ
Voice Right3 GET/SET               VALIDÉ
Voice Left GET/SET                 VALIDÉ

Style direct SELECT/WRITE          VALIDÉ
Style current identity READ        NON RÉSOLU

External Controller Start/Stop     VALIDÉ
External Controller Fingering      VALIDÉ
External Controller ACMP           NON DISPONIBLE / piste fermée
```

# 12. Étapes suivantes

1. Tester le GET Voice XG sur CVP-905.
2. Si GET Voice répond sur CVP, identifier les mappings Main/Layer/Left.
3. Tester ensuite le SET Voice de façon restaurable sur CVP.
4. Tester la commande Style select `51 05 00 03 04` sur CVP avec une valeur connue.
5. Continuer sur Genos la recherche ciblée d'un GET du Style courant.
6. Ne pas extrapoler les adresses Genos au CVP sans validation.
