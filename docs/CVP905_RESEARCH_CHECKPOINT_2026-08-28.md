# CVP-905 — checkpoint recherche du 28 août 2026

Matériel de référence : **Yamaha CVP-905 firmware 1.03**  
Interface : **MIDI DIN ProdipeMIDIlilo**  
Projet : **CVP Access**

Ce document fige les découvertes récentes et surtout les zones déjà explorées sans résultat afin d’éviter de relancer les mêmes recherches sans nouvelle hypothèse.

> Un résultat négatif signifie uniquement : « rien trouvé dans l’espace et avec la méthode décrits ».  
> Il n’exclut pas une autre famille SysEx, une commande write-only, une structure Registration/Style, un protocole interne ou un autre mécanisme Yamaha.

---

## 1. Fingering Type — campagne CSP Deep Weekend terminée

États comparés :

```text
A  = REG5 / AI Full Keyboard
B  = REG6 / AI Fingered
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
Miroirs 04/05/06  : 0
Stables non miroir: 0
Match exact 0C/03 : 0
```

Conclusion :

**Aucune propriété CSP GET de l’espace exploré ne reflète de façon reproductible le changement AI Full Keyboard <-> AI Fingered.**

Ne pas relancer le même scan CSP massif Fingering sans nouvelle hypothèse.

Valeurs de stockage confirmées dans `.rgt/.ssu` :

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

---

## 2. Fingering Type — autres pistes déjà épuisées

### CSP EVENTS

```text
26 624 propriétés testées
63 abonnements acceptés
```

Aucun INFO spontané exploitable lors du rappel REG5/REG6.

**Ne pas refaire cette campagne.**

### XG documenté

```text
9 137 adresses testées
1 936 répondantes
0 candidat Fingering reproductible
0 exact 0C -> 03
```

**Ne pas refaire cette campagne.**

### Sniff passif panneau

Les changements manuels de Split/Fingering n’ont pas produit de SysEx Yamaha exploitable sur MIDI OUT.

Même les changements de Split connus ne sont pas retransmis de façon exploitable.

**Piste abandonnée.**

### Famille Yamaha 51 — candidat direct déjà rejeté

Commande testée :

```text
F0 43 73 01 51 00 00 00 03 10 02 dd F7
```

Testée comme Fingering direct : aucun changement.

**Ne pas retester `10 02` comme commande directe Fingering.**

### Ancien Special Operator

```text
F0 43 73 01 11 00 40 dd F7
```

Ignoré par le CVP-905.

**Ne pas retester.**

---

## 3. Style — nouvelle commande validée : Sync Start

Différentiel GET répété OFF -> ON :

```text
06 00 07 01 | 00 : DATA:00 -> DATA:01
```

Valeurs :

```text
00 = OFF
01 = ON
```

Validation :

- différentiel GET OFF/ON reproductible ;
- SET ciblé ensuite testé ;
- alternance ON/OFF (« blink ») visible physiquement sur le bouton Sync Start du CVP.

Conclusion :

```text
06 00 07 01 | 00 = Sync Start
00 = OFF
01 = ON
```

**GET + SET validés matériellement.**

### Indépendance par rapport à ACMP

Pendant le blink Sync Start :

1. Sync Start passe OFF ;
2. ACMP est mis manuellement OFF ;
3. Sync Start repasse ON par MIDI ;
4. ACMP reste OFF.

Conclusion :

**Sync Start ne réarme pas ACMP. Les deux fonctions sont indépendantes.**

Commandes CSP `06` Style actuellement validées :

```text
06 00 03 01 | 00 = Style Start/Stop
06 00 07 01 | 00 = Sync Start
```

---

## 4. ACMP — zones testées sans résultat

### 4.1 Famille CSP 06, index 00

ACMP OFF -> ON :

```text
Property : 06 00..0F 00..7F 01
Index    : 00
```

Résultat :

```text
Changements détectés : 0
```

### 4.2 Scan CSP large, index 00

ACMP OFF -> ON, espace par défaut de `cvp_diff_scan_wide.py` :

```text
Premier octet : 00..0F
Deuxième      : 00..03
Troisième     : 00..1F
Index         : 00
```

Résultat :

```text
Changements détectés : 0
```

### 4.3 Famille CSP 06, tous indexes

ACMP OFF -> ON :

```text
Property     : 06 00 00..7F 01
Index        : 00..7F
Combinaisons : 16 384
```

Résultat :

```text
TOTAL CHANGEMENTS : 0
```

Conclusion :

**Aucune propriété GET classique ACMP n’a été trouvée dans ces zones.**

**Ne pas refaire ces scans ACMP à l’identique.**

Prochaine recherche ACMP : partir d’une autre hypothèse, par exemple :

