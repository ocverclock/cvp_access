# CVP Access

**Interface d’accessibilité pour pianos Yamaha Clavinova CVP, basée sur Raspberry Pi, MIDI SysEx et retour vocal.**

CVP Access permet de piloter des fonctions importantes d’un Yamaha CVP depuis un clavier USB AZERTY, avec annonces vocales dans les haut-parleurs du piano. Le projet vise en priorité l’utilisation sans écran tactile.

> Projet non officiel. CVP Access n’est ni affilié à Yamaha Corporation, ni approuvé par Yamaha.

## État du projet

Version application de référence :

```text
CVP Access 1.5-RC4-dev
```

Version installateur / updater :

```text
0.3.2
```

Validation matérielle principale :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP pour le retour vocal
```

Le fichier `cvp_access_v1.4.1.py` reste volontairement présent : la v1.5 l’utilise comme moteur Yamaha SysEx validé.

## Fonctions disponibles

### Song MIDI

- mute/unmute réel des 16 pistes ;
- synchronisation des pistes au démarrage ;
- tempo ;
- transpose ;
- Play / Pause / Stop ;
- annonce de la position mesure/temps ;
- mesure précédente / suivante ;
- déplacement de 5 mesures ;
- accès direct à une mesure avec F3 ;
- points A/B et activation de boucle ;
- conservation automatique du métronome lors d’un déplacement vers l’arrière.

### Style

- mute/unmute des 8 parties Style ;
- volume global Style ;
- Start / Stop du Style avec F13 ;
- Intro 1 / 2 / 3 ;
- Main A / B / C / D ;
- Fill A / B / C / D ;
- Break ;
- Ending 1 / 2 / 3.

Les sections Style RC4 sont disponibles comme actions TOML configurables. Aucune nouvelle touche n’est imposée dans la configuration par défaut.

### Registration Memory

Rappel direct des Registration Memory 1 à 8 via action TOML :

```text
registration_recall:1
...
registration_recall:8
```

### Parties clavier

- Layer / Dual ON/OFF ;
- Left ON/OFF ;
- volume Main global de 0 à 127.

### Volume Song

Le volume global Song / MidiMaster est contrôlé directement de 0 à 127.

### Accessibilité

- clavier USB AZERTY configurable par TOML ;
- retour vocal Piper en français ;
- Piper asynchrone : le clavier n’attend pas la synthèse vocale ;
- mode `hybrid` avec WAV pré-générés + génération à la demande ;
- cache des phrases Piper ;
- remplacement des anciennes annonces de volume en attente par la valeur la plus récente ;
- `CTRL + touche` annonce la fonction affectée **sans l’exécuter** ;
- Caps Lock peut fournir une seconde couche de commandes ;
- carte clavier HTML générée depuis `keyboard.toml`.

## Commandes clavier par défaut

### Pistes Song

```text
A Z E R T Y U I   -> pistes 1 à 8
Q S D F G H J K   -> pistes 9 à 16
```

### Parties Style / clavier

```text
&    Rhythm 1
é    Rhythm 2
"    Bass
'    Chord 1
(    Chord 2
-    Pad
è    Phrase 1
_    Phrase 2
ç    Layer / Dual
à    Left
```

### Informations, transport et boucle

```text
F1              annoncer le tempo
F2              annoncer le transpose
F3              aller à une mesure
F4              définir le point A
F5              définir le point B
F6              activer / désactiver la boucle A/B
F13             Style Start / Stop

Espace          Play / Pause Song
Entrée          Stop Song
P               annoncer mesure / temps

←               mesure -1
→               mesure +1
Maj + ←         mesure -5
Maj + →         mesure +5
```

### Volumes

```text
↑               volume voix +
↓               volume voix -

Page Up         volume Style +5
Page Down       volume Style -5

Home            volume Song +1
Maj + Home      volume Song +5
End             volume Song -1
Maj + End       volume Song -5

Insert          volume Main +1
Maj + Insert    volume Main +5
Delete          volume Main -1
Maj + Delete    volume Main -5
```

### Aide vocale

`CTRL` est réservé à l’aide.

Exemples :

```text
CTRL + A
-> annonce la fonction de A
-> ne change pas l’état de la piste

CTRL + Maj + ←
-> annonce "Recule le Song de cinq mesures"
-> ne déplace pas le Song
```

### Système

```text
ESC             quitte CVP Access
                systemd peut ensuite le relancer
```

## Actions RC4-dev disponibles

Les nouvelles actions peuvent être affectées librement dans `[keys]` :

```text
style_intro:1..3
style_main:1..4
style_fill:1..4
style_break
style_ending:1..3
registration_recall:1..8
```

Exemple :

```toml
F7 = "style_main:1"
F8 = "style_main:2"
F9 = "style_main:3"
F10 = "style_main:4"

"SHIFT+F7" = "style_intro:1"
"SHIFT+F8" = "style_intro:2"
"SHIFT+F9" = "style_intro:3"

"ALT+F7" = "style_ending:1"
"ALT+F8" = "style_ending:2"
"ALT+F9" = "style_ending:3"

F11 = "style_break"
F12 = "registration_recall:1"
```

Ces affectations sont uniquement des exemples ; `config/default.toml` reste inchangé.

## Configuration clavier

Configuration client active :

```text
/etc/cvp-access/keyboard.toml
```

Configuration de référence dans le dépôt :

```text
config/default.toml
```

Validation :

```bash
python3 cvp_keyboard.py --check /etc/cvp-access/keyboard.toml
```

## Carte visuelle du clavier

Génération manuelle :

```bash
python3 cvp_keyboard_map.py \
    --config /etc/cvp-access/keyboard.toml \
    --output /etc/cvp-access/keyboard-map.html
```

L’installateur et l’updater essaient également de générer cette carte. Un échec de génération de la carte ne bloque pas l’installation du runtime.

## Retour vocal Piper

Configuration par défaut :

```toml
[speech]
mode = "hybrid"
generation = "configured"
cache = true
voice = "fr_FR-siwis-medium"
length_scale = 0.85
```

En mode `hybrid` :

1. un WAV pré-généré est utilisé s’il existe ;
2. sinon Piper synthétise la phrase ;
3. la phrase peut être conservée dans le cache ;
4. la synthèse est traitée dans un thread séparé afin de ne pas bloquer les commandes clavier.

Les fichiers WAV utilisateur sont stockés hors du dépôt, dans `~/cvp_voice`.

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

Les commandes Yamaha SysEx de ce projet ont été validées via MIDI DIN externe. L’USB Audio du CVP est utilisé pour les annonces vocales.

## Installation

Système visé :

```text
Raspberry Pi OS Lite 64-bit
Debian 13 / Trixie
ARM64
```

Installation depuis une image propre :

```bash
git clone https://github.com/ocverclock/cvp_access.git CVP_access
cd CVP_access

sudo bash cvp_access_installer/install.sh
```

L’installateur 0.3.2 :

- vérifie Debian/Trixie et ARM64 ;
- installe les dépendances ;
- installe Piper dans un environnement Python isolé ;
- installe `cvp_access_v1.5.py` comme runtime ;
- conserve `cvp_access_v1.4.1.py` comme moteur SysEx ;
- installe `cvp_keyboard.py`, `cvp_song.py`, `cvp_speech.py` et `cvp_piper_worker.py` ;
- installe le générateur de carte clavier s’il est présent ;
- crée la configuration client si elle n’existe pas ;
- conserve une configuration client existante ;
- prépare les annonces Piper nécessaires ;
- configure systemd, Samba, SSH et Avahi.

## Mise à jour

```bash
cd ~/CVP_access
sudo bash cvp_access_installer/update.sh
```

L’updater 0.3.2 préserve `/etc/cvp-access/keyboard.toml` lorsqu’il existe.

## Protocole Yamaha validé

Les détails RC3 sont conservés dans `CVP905_PROTOCOL_CHECKPOINT_RC3.md`.

Les nouvelles validations RC4 sont conservées dans :

```text
CVP905_PROTOCOL_CHECKPOINT_RC4.md
```

Principales nouveautés RC4 :

```text
Section Control
F0 43 7E 00 ss 7F F7

Registration Recall
F0 43 73 01 52 25 11 00 02 00 XX F7

Style Split Point
F0 43 73 01 51 00 00 00 03 10 00 dd F7

Left Split Point
F0 43 73 01 51 00 00 00 03 10 01 dd F7
```

## Recherche Fingering Type

Le codage du Fingering Type est maintenant confirmé dans les fichiers `.rgt` / `.ssu` :

```text
03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

La commande MIDI directe reste inconnue.

Les pistes suivantes ont déjà été explorées :

- ancien Special Operator Fingering ;
- CSP EVENTS ;
- zones XG documentées ;
- sniff passif du panneau ;
- candidat famille `51` / `10 02`.

Un scan GET read-only des indexes CSP `20..7F` est en cours.

## Documentation

- `RC3_NOTES.md` : synthèse RC3 ;
- `CVP905_PROTOCOL_CHECKPOINT_RC3.md` : checkpoint RC3 ;
- `CVP905_PROTOCOL_CHECKPOINT_RC4.md` : nouvelles validations RC4 ;
- `versions.md` : historique des versions ;
- `docs/` : documentation et outils de recherche protocole.

## Licence

Voir `LICENSE`.
