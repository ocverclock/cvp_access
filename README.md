# CVP Access

**Interface d’accessibilité pour pianos Yamaha Clavinova CVP, basée sur Raspberry Pi, MIDI SysEx et retour vocal.**

CVP Access permet à un musicien non-voyant ou malvoyant d’accéder à des fonctions du Yamaha CVP depuis un simple clavier USB, sans dépendre de l’écran tactile.

Le Raspberry Pi communique avec le piano par MIDI DIN pour le contrôle et utilise l’USB Audio du CVP pour diffuser les annonces vocales directement dans les haut-parleurs du piano.

> Projet non officiel. CVP Access n’est ni affilié à Yamaha Corporation, ni approuvé par Yamaha.

---

## État du projet

Le projet est fonctionnel et toujours en développement.

### Version application actuellement publiée

```text
cvp_access_v1.4.1.py
```

### Version installateur

```text
0.2.1
```

L’installateur choisit automatiquement :

1. `cvp_access.py` s’il existe à la racine du dépôt ;
2. sinon le fichier `cvp_access_v*.py` ayant le numéro de version le plus élevé.

Cela permet de conserver l’historique des versions tout en installant automatiquement la plus récente.

---

# Fonctions actuellement disponibles

## Song MIDI

- mute/unmute des 16 pistes Song ;
- lecture de l’état réel de chaque piste avant modification ;
- vérification de l’état après modification ;
- synchronisation des 16 pistes au démarrage ;
- lecture du tempo courant ;
- lecture du transpose courant ;
- Play / Pause ;
- Stop ;
- lecture de la position du Song ;
- annonce vocale de la mesure et du temps.

## Style / accompagnement

- volume global Style de 0 à 127 ;
- lecture du volume réel avant modification ;
- vérification après modification ;
- mute/unmute individuel des 8 parties Style :
  - Rhythm 1 ;
  - Rhythm 2 ;
  - Bass ;
  - Chord 1 ;
  - Chord 2 ;
  - Pad ;
  - Phrase 1 ;
  - Phrase 2 ;
- détection d’un changement de Style par observation des Program Change ;
- remise à ON du cache des 8 parties lors d’un changement de Style.

## Parties clavier

- Layer / Dual ON/OFF ;
- Left ON/OFF.

## Accessibilité

- contrôle complet depuis un clavier USB AZERTY ;
- retour vocal en français ;
- volume de la voix indépendant ;
- annonces vocales pré-générées pour une réponse rapide ;
- protection contre plusieurs instances simultanées ;
- fermeture propre du processus MIDI `amidi` ;
- redémarrage automatique possible via `systemd`.

---

# Architecture matérielle

```text
                    Clavier USB
                        │
                        ▼
                  Raspberry Pi
                  /            \
                 /              \
            MIDI SysEx        USB Audio
                │                │
                ▼                │
       Interface USB MIDI        │
          Prodipe MIDI           │
                │                │
             MIDI DIN            │
                │                │
                ▼                ▼
             Yamaha Clavinova CVP
                       │
                       ▼
                 Haut-parleurs CVP
```

## Pourquoi deux connexions ?

### Commandes

```text
Raspberry Pi
    ↓ USB
Interface Prodipe USB MIDI
    ↓ MIDI DIN IN/OUT
Yamaha CVP
```

Les commandes SysEx Yamaha utilisées par CVP Access ont été validées via une interface MIDI DIN externe.

Lors des essais, la liaison USB MIDI directe du CVP était visible sous Linux, mais les commandes SysEx utilisées par le projet ne fonctionnaient pas correctement par cette voie.

### Retour vocal

```text
Raspberry Pi
    ↓ USB Audio
Yamaha CVP
    ↓
Haut-parleurs du piano
```

L’USB Audio du CVP permet donc d’utiliser directement le système audio du piano pour les annonces.

---

# Commandes clavier

Le clavier est actuellement prévu pour une disposition **AZERTY**.

## Pistes Song 1 à 16

```text
A Z E R T Y U I
1 2 3 4 5 6 7 8

Q S D F G H J K
9 10 11 12 13 14 15 16
```

