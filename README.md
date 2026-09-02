# CVP Access

**Interface d’accessibilité pour Yamaha Clavinova CVP, basée sur Raspberry Pi, MIDI SysEx, clavier USB et retour vocal Piper.**

CVP Access permet de piloter et d’interroger des fonctions importantes d’un Yamaha CVP depuis un clavier USB AZERTY, avec annonces vocales dans les haut-parleurs du piano. Le projet vise en priorité une utilisation sans écran tactile.

> Projet non officiel. CVP Access n’est ni affilié à Yamaha Corporation, ni approuvé par Yamaha.

## État du projet

Version de référence :

```text
CVP Access 1.5.1-RC3
```

Validation matérielle principale :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP
Clavier Apple Extended USB
Piper fr_FR-siwis-medium
```

Le runtime 1.5.1 reste construit au-dessus du moteur historique validé :

```text
cvp_access_1_5_1.py
  -> cvp_access_v1.5.py
      -> cvp_access_v1.4.1.py
```

Ne pas supprimer les fichiers historiques tant que cette architecture transitoire n’a pas été remplacée.

## Nouveautés 1.5.1-RC3

### Arrêt Piper propre

La RC3 corrige le worker Piper qui pouvait rester vivant lors d’un arrêt systemd et finir par recevoir un `SIGKILL`.

Le runtime intercepte désormais `SIGTERM` et `SIGINT`, provoque une sortie Python normale et laisse `atexit` fermer le worker Piper.

Le nettoyage est enregistré **avant le préchargement Piper**.

Validé physiquement :

```text
arrêt après préchargement Piper : aucun SIGKILL
arrêt pendant préchargement     : aucun SIGKILL
```

### Lecture des Voices Main / Layer / Left

Propriété CSP validée :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Le CVP renvoie quatre groupes de 7 bits. CVP Access reconstruit une valeur 24 bits puis extrait :

```text
MSB / LSB / PC#
```

Exemples physiquement validés :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

Touches :

```text
N = nom Voice Main
, = nom Voice Layer
; = nom Voice Left
```

La synthèse prononce uniquement le nom du son.

La table locale `cvp_voice_names.py` est encore partielle en RC3 : elle contient les trois Voices physiquement identifiées pendant la validation. Une Voice inconnue utilise un fallback numérique MSB / LSB / Program.

Voir :

```text
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
```

## Fonctions principales

### Song MIDI

- mute/unmute réel des 16 pistes ;
- lecture / pause / stop ;
- annonce de la position ;
- mesure précédente / suivante ;
- déplacement de 5 mesures ;
- accès direct à une mesure ;
- boucle A/B ;
- annonce du nom du Song ;
- annonce de sa longueur ;
- métronome ;
- volume Song ;
- tempo ;
- transpose.

### Style

- mute/unmute des 8 parties ;
- volume global Style ±1 / ±5 ;
- Start / Stop ;
- Syncro Start ;
- annonce du nom du Style ;
- Intro 1 / 2 / 3 ;
- Main A / B / C / D ;
- Fill A / B / C / D ;
- Break ;
- Ending 1 / 2 / 3.

Les sections Style restent disponibles comme actions configurables même lorsqu’elles ne sont pas affectées au layout par défaut.

### Registration Memory

Rappel direct disponible :

```text
registration_recall:1
...
registration_recall:8
```

### Parties clavier

- Layer / Dual ON/OFF ;
- Left ON/OFF ;
- volume Main ;
- lecture du nom des Voices Main / Layer / Left.

### Accessibilité

- clavier USB AZERTY configurable par TOML ;
- `CTRL + touche` = aide vocale sans exécution ;
- Caps Lock abandonné dans le layout 1.5.1 ;
- retour vocal Piper en français ;
- mode `hybrid` ;
- WAV pré-générés ;
- cache dynamique ;
- worker Piper préchargé ;
- carte clavier HTML générée depuis la configuration active.

## Layout clavier 1.5.1-RC3

### Parties Style / clavier

```text
1 = Rythme 1
2 = Rythme 2
3 = Basse
4 = Accord 1
5 = Accord 2
6 = Pad
7 = Phrase 1
8 = Phrase 2
9 = Layer / Dual
0 = Left
```

### Pistes Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
```

### Informations

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

### Song

```text
Espace       = Play / Pause
Entrée       = Stop
P            = position
← / →        = mesure -1 / +1
Maj + ← / →  = mesure -5 / +5
F3           = aller à une mesure
F4           = point A
F5           = point B
F6           = boucle A/B
```

### Volumes

```text
↑ / ↓                  = Vol. guide vocal + / -
Page ↑ / Page ↓        = Style +1 / -1
Maj + Page ↑ / Page ↓  = Style +5 / -5
Origine / Fin          = Song +1 / -1
Maj + Origine / Fin    = Song +5 / -5
Inser / Suppr          = Main +1 / -1
Maj + Inser / Suppr    = Main +5 / -5
```

## Aide vocale CTRL

`CTRL` est réservé à l’aide.

Exemple :

```text
CTRL + N
-> annonce la fonction affectée à N
-> n'interroge pas la Voice
```

## Synthèse vocale

Configuration de référence :

```toml
[speech]
mode = "hybrid"
generation = "configured"
cache = true
voice = "fr_FR-siwis-medium"
length_scale = 0.85
```

Politique :

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> stockage dans le cache
```

Cache :

```text
~/.cache/cvp-access/tts/
```

Terminologie utilisateur :

```text
Vol. guide vocal
Syncro Start
Pas de Song chargé.
```

## Vérification du paquet 1.5.1

```bash
python3 VERIFY_PACKAGE_151.py
```

Résultat attendu :

```text
CVP Access 1.5.1 RC3 package: OK
```

## Upgrade vers 1.5.1-RC3

Sur une installation CVP Access existante :

```bash
cd ~/CVP_access
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Attendu :

```text
[CVP Access] Upgrade runtime -> 1.5.1-RC3
...
[CVP Access] 1.5.1-RC3 installed.
```

Le test de reproductibilité depuis un clone GitHub neuf doit être refait après consolidation finale de la RC3.

Une installation 1.5.1-RC3 réellement vierge depuis une nouvelle carte Raspberry Pi OS reste un test futur.

## Architecture matérielle

```text
Clavier USB
    |
    v
Raspberry Pi
    | \
    |  \ USB Audio -> haut-parleurs CVP
    |
    +---- USB -> interface MIDI Prodipe
                   |
                   v
                MIDI DIN
                   |
                   v
               Yamaha CVP
```

Les commandes SysEx CVP du projet ont été validées via MIDI DIN externe.

## Documentation de reprise

Lire dans cet ordre :

```text
PROJECT_STATE.md
AI_HANDOFF.md
docs/CVP_ACCESS_1_5_1.md
docs/KEY_ACTIONS_1_5_1.md
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
CVP905_PROTOCOL_CHECKPOINT_RC4.md
docs/FUNCTION_CATALOG.md
```

## Recherche protocole

Les recherches directes suivantes sont clôturées sauf nouvelle preuve :

```text
ACMP
Fingering
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

Les résultats Genos constituent un laboratoire secondaire et ne doivent jamais être présentés comme une validation CVP sans test physique sur CVP-905.

## Licence

Voir `LICENSE`.
