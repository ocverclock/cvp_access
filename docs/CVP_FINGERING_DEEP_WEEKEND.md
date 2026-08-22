# CVP-905 — campagne Fingering Deep Weekend

Date de préparation : 22 août 2026.

## Pourquoi cette campagne

La campagne V2 `indexes 20..7F` s'est terminée correctement :

- 3 142 721 réponses baseline ;
- 256/256 blocs ;
- 672 différences A/B ;
- 384 différences stables A/B/A/B ;
- 0 match exact `0C -> 03`.

Le contrôle direct REG5 / REG6 / REG7 a ensuite montré :

```text
REG5 -> 04
REG6 -> 05
REG7 -> 06
```

sur la famille `00 00 00 01|20` (et le même motif était répété sur les 384
candidats stables). Ces résultats sont donc classés comme **miroir du numéro de
Registration**, pas comme Fingering Type.

Le scanner Deep Weekend conserve néanmoins tous les écarts et utilise REG7 comme
contrôle final : un motif stable `04 / 05 / 06` est marqué
`registration_mirror_04_05_06` au lieu d'être confondu avec Fingering.

## Sécurité

- propriétés inconnues : **GET uniquement** ;
- aucun SET CSP inconnu ;
- seuls les rappels Registration déjà validés REG5 / REG6 / REG7 sont utilisés ;
- REG5 est restaurée dans le `finally` ;
- un GET Tempo validé sert de garde de vie avant/après chaque bloc ;
- si le CVP est éteint ou si la liaison MIDI tombe, le bloc n'est pas marqué terminé ;
- SQLite permet la reprise après reboot ou crash.

## États utilisés

```text
A  = REG5 = AI Full Keyboard
B  = REG6 = AI Fingered
A2 = REG5 (confirmation)
B2 = REG6 (confirmation)
C  = REG7 (contrôle numéro de Registration)
```

REG7 n'est pas utilisée comme troisième état Fingering. Elle sert uniquement à
repérer les propriétés qui suivent le numéro de Registration (`04/05/06`).

## Couverture

### Zone 1 — cœur complet

```text
p0      00..0F
p1      00..0F
p2      00..7F
p3      01
index   00..7F
```

Cette zone repasse entièrement la campagne précédente et ajoute les indexes
`00..1F` qui n'avaient pas été couverts par V2.

### Zone 2 — extension p0

```text
p0      10..1F
p1      00..0F
p2      00..7F
p3      01
index   00..7F
```

### Zone 3 — extension p1

```text
p0      00..0F
p1      10..1F
p2      00..7F
p3      01
index   00..7F
```

### Zone 4 — structure p3, index 00

```text
p0      00..0F
p1      00..0F
p2      00..7F
p3      00,02..0F
index   00
```

Cette dernière zone est de priorité plus faible. Le budget mural par défaut est
48 h ; si les 48 h sont atteintes, le scanner termine proprement avec ce qui a
été couvert et produit le rapport.

## Volume maximal planifié

```text
Clés uniques A/B : 13 074 432
GET A+B          : 26 148 864
```

Les confirmations A2/B2/REG7 ne portent que sur les différences trouvées.

## Fichiers locaux

```text
~/CVP_access/fingering_deep_weekend.sqlite3
~/CVP_access/fingering_deep_weekend_report.json
```

Ces fichiers sont des sorties de recherche et ne doivent pas être commités.

## Lancement manuel

```bash
cd ~/CVP_access
sudo systemctl stop cvp-access cvp-fingering-scan
sudo pkill -x amidi 2>/dev/null || true
python3 -u docs/cvp_find_fingering_deep_weekend.py --max-hours 48
```

## Service systemd recommandé

`/etc/systemd/system/cvp-fingering-deep-weekend.service` :

```ini
[Unit]
Description=CVP Access - Fingering Deep Weekend GET Scan
After=multi-user.target
Conflicts=cvp-access.service cvp-fingering-scan.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/CVP_access
Environment=PYTHONUNBUFFERED=1
ExecStartPre=-/usr/bin/pkill -u pi -x amidi
ExecStart=/usr/bin/python3 -u /home/pi/CVP_access/docs/cvp_find_fingering_deep_weekend.py --max-hours 48
Restart=on-failure
RestartSec=300
KillMode=control-group
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
```

Installation :

```bash
sudo systemctl daemon-reload
sudo systemctl disable --now cvp-access cvp-fingering-scan
sudo systemctl enable --now cvp-fingering-deep-weekend
```

Suivi :

```bash
journalctl -u cvp-fingering-deep-weekend -n 40 --no-pager
journalctl -u cvp-fingering-deep-weekend -f
```

À la fin :

```bash
sudo systemctl disable --now cvp-fingering-deep-weekend
sudo systemctl enable --now cvp-access
```

## Lecture du rapport final

Les compteurs les plus importants sont :

```text
AB
ABA
ABAB
registration_mirror_04_05_06
stable_non_mirror
exact_0C_03
```

Les candidats intéressants sont d'abord les `ABAB` qui ne sont **pas** marqués
`registration_mirror_04_05_06`, puis les éventuels `exact_0C_03`.
