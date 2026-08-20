# CVP Access RC3 controls — lot de test

Fonctions regroupées dans ce lot, validées sur Yamaha CVP-905 firmware 1.03 :

- F13 : Style Start / Stop
- HOME / END : volume Song +1 / -1
- SHIFT+HOME / SHIFT+END : volume Song +5 / -5
- INSERT / DELETE : volume Main +1 / -1
- SHIFT+INSERT / SHIFT+DELETE : volume Main +5 / -5
- conservation du métronome lors d'une navigation Song arrière
- annonces Piper asynchrones et hooks RC3 complets

## Application

Décompresser le ZIP, puis depuis le dossier obtenu :

```bash
python3 apply_rc3_controls_update.py ~/CVP_access
```

Le script crée des sauvegardes `*.bak-RC3-controls`, applique le lot puis
compile les fichiers Python et valide les TOML. Il n'envoie aucune commande MIDI.

## Avant test du runtime

```bash
cd ~/CVP_access

sudo systemctl stop cvp-access
pkill -f 'amidi.*-d'

python3 cvp_keyboard.py --check keyboard_RC3_example.toml
sudo cp keyboard_RC3_example.toml /etc/cvp-access/keyboard.toml

python3 cvp_access_v1.5.py
```

## Régression à tester

1. F13 deux fois : Style START puis STOP.
2. HOME / END : Song +1 / -1.
3. SHIFT+HOME / SHIFT+END : Song +5 / -5.
4. INSERT / DELETE : Main +1 / -1.
5. SHIFT+INSERT / SHIFT+DELETE : Main +5 / -5.
6. Métronome ON + LEFT : reste ON.
7. Métronome ON + SHIFT+LEFT : reste ON.
8. Métronome ON + F3 vers une mesure antérieure : reste ON.
9. F3 / F4 / F5 / F6 : fonctions Song/Loop toujours opérationnelles.
10. Vérifier que les annonces Piper n'empêchent pas les touches suivantes de répondre.