Chaque touche bascule la piste correspondante :

```text
ON → OFF
OFF → ON
```

L’état réel du CVP est relu avant le changement.

## Parties Style

```text
&   Rhythm 1
é   Rhythm 2
"   Bass
'   Chord 1
(   Chord 2
-   Pad
è   Phrase 1
_   Phrase 2
```

## Parties clavier

```text
ç   Layer / Dual
à   Left
```

## Informations et transport

```text
F1          annoncer le tempo
F2          annoncer le transpose

Espace      Play / Pause Song
Entrée      Stop Song
P           annoncer mesure / temps

↑           volume de la voix +
↓           volume de la voix -

Page Up     volume Style +5
Page Down   volume Style -5

ESC         quitter l’application
            → systemd la redémarre automatiquement
```

---

# Retour vocal

CVP Access utilise **Piper**, un moteur de synthèse vocale local.

Version Piper actuellement figée :

```text
piper-tts 1.6.0
```

Voix utilisée :

```text
fr_FR-siwis-medium
```

Le modèle vocal n’est pas stocké dans ce dépôt.

L’installateur :

1. crée un environnement Python isolé ;
2. installe Piper ;
3. télécharge automatiquement `fr_FR-siwis-medium` ;
4. génère automatiquement toute la banque de fichiers WAV.

Exemples d’annonces :

```text
Piste 1 coupée.
Piste 1 activée.

Tempo 100.

Transpose plus 7.

Accompagnement 85.

Rythme 1 désactivé.

Lecture.
Pause.
Arrêt.

Mesure 24, temps 3.
```

Piper n’est pas chargé pendant l’utilisation normale du piano : les annonces sont pré-générées pour réduire fortement la latence.

---

# Installation automatique

## Système recommandé

Utiliser une image fraîche :

```text
Raspberry Pi OS Lite 64-bit
Debian 13 / Trixie
```

L’installateur vérifie automatiquement :

- version de l’OS ;
- architecture ARM64 ;
- espace disque disponible.

Il refuse volontairement une autre version majeure de Debian au lieu d’effectuer une migration système risquée.

## Installation

Depuis une Raspberry Pi OS Lite fraîche :

```bash
git clone https://github.com/ocverclock/cvp_access.git CVP_access
cd CVP_access

sudo bash cvp_access_installer/install.sh
```

L’utilisation de `bash` est volontaire : les fichiers ajoutés via l’interface web GitHub peuvent ne pas avoir le bit exécutable.

---

# Ce que l’installateur configure

`install.sh` réalise automatiquement :

```text
contrôle Raspberry Pi OS / ARM64
        ↓
contrôle espace disque
        ↓
apt update
        ↓
apt full-upgrade
        ↓
installation dépendances
        ↓
permissions audio + input
        ↓
installation Piper dans un venv
        ↓
téléchargement fr_FR-siwis-medium
        ↓
génération de la banque vocale
        ↓
installation CVP Access dans /opt/cvp-access
        ↓
configuration systemd
        ↓
configuration Samba
        ↓
activation SSH
        ↓
activation Avahi / .local
        ↓
CVP Doctor
        ↓
proposition de redémarrage
```

Les principales dépendances installées comprennent :

- Python 3 ;
- `evdev` ;
- ALSA / `amidi` / `aplay` ;
- Mido ;
- RtMidi ;
- Piper ;
- Samba ;
- SSH ;
- Avahi ;
- outils USB et diagnostic.

La liste APT autoritative se trouve dans :

```text
cvp_access_installer/apt-packages.txt
```

---

# Installation runtime

Le programme exécuté n’est pas lancé directement depuis le dépôt Git.

L’installateur copie la version courante dans :

```text
/opt/cvp-access/cvp_access.py
```

Le dépôt reste donc modifiable par Samba sans casser immédiatement le programme actuellement exécuté.

Le service `systemd` utilise la copie située dans `/opt/cvp-access`.

---

# Démarrage automatique

Le service :

```text
cvp-access.service
```

est activé au démarrage.

Comportement attendu :

