# CVP Fingering scanner 20..7F — V2 SQLite

## But

Remplacer définitivement `cvp_find_fingering_indexes_20_7f.py` V1, dont le JSON géant saturait la RAM du Raspberry Pi 1 Go.

La V2 conserve la même recherche protocolaire :

```text
A  = REG5 / AI Full Keyboard
B1 = REG6 / AI Fingered
A2 = REG5
B2 = REG6
```

Les propriétés inconnues sont interrogées en **GET uniquement**.

Script actif :

```text
docs/cvp_find_fingering_indexes_20_7f_v2.py
```

## Espace scanné

```text
Property-ID : 00..0F / 00..0F / 00..7F / 01
Indexes     : 20..7F
256 blocs
12 288 GET par bloc
```

## Reprise de la campagne V1

Si `~/CVP_access/fingering_idx20_7f_report.json` existe et que la base SQLite n'existe pas, V2 importe le baseline en streaming :

```text
~/CVP_access/fingering_idx20_7f.sqlite3
```

Le JSON V1 n'est jamais modifié. Un bloc legacy marqué terminé mais ne contenant aucune réponse est rejeté et rescanné.

Migration réelle du 22 août 2026 :

```text
1 951 899 réponses baseline
159 blocs valides repris
4 blocs rejetés puis rescannés : 09:0F, 0A:00, 0A:01, 0A:02
```

## Gain mémoire observé

V1 :

```text
JSON ~137 MiB
Python ~710 MiB RSS avant OOM
bloc dégradé jusqu'à ~7 min
```

V2 :

```text
RSS max observée ~27-28 MiB
bloc observé ~1,3 min
```

## Test migration uniquement

```bash
cd ~/CVP_access
python3 -u docs/cvp_find_fingering_indexes_20_7f_v2.py --migrate-only
```

Cette commande ne nécessite pas le MIDI.

## Lancement manuel

```bash
cd ~/CVP_access
sudo systemctl stop cvp-access
sudo pkill -f amidi 2>/dev/null || true

python3 -u docs/cvp_find_fingering_indexes_20_7f_v2.py 2>&1 \
  | tee -a ~/CVP_access/fingering_idx20_7f_v2.log
```

## Mode autonome recommandé pour les longues campagnes

Service utilisé avec succès :

```ini
[Unit]
Description=CVP Access - Fingering GET Scan V2
After=multi-user.target
Conflicts=cvp-access.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/CVP_access
Environment=PYTHONUNBUFFERED=1
ExecStartPre=-/usr/bin/pkill -u pi -x amidi
ExecStart=/usr/bin/python3 -u /home/pi/CVP_access/docs/cvp_find_fingering_indexes_20_7f_v2.py
Restart=on-failure
RestartSec=30
KillMode=control-group
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

Installation :

```bash
sudo tee /etc/systemd/system/cvp-fingering-scan.service >/dev/null <<'EOF'
[Unit]
Description=CVP Access - Fingering GET Scan V2
After=multi-user.target
Conflicts=cvp-access.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/CVP_access
Environment=PYTHONUNBUFFERED=1
ExecStartPre=-/usr/bin/pkill -u pi -x amidi
ExecStart=/usr/bin/python3 -u /home/pi/CVP_access/docs/cvp_find_fingering_indexes_20_7f_v2.py
Restart=on-failure
RestartSec=30
KillMode=control-group
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl disable --now cvp-access
sudo systemctl daemon-reload
sudo systemctl enable --now cvp-fingering-scan
```

Suivi :

```bash
journalctl -u cvp-fingering-scan -n 30 --no-pager
journalctl -u cvp-fingering-scan -f
systemctl status cvp-fingering-scan --no-pager -l
```

Fermer SSH ou quitter `journalctl -f` n'arrête pas le scan.

## Reprise après crash/reboot

- Phase 1 : blocs validés stockés dans `blocks`.
- B1 : curseur persistant en SQLite.
- A2/B2 : chaque candidat porte son état d'avancement.
- `Restart=on-failure` relance le processus après crash.
- `enable` relance le service après reboot.

## Sorties générées — ne pas committer

```text
fingering_idx20_7f.sqlite3
fingering_idx20_7f.sqlite3-wal
fingering_idx20_7f.sqlite3-shm
fingering_idx20_7f_v2_report.json
fingering_idx20_7f_v2.log
```

Le `.gitignore` du projet doit les exclure.

## Fin de campagne

Le rapport compact donne :

```text
baseline_responses
preliminary_candidates_AB
confirmed_ABA
confirmed_ABAB
exact_0C_03_count
confirmed[]
```

Le marqueur `0C -> 03` correspond aux valeurs de stockage observées pour AI Full Keyboard -> AI Fingered.

Après la campagne :

```bash
sudo systemctl disable --now cvp-fingering-scan
sudo systemctl enable --now cvp-access
```

Ne conclure sur Fingering Type qu'après la fin complète A/B/A/B.
