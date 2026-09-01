# CVP Access 1.5.1-RC1-dev

## But

Aligner les quatre couches du projet :

```text
protocole validé
    -> module Python
    -> action clavier
    -> annonce vocale
```

sans casser la v1.5 actuellement validée.

## Stratégie de sécurité

`cvp_access_v1.5.py` et `cvp_access_v1.4.1.py` sont conservés.

Le nouveau point d'entrée est :

```text
cvp_access_1_5_1.py
```

Il charge la v1.5 et remplace uniquement les composants consolidés.

Rollback runtime :

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## Correctifs

### Song Name

Le décodeur historique de `cvp_song.py` supposait une longueur 14-bit.

La 1.5.1 utilise `cvp_song_151.py` + `cvp_yamaha.decode_yamaha_text()` :

```text
1 octet masque des bits hauts + jusqu'à 7 octets
```

### MIDI

`cvp_midi.MidiService` devient l'API pour les nouveaux contrôleurs.

Les anciennes fonctions restent dans le moteur v1.4.1 pendant la migration.

### Fonctions utilisateur ajoutées

- nom Style ;
- nom Song ;
- longueur Song ;
- Sync Start ON/OFF ;
- Guide ON/OFF ;
- Stream Lights ON/OFF ;
- Métronome ON/OFF ;
- Section Control sur couche CAPS ;
- Registration 1..8 sur couche CAPS.

### Vocal

Les phrases finies de la couche 1.5.1 sont pré-générées :

- aide CTRL ;
- états Sync Start ;
- Guide ;
- Stream Lights ;
- Métronome ;
- labels Intro/Main/Fill/Break/Ending/Registration.

Les données variables utilisent Piper dynamique + cache :

- nom Song ;
- nom Style ;
- longueur arbitraire.

## Installation RC1

Sur une installation v1.5 existante :

```bash
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Installation neuve :

```bash
sudo bash cvp_access_installer/install_1_5_1.sh
```

Mise à jour ultérieure :

```bash
sudo bash cvp_access_installer/update_1_5_1.sh
```

## Validation attendue sur CVP-905

Avant promotion en stable :

1. démarrage du service ;
2. `CTRL` aide couche normale ;
3. `Caps Lock` + `CTRL` aide couche secondaire ;
4. annonce Style ;
5. annonce Song ;
6. longueur Song ;
7. Sync Start toggle + relecture ;
8. Guide toggle + relecture ;
9. Stream Lights toggle + relecture ;
10. Métronome toggle + relecture ;
11. Intro/Main/Fill/Break/Ending ;
12. Registration 1..8 ;
13. anciennes commandes v1.5 inchangées.