```text
Raspberry Pi démarre
        ↓
CVP Access démarre
        ↓
interface MIDI recherchée
        ↓
états CVP synchronisés
        ↓
clavier USB actif
```

En cas d’arrêt du programme :

```text
systemd
   ↓
redémarrage automatique
```

Ainsi, la touche `ESC` permet également de provoquer un redémarrage propre de CVP Access.

---

# Samba

L’installateur installe et configure Samba.

Le **dépôt Git complet** est partagé sur le réseau sous le nom :

```text
CVP_access
```

Exemple depuis Windows :

```text
\\cvp-access.local\CVP_access
```

Exemple depuis Linux :

```text
smb://cvp-access.local/CVP_access
```

Lors de l’installation, un mot de passe Samba est demandé pour l’utilisateur Linux.

Si un autre hostname a été configuré avec Raspberry Pi Imager, il est conservé.

---

# SSH et découverte réseau

L’installateur active :

```text
openssh-server
avahi-daemon
```

Sur une installation utilisant le hostname par défaut, celui-ci devient :

```text
cvp-access
```

Connexion typique :

```bash
ssh utilisateur@cvp-access.local
```

---

# CVP Doctor

Le projet fournit un outil de diagnostic :

```bash
python3 cvp_access_installer/tools/cvp_doctor.py
```

Il contrôle notamment :

```text
Raspberry Pi OS
architecture ARM64
Python
evdev
Piper
banque vocale
clavier USB
Prodipe MIDI
Clavinova USB Audio
runtime CVP Access
service systemd
Samba
Avahi
SSH
```

## Test MIDI réel

Pour effectuer un vrai `GET Tempo` sur le Yamaha :

```bash
sudo systemctl stop cvp-access

python3 cvp_access_installer/tools/cvp_doctor.py --active-midi

sudo systemctl start cvp-access
```

## Test audio réel

```bash
python3 cvp_access_installer/tools/cvp_doctor.py --active-audio
```

## Test MIDI + audio

```bash
sudo systemctl stop cvp-access

python3 cvp_access_installer/tools/cvp_doctor.py \
    --active-midi \
    --active-audio

sudo systemctl start cvp-access
```

---

# Mise à jour

```bash
cd ~/CVP_access

sudo bash cvp_access_installer/update.sh
```

La mise à jour :

- récupère les changements GitHub ;
- met Raspberry Pi OS à jour ;
- installe les éventuelles nouvelles dépendances ;
- met Piper à jour selon la version définie par le projet ;
- régénère uniquement les annonces vocales manquantes ;
- actualise le runtime ;
- actualise `systemd` ;
- actualise Samba ;
- redémarre CVP Access ;
- lance CVP Doctor.

Pour protéger le travail local, `update.sh` **n’écrase pas un dépôt Git contenant des modifications non validées**.

---

# Désinstallation

Retirer CVP Access tout en conservant Piper et la banque vocale :

```bash
sudo bash cvp_access_installer/uninstall.sh
```

Suppression complète du runtime, de Piper et des voix générées :

```bash
sudo bash cvp_access_installer/uninstall.sh --purge
```

Les paquets système, SSH, Samba et Avahi ne sont volontairement pas supprimés automatiquement.

---

# Yamaha SysEx

Le protocole utilisé par CVP Access est issu d’un travail de reverse engineering et de tests pratiques.

Le projet **ConPianist** de `hugbug` a constitué une source majeure pour comprendre plusieurs propriétés Yamaha.

Préfixe général rencontré :

```text
F0 43 73 01 52 25 26
```

Actions principales :

```text
GET       01 00
SET       01 01
INFO      00 00
RESPONSE  00 01
EVENTS    02 00
```

Exemple de propriétés déjà exploitées :

```text
Active piste     0C 00 01 01
Volume           0C 00 00 01
Tempo            08 00 00 01
Transpose        0A 00 00 01
Song Play        04 00 05 01
Song Position    04 00 0A 01
```

La documentation détaillée et les commandes encore expérimentales sont conservées dans :

