# CVP Access — état de référence du projet

Dernière consolidation : **28 août 2026**.

## Matériel de référence

Toutes les validations matérielles actuelles doivent être interprétées comme réalisées sur :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN ProdipeMIDIlilo
USB Audio du CVP pour les annonces vocales
```

Les anciennes mentions de **CVP-909** sont historiques et ne doivent plus être utilisées comme preuve de validation pour ce projet.

## Sources de vérité — ordre de priorité

En cas de contradiction, utiliser cet ordre :

1. `PROJECT_STATE.md` — matériel, version et hiérarchie documentaire.
2. `CVP905_PROTOCOL_CHECKPOINT_RC4.md` — état courant du reverse engineering Yamaha.
3. `docs/FUNCTION_CATALOG.md` — statut actuel des fonctions/propriétés.
4. `docs/KEY_ACTIONS.md` — actions réellement exposables dans `keyboard.toml`.
5. `cvp_access_v1.5.py` + `cvp_keyboard.py` + `cvp_song.py` — implémentation runtime actuelle.
6. `docs/CVP905_RESEARCH_CHECKPOINT_2026-08-28.md` — preuves et zones négatives de la campagne du 28 août.
7. `docs/CVP_FINGERING_SCANNER_V2.md` et scripts de scan — historique/méthode de recherche, pas source de vérité à eux seuls.
8. Documents datés `docs/CVP905_*_YYYY-MM-DD.md` — preuves historiques utiles.
9. `CVP905_PROTOCOL_CHECKPOINT_RC3.md` — historique RC3 seulement ; RC4 prime en cas de contradiction.

Les scripts de recherche ne sont **jamais** une source de vérité à eux seuls : leurs résultats doivent être reportés dans le checkpoint ou le catalogue.

## Version actuelle

```text
Runtime : CVP Access 1.5-RC4-dev
Installer / updater : 0.3.2
Moteur SysEx conservé : cvp_access_v1.4.1.py
```

`cvp_access_v1.4.1.py` ne doit pas être supprimé : `cvp_access_v1.5.py` l'importe comme moteur Yamaha validé.

## CSP moderne — rappel

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

## Découvertes stabilisées au 28 août 2026

### Song — chemin / nom

Propriété :

```text
04 00 01 01 | 00
```

GET matériellement validé.

Exemple observé avec le Song **Shallow** :

```text
PRESET:/SONG/60 Popular/Pop/Shallow.S000.mid
```

Le CVP renvoie donc le **chemin complet** et pas seulement le nom.

Le format texte observé est un empaquetage Yamaha par blocs :

```text
1 octet masque des bits hauts + jusqu'à 7 octets de données
```

Il n'y a pas de longueur 14-bit en tête dans les réponses observées.

Pour les chaînes ASCII testées, les octets de masque valent `00`.

Le décodeur actuel de `cvp_song.py` doit être corrigé avant de considérer son résultat texte comme fiable dans le runtime.

Hypothèse de travail acceptée pour gagner du temps : appliquer aussi aux Songs les préfixes de source `PRESET:`, `USER:` et `USB1:` observés sur les Styles. Seul `PRESET:` a été physiquement observé sur un Song à ce jour ; ne pas refaire les tests USER/USB Song sauf contradiction réelle.

### Style — chemin / nom / source

Propriété :

```text
06 00 00 01 | 00
```

GET matériellement validé sur plusieurs Styles et plusieurs sources.

Exemples observés :

```text
PRESET:/STYLE/Pop&Rock/Pop/Cool 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/80s 8Beat.T308.prs
PRESET:/STYLE/Pop&Rock/Pop/Up-tempo 8Beat.T308.prs
USER:/STYLE/80sMajestyRock.T548.prs
USB1:/training.T310.sty
```

Cette propriété permet d'extraire :

```text
nom
source
chemin/catégorie
extension
```

Usage accessibilité visé, par exemple :

```text
Style : training
Source : USB 1
```

ou :

```text
Style : Cool 8Beat
Source : Preset
Catégorie : Pop & Rock, Pop
```

### Style — commandes validées

```text
06 00 03 01 | 00 = Style Start/Stop
06 00 07 01 | 00 = Sync Start
```

Pour Sync Start :

```text
00 = OFF
01 = ON
```

GET et SET ont été validés matériellement. Un blink MIDI ON/OFF a été visible sur le panneau.

Sync Start et ACMP sont indépendants : remettre Sync Start ON par MIDI ne remet pas ACMP ON si ACMP a été coupé manuellement.

## Recherche Fingering Type — état final

Valeurs confirmées dans les fichiers Yamaha `.rgt` / `.ssu` :

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Commande MIDI directe : **non résolue à ce jour**.

### Campagne Deep Weekend terminée

Campagne GET-only finale :

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

**Aucune propriété CSP GET de l'espace exploré ne reflète de façon reproductible le changement de Fingering Type.**

La campagne massive CSP Fingering est terminée. Ne pas la relancer sans nouvelle hypothèse.

Fichiers locaux historiques de cette campagne :

```text
docs/cvp_find_fingering_deep_weekend.py
fingering_deep_weekend.sqlite3
fingering_deep_weekend_report.json
```

La base SQLite et le rapport massif restent des artefacts locaux et ne sont pas destinés à GitHub.

## Zones de recherche explicitement négatives

Les résultats négatifs signifient uniquement : « rien trouvé dans la zone et avec la méthode décrites ». Ils n'excluent pas une autre famille SysEx, une commande write-only, une structure Registration/Style ou un mécanisme interne.

### Fingering — ne pas refaire à l'identique

```text
CSP Deep Weekend   : terminé, aucun candidat A/B/A/B stable
CSP EVENTS         : 26 624 propriétés, 63 abonnements acceptés, aucun signal Fingering exploitable
XG documenté       : 9 137 adresses, 1 936 réponses, aucun candidat reproductible
Sniff panneau      : aucun SysEx Split/Fingering exploitable
Famille 51 / 10 02 : testé comme Fingering direct, négatif
Special Operator   : F0 43 73 01 11 00 40 dd F7 ignoré
```

### ACMP — ne pas refaire à l'identique

Résultats OFF -> ON :

```text
06 00..0F 00..7F 01 | index 00       -> 0 changement
wide 00..0F/00..03/00..1F | index 00 -> 0 changement
06 00 00..7F 01 | index 00..7F       -> 0 changement
```

Le dernier espace représente 16 384 GET ciblés.

Sniff MIDI OUT pendant lecture d'un Style et bascules ACMP ON/OFF : trafic de notes/contrôleurs Style et une trame tempo observés, mais aucune trame ACMP identifiable.

### Autres fonctions Style — zone 06, index 00

```text
Auto Fill In : 06 00..0F 00..7F 01 | 00 -> 0 changement
Synchro Stop : même zone, CVP en mode Fingered -> 0 changement
OTS Link     : même zone -> 0 changement
```

Ne pas refaire ces scans à l'identique.

## Pistes prioritaires restantes

### ACMP

Priorité actuelle :

1. vérifier si ACMP est mémorisé/restauré par Registration Memory ;
2. si oui, comparer deux registrations identiques sauf ACMP ;
3. analyser la structure `.rgt` / bloc Style ;
4. chercher un lien avec la famille Yamaha `51` ;
5. envisager une commande write-only uniquement avec preuve solide.

### Fingering Type

Les scans massifs CSP/XG/EVENTS sont considérés épuisés.

Priorité :

1. structure `.rgt/.ssu` ;
2. mécanisme de rappel Registration ;
3. famille `51` avec une nouvelle hypothèse ;
4. bus interne carte principale/interface si nécessaire.

## Règle de sécurité reverse engineering

- scan large : **GET uniquement** ;
- SET inconnu : interdit en brute force ;
- validation SET ciblée : `GET -> SET -> GET -> restauration -> GET` ;
- toute valeur anormale type `0x31` après SET = arrêt du test ;
- arrêter `cvp-access` et libérer `amidi` avant les probes bruts ;
- avant une nouvelle campagne, consulter les zones négatives afin de ne pas refaire un espace déjà épuisé.
