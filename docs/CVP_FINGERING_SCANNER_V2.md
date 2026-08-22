# CVP Fingering scanner 20..7F — V2 SQLite

## But

Remplacer `cvp_find_fingering_indexes_20_7f.py`, dont le gros JSON finissait
par saturer la RAM d'un Raspberry Pi 1 Go.

La V2 garde la même recherche protocolaire :

```text
A = REG5 / AI Full Keyboard
B = REG6 / AI Fingered
A2 = REG5
B2 = REG6
```

Les propriétés inconnues sont interrogées en **GET uniquement**.

## Fichier

```text
docs/cvp_find_fingering_indexes_20_7f_v2.py
```

## Reprise de la campagne V1

Si ceci existe :

```text
~/CVP_access/fingering_idx20_7f_report.json
```

et que la base SQLite V2 n'existe pas, la V2 importe le baseline en streaming
dans :

```text
~/CVP_access/fingering_idx20_7f.sqlite3
```

Le JSON de la V1 n'est jamais modifié.

Un bloc legacy marqué terminé mais ne contenant **aucune réponse** est rejeté
pendant la migration et sera rescanné. Cela protège notamment contre les
arrêts OOM observés pendant la campagne initiale.

## Lancement conseillé

Arrêter l'ancienne campagne puis libérer le port MIDI :

```bash
cd ~/CVP_access

sudo systemctl stop cvp-access
sudo pkill -f amidi 2>/dev/null || true
```

Test de migration sans MIDI :

```bash
python3 -u docs/cvp_find_fingering_indexes_20_7f_v2.py --migrate-only
```

Puis lancer la campagne :

```bash
python3 -u docs/cvp_find_fingering_indexes_20_7f_v2.py 2>&1 \
  | tee -a ~/CVP_access/fingering_idx20_7f_v2.log
```

## Fichiers générés

```text
fingering_idx20_7f.sqlite3
fingering_idx20_7f_v2_report.json
fingering_idx20_7f_v2.log
```

La base SQLite et les logs sont des sorties de campagne et ne doivent pas être
committés dans GitHub.

## Architecture mémoire

La V1 faisait essentiellement :

```text
énorme JSON -> énorme dict Python -> réécriture du JSON complet
```

La V2 fait :

```text
1 bloc / 1 batch en RAM
        ↓
SQLite
        ↓
libération mémoire
```

Les phases B1/A2/B2 sont elles aussi traitées par lots de 1500 propriétés.

## Résultat final

Le rapport compact conserve uniquement les compteurs et les candidats
confirmés A/B/A/B, avec un marqueur spécial pour :

```text
0C -> 03
```

qui correspond aux valeurs observées dans les fichiers `.rgt` / `.ssu` pour
AI Full Keyboard -> AI Fingered.
