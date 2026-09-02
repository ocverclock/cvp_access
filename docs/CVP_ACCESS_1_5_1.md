# CVP Access 1.5.1 — consolidation technique RC3

## Statut

**CVP Access 1.5.1-RC3** est le checkpoint de référence validé sur Yamaha CVP-905 firmware 1.03 au 1 septembre 2026.

La RC3 reprend la base RC2 et ajoute principalement :

1. l’arrêt propre du worker Piper ;
2. la lecture de l’identité et du nom des Voices Main / Layer / Left.

## Matériel de référence

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio CVP
Clavier Apple Extended USB
```

## Architecture transitoire

```text
cvp_access_1_5_1.py
        |
        +-- cvp_access_v1.5.py
        |       |
        |       `-- cvp_access_v1.4.1.py
        |
        +-- cvp_midi.py
        +-- cvp_song_151.py
        +-- cvp_speech.py
        +-- cvp_speech_151.py
        +-- cvp_piper_worker.py
        +-- cvp_style.py
        +-- cvp_voice.py
        +-- cvp_voice_names.py
        +-- cvp_registration.py
        +-- cvp_keyboard.py
        +-- cvp_keyboard_map.py
        `-- cvp_yamaha.py
```

Le fichier installé comme runtime reste :

```text
/opt/cvp-access/cvp_access.py
```

Sa source 1.5.1 est :

```text
cvp_access_1_5_1.py
```

Les moteurs historiques restent nécessaires à l’architecture actuelle.

## RC3 — arrêt propre de Piper

### Problème RC2

Lors d’un arrêt systemd, le runtime recevait SIGTERM mais le worker Piper pouvait rester vivant jusqu’au timeout systemd, puis recevoir SIGKILL.

### Correction

`cvp_access_1_5_1.py` installe des handlers :

```text
SIGTERM
SIGINT
```

Ils provoquent :

```text
SystemExit
```

et permettent à Python d’exécuter le nettoyage normal.

Dans `cvp_speech.py`, le nettoyage est enregistré avant le préchargement :

```python
atexit.register(self.close)
```

Chaîne attendue :

```text
SIGTERM
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt du worker Piper
```

### Validations physiques

Arrêt après chargement Piper :

```text
Arrêt propre demandé (signal 15).
Récepteur MIDI arrêté.
Deactivated successfully.
Stopped cvp-access.service
```

Aucun SIGKILL.

Arrêt pendant préchargement :

```text
Préchargement Piper...
Arrêt propre demandé (signal 15).
Deactivated successfully.
Stopped cvp-access.service
```

Aucun SIGKILL.

## RC3 — lecture des Voices

### Propriété CSP

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

### Payload observé

```text
MAIN  : 03 30 00 00
LAYER : 00 20 42 31
LEFT  : 03 20 0E 04
```

### Décodage 4 × 7 bits

```python
packed = (
    (b0 << 21)
    | (b1 << 14)
    | (b2 << 7)
    | b3
)

msb = (packed >> 16) & 0xFF
lsb = (packed >> 8) & 0xFF
program = (packed & 0xFF) + 1
```

Correspondances validées :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

### Module local

```text
cvp_voice_names.py
```

Il fournit :

```text
CVPVoiceId
decode_cvp_voice()
resolve_voice_name()
```

### Limite RC3

La table des noms est encore partielle.

Elle contient actuellement les trois Voices physiquement identifiées pendant la validation.

Une Voice non référencée utilise un fallback numérique MSB / LSB / Program.

La prochaine évolution logique est l’intégration de la table complète des Voices preset du CVP-905 depuis la Yamaha Data List.

Voir :

```text
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
```

## Layout accessibilité RC3

La couche CAPS de RC1 reste abandonnée.

### Informations principales

```text
W  = nom Style
X  = nom Song
C  = longueur Song
V  = Syncro Start
B  = Guide
N  = nom Voice Main
,  = nom Voice Layer
;  = nom Voice Left
F7 = Métronome
```

### Parties Style / clavier

```text
1..8 = parties Style
9    = Layer / Dual
0    = Left
```

### Pistes Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
```

### Volumes