- famille Yamaha `51` ;
- structure Registration / Style ;
- commande write-only ;
- autre protocole Yamaha ;
- mécanisme interne non retransmis sur MIDI OUT.

---

## 5. ACMP — sniff MIDI OUT

Test effectué pendant qu’un Style tournait, avec plusieurs bascules ACMP ON/OFF.

Trafic observé :

```text
98 ...
99 ...
B8 ...
B9 ...
BA ...
...
BE ...
```

Ce trafic correspond aux notes et contrôleurs MIDI des parties du Style.

SysEx observé :

```text
F0 43 7E 01 00 24 4F 40 F7
```

Cette trame correspond au contrôle de tempo du Style observé pendant le test.

Aucune trame spécifique ACMP identifiable n’a été observée lors des bascules ON/OFF.

Conclusion :

**Le test passif MIDI OUT n’a pas fourni de commande ACMP exploitable.**

Cela n’exclut pas une commande interne, write-only ou non retransmise sur MIDI OUT.

---

## 6. Autres fonctions Style — recherches CSP 06 négatives

Les fonctions suivantes ont été testées avec :

```text
Property : 06 00..0F 00..7F 01
Index    : 00
```

Méthode :

```text
état OFF -> baseline GET
état ON  -> comparaison GET
```

### Auto Fill In

```text
Changements détectés : 0
```

### Synchro Stop

Le CVP a été placé en mode **Fingered**, condition nécessaire pour rendre Synchro Stop disponible.

Résultat :

```text
Changements détectés : 0
```

### OTS Link

```text
Changements détectés : 0
```

Conclusion :

```text
Auto Fill In : aucune propriété trouvée dans cette zone
Synchro Stop : aucune propriété trouvée dans cette zone
OTS Link     : aucune propriété trouvée dans cette zone
```

**Ne pas refaire ces trois scans à l’identique.**

---

## 7. Zone CSP 06 — état actuel

### Identifié et validé

```text
06 00 03 01 | 00 = Style Start/Stop
06 00 07 01 | 00 = Sync Start
```

### Recherché sans résultat dans les zones décrites

```text
ACMP
Auto Fill In
Synchro Stop
OTS Link
```

Il ne faut pas conclure que ces fonctions sont impossibles à piloter.  
Seulement qu’elles n’ont pas été trouvées dans les espaces CSP `06` déjà testés.

---

## 8. Pistes prioritaires restantes

### ACMP

Priorité :

1. vérifier si ACMP est mémorisé/restauré par Registration Memory ;
2. si oui, comparer deux registrations strictement identiques sauf ACMP ;
3. analyser la structure `.rgt` / bloc Style ;
4. chercher un lien avec la famille Yamaha `51` ;
5. envisager une commande write-only uniquement avec preuve solide.

### Fingering Type

Les scans massifs CSP/XG/EVENTS sont considérés épuisés.

Priorité :

1. structure `.rgt/.ssu` ;
2. mécanisme de rappel Registration ;
3. famille `51` sous une nouvelle hypothèse ;
4. bus interne carte principale / interface si nécessaire.

---

## 9. Règles pour éviter de refaire le même travail

Avant toute nouvelle campagne :

1. consulter `PROJECT_STATE.md` ;
2. consulter `CVP905_PROTOCOL_CHECKPOINT_RC4.md` ;
3. consulter `docs/FUNCTION_CATALOG.md` ;
4. consulter ce checkpoint ;
5. ne pas relancer une zone marquée « ne pas refaire » sans nouvelle hypothèse explicite ;
6. scans larges inconnus : **GET-only** ;
7. aucun brute-force SET inconnu ;
8. SET ciblé seulement après identification GET ou autre preuve solide ;
9. restaurer l’état après les SET de validation ;
10. toute valeur anormale `0x31` après SET = arrêt du test.

---

## 10. Documentation maître à mettre à jour

À intégrer ensuite dans les documents principaux :

### `PROJECT_STATE.md`

- campagne Fingering Deep Weekend terminée ;
- résultat final 1024/1024 ;
- aucun candidat A/B/A/B stable ;
- Sync Start validé GET + SET ;
- zones Style négatives à ne pas rescanner.

### `CVP905_PROTOCOL_CHECKPOINT_RC4.md`

- remplacer la campagne Fingering « active » par le résultat final ;
- ajouter Sync Start ;
- ajouter les zones ACMP négatives ;
- ajouter Auto Fill / Synchro Stop / OTS Link négatifs ;
- ajouter le sniff ACMP.

### `docs/FUNCTION_CATALOG.md`

Ajouter :

```text
Sync Start | 06 00 07 01 | 00 | VALIDÉE GET/SET
```

et documenter ACMP / Auto Fill / Synchro Stop / OTS Link comme **NON RÉSOLUES**, avec renvoi vers ce checkpoint pour les zones déjà testées.

