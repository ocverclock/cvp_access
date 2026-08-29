# CVP Access — état de référence du projet

Dernière consolidation : **29 août 2026**.

## Matériel de référence CVP

Toutes les validations CVP de ce projet doivent être interprétées comme réalisées sur :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP pour les annonces vocales
```

Les anciennes mentions de **CVP-909** sont historiques et ne doivent plus être utilisées comme preuve de validation.

## Banc de recherche secondaire : Genos 1

Depuis le 29 août 2026, un **Yamaha Genos 1** est utilisé comme banc de recherche Yamaha complémentaire.

Règle absolue :

> Une commande validée sur Genos n'est pas considérée comme validée sur CVP-905 tant qu'elle n'a pas été testée physiquement sur le CVP.

Les résultats Genos sont consolidés séparément dans :

```text
docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md
```

## Sources de vérité — ordre de priorité

En cas de contradiction, utiliser cet ordre :

1. `PROJECT_STATE.md` — matériel, version, décisions et hiérarchie documentaire.
2. `CVP905_PROTOCOL_CHECKPOINT_RC4.md` — reverse engineering CVP-905.
3. `docs/FUNCTION_CATALOG.md` — catalogue maître des fonctions et statuts.
4. `docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md` — résultats Genos 1, séparés des validations CVP.
5. `docs/KEY_ACTIONS.md` — actions réellement exposées dans `keyboard.toml`.
6. `cvp_access_v1.5.py` + modules runtime — implémentation.
7. Documents de recherche datés — preuves/historique.
8. `CVP905_PROTOCOL_CHECKPOINT_RC3.md` — historique uniquement.

Un script de recherche n'est jamais une source de vérité à lui seul : un résultat doit être reporté dans le checkpoint ou le catalogue.

## Version actuelle

```text
Runtime : CVP Access 1.5-RC4-dev
Installer / updater : 0.3.2
Moteur SysEx conservé : cvp_access_v1.4.1.py
```

`cvp_access_v1.4.1.py` ne doit pas être supprimé : le runtime v1.5 l'importe comme moteur Yamaha validé.

## CSP moderne CVP — rappel

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

## Découvertes CVP stabilisées

### Song — chemin / nom

Propriété :

```text
04 00 01 01 | 00
```

GET matériellement validé.

Exemple :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

Le CVP renvoie le chemin complet.

Format texte observé :

```text
1 octet masque des bits hauts + jusqu'à 7 octets de données
```

L'ancienne hypothèse d'une longueur 14-bit en tête est fausse pour ces réponses.

`cvp_song.py` doit encore être corrigé pour utiliser ce décodage.

### Style — chemin / nom / source

Propriété :

```text
06 00 00 01 | 00
```

GET matériellement validé sur plusieurs sources :

```text
PRESET:/STYLE/Pop&Rock/Pop/Cool 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/80s 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/Up-tempo 8Beat.T308.prs
USER:/STYLE/80sMajestyRock.T548.prs
USB1:/training.T310.sty
```

Cette propriété permet d'extraire le nom, la source, la catégorie et l'extension.

### Style — commandes CVP validées

```text
06 00 03 01 | 00 = Style Start/Stop
06 00 07 01 | 00 = Sync Start
```

Sync Start :

```text
00 = OFF
01 = ON
```

GET et SET validés.

Section Control :

```text
F0 43 7E 00 ss 7F F7
```

Valeurs validées :

```text
00..02 = Intro 1..3
08..0B = Main A..D
10..13 = Fill A..D
18     = Break
20..22 = Ending 1..3
```

Mute des huit parties Style :

```text
F0 43 73 01 51 05 00 00 08
Rhy1 Rhy2 Bass Chd1 Chd2 Pad Phr1 Phr2
F7
```

`00=OFF`, `01=ON`.

### Registration Memory — rappel externe

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

`XX=00..07` pour Registration 1..8.

Notification observée :

```text
F0 43 73 01 52 25 00 01 01 00 01 XX F7
```

## ACMP — recherche directe clôturée

La recherche d'une commande MIDI directe ACMP sur CVP-905 est **clôturée pour le projet actuel**.

Espaces déjà testés sans résultat :

```text
06 00..0F 00..7F 01 | index 00
wide 00..0F / 00..03 / 00..1F | index 00
06 00 00..7F 01 | index 00..7F
```

Le dernier test représente 16 384 GET ciblés.

Sniff MIDI OUT : aucune trame ACMP identifiable.

La documentation CVP consultée indique également ACMP ON/OFF comme fonction de panneau.

### Workaround Registration validé

Dans le bloc `.rgt` étudié :

```text
GPm07 payload[2]
00 = ACMP OFF
7F = ACMP ON
```

Un Registration minimal identique sauf ACMP a été validé physiquement : rappel ON/OFF correct, sans modifier Style, Fingering ou Voice.

Décision projet :

> Pour ACMP, utiliser Registration si nécessaire. Ne pas relancer une recherche directe sans nouvelle preuve de protocole.

## Fingering Type — recherche directe clôturée

Valeurs confirmées dans `.rgt` :

```text
GPm07 payload[8]