```text
PageUp / PageDown             = Style ±1
Shift + PageUp / PageDown     = Style ±5
Home / End                    = Song ±1
Shift + Home / End            = Song ±5
Insert / Delete               = Main ±1
Shift + Insert / Delete       = Main ±5
Up / Down                     = Vol. guide vocal
```

## Aide CTRL

```text
CTRL + touche
```

annonce la fonction sans l’exécuter.

Les nouvelles actions Voice suivent la même règle.

## Politique vocale Voice

Pour Main / Layer / Left, le runtime prononce uniquement le nom du son.

Il ne prononce pas :

```text
Main CFX Concert Grand
```

mais :

```text
CFX Concert Grand
```

Le nom de la partie reste dans les logs.

## Song

Le runtime 1.5.1 utilise le décodage Yamaha validé pour le nom du Song.

Sans Song chargé :

```text
Pas de Song chargé.
```

Propriétés principales :

```text
Nom/path  : 04 00 01 01 | 00
Position  : 04 00 0A 01 | 00
Longueur  : 04 00 1B 01 | 00
Loop A/B  : 04 00 0D 01 | 00
Tracks    : 04 01 00 01 | 10..1F
```

## Style

Nom/path :

```text
06 00 00 01 | 00
```

Les suffixes techniques Yamaha `.Txxx` / `.Sxxx` sont retirés du nom prononcé.

Sync Start protocole :

```text
06 00 07 01 | 00
```

Terminologie utilisateur :

```text
Syncro Start
```

## Guide

```text
04 03 00 01 | 00
```

GET/SET bool validé.

## Métronome

```text
07 00 00 01 | 00
```

GET/SET validé.

## Actions implémentées non attribuées par défaut

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights
```

Elles doivent rester visibles dans la section :

```text
Actions disponibles mais non attribuées
```

de la map clavier.

## Synthèse vocale

Mode :

```text
hybrid
```

Politique :

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> cache
```

Piper est préchargé au démarrage.

Cache :

```text
~/.cache/cvp-access/tts/
```

## Génération vocale

`generate_151_voices.py` génère les aides CTRL configurées et les états nécessaires.

Les trois aides Voice sont pré-générables ; les noms de Voices restent des valeurs dynamiques.

## Vérification du paquet

```bash
python3 VERIFY_PACKAGE_151.py
```

Attendu :

```text
CVP Access 1.5.1 RC3 package: OK
```

Le vérificateur teste notamment :

```text
03 30 00 00 -> 108/0/1
00 20 42 31 -> 8/33/50
03 20 0E 04 -> 104/7/5
```

et les trois noms associés.

## Upgrade

```bash
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Attendu :

```text
[CVP Access] Upgrade runtime -> 1.5.1-RC3
...
[CVP Access] 1.5.1-RC3 installed.
```

L’upgrade :

- installe `cvp_voice_names.py` ;
- migre les nouveaux bindings lorsque les touches sont libres ;
- préserve les personnalisations utilisateur ;
- compile les modules ;
- génère la map ;
- génère les WAV configurés ;
- lance le Doctor ;
- redémarre le service.

## Validation RC3 minimale

```text
VERIFY_PACKAGE_151.py : OK
Doctor                : OK
Service               : actif
Piper preload         : OK
Arrêt normal          : aucun SIGKILL
Arrêt pendant preload : aucun SIGKILL
N / , / ;             : fonctionnels
CTRL aide              : sans exécution
```

## Reproductibilité

La RC2 a été validée depuis un clone GitHub neuf.

Après consolidation complète de la RC3 sur `main`, refaire le test clone neuf + upgrade afin de figer la reproductibilité RC3.

Une installation réellement vierge depuis une nouvelle carte Raspberry Pi OS reste un test futur.

## Terminologie utilisateur

Toujours utiliser :

```text
Vol. guide vocal
Syncro Start
Pas de Song chargé.
```

## Points de recherche à ne pas rouvrir sans nouvelle preuve

```text
ACMP direct
Fingering direct
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

Les résultats Genos restent secondaires et ne deviennent jamais une validation CVP sans test physique sur CVP-905.