```text
docs/yamaha-sysex-library.md
docs/PROTOCOL_NOTES.md
docs/cvp_probe_readonly.py
```

Une commande trouvée dans une documentation ou dans ConPianist n’est pas considérée comme compatible CVP tant qu’elle n’a pas été testée sur le matériel réel.

---

# Structure actuelle du dépôt

```text
cvp_access/
├── README.md
├── LICENSE
├── .gitignore
│
├── cvp_access_v1.4.1.py
├── versions.md
├── listes_commande.md
│
├── cvp_access_installer/
│   ├── install.sh
│   ├── update.sh
│   ├── uninstall.sh
│   ├── apt-packages.txt
│   ├── requirements-piper.txt
│   │
│   ├── tools/
│   │   ├── cvp_doctor.py
│   │   ├── generate_track_voices.py
│   │   └── generate_value_voices.py
│   │
│   ├── systemd/
│   │   └── cvp-access.service.in
│   │
│   ├── samba/
│   │   └── cvp-access.conf.in
│   │
│   └── docs/
│       ├── INSTALLATION.md
│       └── DEPENDENCIES.md
│
└── docs/
    ├── yamaha-sysex-library.md
    ├── PROTOCOL_NOTES.md
    └── cvp_probe_readonly.py
```

Les anciennes versions du programme sont actuellement conservées dans le dépôt pour documenter l’évolution du projet.

---

# Matériel actuellement utilisé pendant le développement

- Raspberry Pi sous Raspberry Pi OS Lite 64-bit ;
- clavier USB AZERTY ;
- interface Prodipe USB MIDI ;
- Yamaha Clavinova CVP ;
- liaison MIDI DIN bidirectionnelle ;
- liaison USB Audio CVP.

La compatibilité avec d’autres interfaces USB MIDI ou d’autres modèles Yamaha doit être confirmée expérimentalement.

---

# Principes du projet

CVP Access privilégie :

- l’accessibilité sans écran ;
- une réponse immédiate ;
- un comportement prévisible ;
- la lecture de l’état réel du piano lorsqu’elle est possible ;
- la vérification après modification ;
- le fonctionnement entièrement local ;
- l’absence de dépendance au cloud ;
- une installation reproductible depuis une Raspberry Pi OS Lite fraîche.

---

# Contribution et reverse engineering

Les tests de nouvelles commandes sont les bienvenus.

Pour chaque commande, il est utile de préciser :

```text
modèle Yamaha
fonction testée
SysEx envoyé
réponse reçue
résultat sur le piano
GET validé ?
SET validé ?
```

Le script :

```text
docs/cvp_probe_readonly.py
```

est destiné à faciliter l’exploration en lecture seule des propriétés encore inconnues.

---

# Crédits

Développement et tests :

**David Roussel — Melody Music Caen**

Travail de protocole réalisé avec l’aide de :

- ConPianist / hugbug ;
- documentation MIDI Yamaha ;
- tests directs sur les instruments Yamaha CVP.

Merci aux auteurs des projets open source utilisés par CVP Access, notamment Piper.

---

# Licence

Le dépôt est actuellement distribué sous licence **MIT**.

Voir :

```text
LICENSE
```

Les modèles vocaux Piper possèdent leurs propres conditions de licence. CVP Access télécharge le modèle vocal pendant l’installation au lieu de le redistribuer dans ce dépôt.

---

# English summary

CVP Access is a Raspberry Pi accessibility controller for Yamaha Clavinova CVP digital pianos.

It provides tactile USB-keyboard control, Yamaha MIDI SysEx communication over MIDI DIN, and pre-generated French spoken feedback through the piano’s USB Audio interface.

A fresh Raspberry Pi OS Lite 64-bit installation can be provisioned with:

```bash
git clone https://github.com/ocverclock/cvp_access.git CVP_access
cd CVP_access
sudo bash cvp_access_installer/install.sh
```

The installer configures the OS dependencies, MIDI/audio tools, Piper TTS with the `fr_FR-siwis-medium` voice, Samba, SSH, Avahi, systemd autostart and the CVP Doctor diagnostic tool.