03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Le rappel Registration restaure correctement le Fingering Type lorsque la catégorie Style est mémorisée.

Campagnes directes terminées sans candidat exploitable :

```text
CSP Deep Weekend
CSP EVENTS
XG documenté
sniff passif
famille 51 / 10 02
Special Operator historique
```

Deep Weekend :

```text
Blocs             : 1024/1024
Clés uniques      : 13 074 432
GET A+B           : 26 148 864
Candidats A/B     : 6
Confirmés A/B/A/B : 0
Exact 0C/03       : 0
```

Décision projet :

> Pour Fingering Type, utiliser Registration si nécessaire. Ne pas relancer les campagnes massives sans nouvelle preuve indépendante.

## Parties Style dans Registration

Le différentiel `.rgt` a identifié :

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

## Auto Fill In / Synchro Stop / OTS Link

Scans CSP `06 00..0F 00..7F 01 | 00` :

```text
Auto Fill In : 0 changement
Synchro Stop : 0 changement (CVP placé en Fingered)
OTS Link     : 0 changement
```

La documentation CVP consultée indique Auto Fill In et Synchro Stop comme fonctions de panneau.

Décision :

```text
Auto Fill In : recherche directe clôturée
Synchro Stop : recherche directe clôturée
OTS Link     : NON RÉSOLU
```

## Résultats Genos 1 du 29 août — NON VALIDÉS CVP

Les résultats suivants sont validés **uniquement sur Genos 1** :

```text
SysEx bidirectionnel / XG Parameter Request : VALIDÉ
CSP moderne CVP sur Genos                   : NÉGATIF
Voice Right1 GET/SET XG                     : VALIDÉ
Voice Right2 GET/SET XG                     : VALIDÉ
Voice Right3 GET/SET XG                     : VALIDÉ
Voice Left GET/SET XG                       : VALIDÉ
Style direct select famille Yamaha 51       : VALIDÉ
Style identité courante GET                 : NON RÉSOLU
```

Détails dans `docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md`.

## Pistes prioritaires suivantes

1. Tester sur CVP-905 le mécanisme XG Voice validé sur Genos, en lecture d'abord.
2. Tester sur CVP-905 la commande de sélection Style famille `51`, avec état restaurable.
3. Sur Genos, chercher un GET ciblé de l'identité du Style autour de `51 05 00 03`.
4. Rechercher les commandes directes encore utiles : sélection Song, chargement de banque Registration, OTS Link.
5. Ne rouvrir ACMP/Fingering direct qu'en présence d'une nouvelle preuve.

## Règles de sécurité reverse engineering

- scan large inconnu : **GET uniquement** ;
- jamais de brute-force SET ;
- SET ciblé seulement avec hypothèse solide et état restaurable ;
- validation : `GET -> SET -> GET -> restauration -> GET` ;
- toute valeur anormale type `0x31` après un SET supposé bool/u7 = arrêt ;
- arrêter `cvp-access` et libérer `amidi` avant les probes bruts ;
- consulter les zones négatives avant toute nouvelle campagne.
