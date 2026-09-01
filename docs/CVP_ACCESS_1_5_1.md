# CVP Access 1.5.1 — consolidation technique RC2

## Statut

La RC2 consolide le runtime testé physiquement sur Yamaha CVP-905 firmware 1.03. Elle remplace le layout expérimental CAPS de la RC1 par un layout directement orienté accessibilité.

## Architecture transitoire

```text
cvp_access_1_5_1.py
        |
        +-- cvp_access_v1.5.py      base fonctionnelle validée
        |       |
        |       `-- cvp_access_v1.4.1.py
        |
        +-- cvp_midi.py
        +-- cvp_song_151.py
        +-- cvp_speech_151.py
        +-- cvp_style.py
        +-- cvp_voice.py
        +-- cvp_registration.py
        `-- cvp_yamaha.py
```

Le fichier installé comme runtime reste `/opt/cvp-access/cvp_access.py`, mais sa source 1.5.1 est `cvp_access_1_5_1.py`.

## Changements RC2

### Layout accessibilité

La couche CAPS RC1 est abandonnée.

```text
W  = nom Style
X  = nom Song
C  = longueur Song
V  = Syncro Start
B  = Guide
F7 = Métronome
```

Les touches `1..8` restent les mutes des huit parties Style.

Le volume Style utilise maintenant :

```text
PageUp               +1
PageDown              -1
Shift + PageUp        +5
Shift + PageDown      -5
```

Le volume de synthèse est présenté comme **« Vol. guide vocal »**.

### Aide CTRL

`CTRL + touche` annonce la fonction sans l'exécuter.

### Map clavier

`cvp_keyboard_map.py` génère une carte A4 paysage depuis la configuration réellement active. Elle affiche l'aide CTRL, les fonctions de chaque touche, les variantes Maj et les actions disponibles mais non attribuées.

### Actions non attribuées

Les fonctions suivantes restent implémentées mais ne sont pas attribuées au layout RC2 : Intro, Main A/B/C/D, Fill A/B/C/D, Break, Ending, Registration Memory et Stream Lights.

### Song

Le décodage du nom Song utilise le format Yamaha validé sur CVP-905. `X` et `C` vérifient d'abord la présence d'un Song. Sans Song chargé :

```text
Pas de Song chargé.
```

### Style

Le nom du Style est lu depuis `06 00 00 01 | 00`. Les suffixes techniques Yamaha tels que `.T308` et `.S000` sont retirés du nom prononcé.

### Syncro Start

Terminologie utilisateur : `Syncro Start`.

Identifiant logiciel conservé : `sync_start_toggle`.

Nom protocole Yamaha conservé dans les documents de recherche : `Sync Start`.

Propriété validée GET/SET : `06 00 07 01 | 00`.

### Guide

Propriété validée GET/SET : `04 03 00 01 | 00`.

### Métronome

Propriété validée GET/SET : `07 00 00 01 | 00`.

### Synthèse vocale

Le mode par défaut est `hybrid` : WAV pré-généré si disponible, sinon cache dynamique, sinon synthèse Piper. Le résultat dynamique est conservé dans le cache.

Le worker Piper est désormais **préchargé au démarrage** du runtime. Le modèle reste chargé pendant toute la durée du service, ce qui supprime le délai important observé lors de la première phrase dynamique.

### Génération vocale 1.5.1

`generate_151_voices.py` génère les aides CTRL configurées et les états Guide, Syncro Start, Métronome et Stream Lights. Le générateur tourne dans le venv Piper et ajoute explicitement `/usr/lib/python3/dist-packages` afin d'accéder à `evdev` fourni par Debian.

## Compatibilité et limites

Restent volontairement hors commande utilisateur directe :

- Voice Name CVP non résolu ;
- ACMP direct non résolu ;
- Fingering direct non résolu ;
- sélection Style par numéro Genos non validée sur CVP ;
- Global Reverb : GET seulement ;
- Stream Lights Speed non validé pour un SET utilisateur sûr.

Les résultats Genos restent un laboratoire secondaire et ne sont jamais considérés comme validation CVP.

## Validation RC2

Critères minimum : service systemd actif, runtime 1.5.1 chargé, configuration clavier sans erreur, mutes Style 1..8, informations W/X/C, Syncro Start V, Guide B, Métronome F7, volumes Style ±1/±5, aide CTRL sans exécution, map générée, Piper préchargé et WAV états 1.5.1 présents.
