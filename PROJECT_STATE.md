# CVP Access — état de référence du projet

Dernière consolidation : **22 août 2026**.

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
6. `docs/CVP_FINGERING_SCANNER_V2.md` — campagne Fingering active.
7. Documents datés `docs/CVP905_*_YYYY-MM-DD.md` — preuves historiques utiles.
8. `CVP905_PROTOCOL_CHECKPOINT_RC3.md` — historique RC3 seulement ; RC4 prime en cas de contradiction.

Les scripts de recherche ne sont **jamais** une source de vérité à eux seuls : leur résultat doit être reporté dans le checkpoint ou le catalogue.

## Version actuelle

```text
Runtime : CVP Access 1.5-RC4-dev
Installer / updater : 0.3.2
Moteur SysEx conservé : cvp_access_v1.4.1.py
```

`cvp_access_v1.4.1.py` ne doit pas être supprimé : `cvp_access_v1.5.py` l'importe comme moteur Yamaha validé.

## Recherche Fingering Type

Valeurs confirmées dans les fichiers Yamaha `.rgt` / `.ssu` :

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

Commande MIDI directe : **non résolue à ce jour**.

Campagne active :

```text
docs/cvp_find_fingering_indexes_20_7f_v2.py
```

Méthode : GET-only sur l'espace CSP élargi puis comparaison :

```text
REG5 AI Full Keyboard
-> REG6 AI Fingered
-> REG5
-> REG6
```

La V2 utilise SQLite et remplace définitivement le scanner JSON V1.

## Règle de sécurité reverse engineering

- scan large : **GET uniquement** ;
- SET inconnu : interdit en brute force ;
- validation SET ciblée : `GET -> SET -> GET -> restauration -> GET` ;
- toute valeur anormale type `0x31` après SET = arrêt du test ;
- arrêter `cvp-access` et libérer `amidi` avant les probes bruts.
