# CVP Access

**Interface d’accessibilité pour pianos Yamaha Clavinova CVP, basée sur Raspberry Pi, MIDI SysEx et retour vocal.**

CVP Access permet de piloter des fonctions importantes d’un Yamaha CVP depuis un clavier USB AZERTY, avec annonces vocales dans les haut-parleurs du piano. Le projet vise en priorité l’utilisation sans écran tactile.

> Projet non officiel. CVP Access n’est ni affilié à Yamaha Corporation, ni approuvé par Yamaha.

## État du projet

Version application de référence :

```text
CVP Access 1.5-RC3
```

Version installateur / updater :

```text
0.3.2
```

Validation matérielle principale de cette RC3 :

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
- Start / Stop du Style avec F13.

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

## Commandes clavier RC3 par défaut

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

`CTRL` est réservé à l’aide dans la RC3.

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

## Configuration clavier

Configuration client active :

```text
/etc/cvp-access/keyboard.toml
```

Configuration de référence dans le dépôt :

```text
config/default.toml
```

Exemple RC3 :

```text
keyboard_RC3_example.toml
```

Validation :

```bash
python3 cvp_keyboard.py --check /etc/cvp-access/keyboard.toml
```

La configuration RC3 de référence contient 53 affectations.

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

Génération des annonces nécessaires à la configuration active :

```bash
~/.local/share/cvp-access/piper-env/bin/python \
  cvp_access_installer/tools/generate_configured_voices.py \
  --config /etc/cvp-access/keyboard.toml
```

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

## Protocole Yamaha validé en RC3

Les détails sont conservés dans `CVP905_PROTOCOL_CHECKPOINT_RC3.md`.

Résumé :

```text
Métronome
07 00 00 01 | 00
00 OFF / 01 ON

Style Start / Stop
06 00 03 01 | 00
00 STOP / 01 START

Volume Song / MidiMaster
0C 00 00 01 | 50
0..127

Volume Main
0C 00 00 01 | 00
0..127

Song position
04 00 0A 01 | 00

Song Loop A/B
04 00 0D 01 | 00
```

## Recherche en cours / suspendue

Le contrôle MIDI du **Fingering Type / AI Full Keyboard** n’a pas produit de candidat reproductible lors des campagnes de recherche effectuées. Cette piste est suspendue et devra plutôt être reprise par comparaison de Registration/Backup ou une autre méthode de différentiel.

## Documentation RC3

- `RC3_NOTES.md` : synthèse de la release ;
- `CVP905_PROTOCOL_CHECKPOINT_RC3.md` : propriétés Yamaha validées ;
- `versions.md` : historique des versions ;
- `docs/` : documentation et outils de recherche protocole.

## Licence

Voir `LICENSE`.
