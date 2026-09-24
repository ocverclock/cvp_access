# CVP Access

**Interface d’accessibilité pour Yamaha Clavinova CVP, basée sur Raspberry Pi, MIDI SysEx, clavier USB et retour vocal Piper.**

CVP Access permet de piloter et d’interroger des fonctions importantes d’un Yamaha CVP depuis un clavier USB AZERTY, avec annonces vocales dans les haut-parleurs du piano. Le projet vise en priorité une utilisation sans écran tactile.

> Projet non officiel. CVP Access n’est ni affilié à Yamaha Corporation, ni approuvé par Yamaha.

## État du projet

Version de référence :

```text
CVP Access 1.5.2-RC1
Consolidation : 24 septembre 2026
```

Validation matérielle principale :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN : ProdipeMIDIlilo ou USB MIDI Interface
USB Audio du CVP
Clavier Apple Extended USB
Piper fr_FR-siwis-medium
```

Le runtime reste construit au-dessus du moteur historique validé. La couche actuelle est transitoire :

```text
cvp_access_1_5_2.py
  -> cvp_access_1_5_1_base.py
      -> cvp_access_v1.5.py
          -> cvp_access_v1.4.1.py
```

Ne pas supprimer ces fichiers tant que cette architecture n’a pas été remplacée.

## Fonctions principales

### Song MIDI

- mute/unmute réel des 16 pistes ;
- **Maj + touche piste = Solo** : la piste sélectionnée reste ON, les 15 autres passent OFF ;
- **L = toutes les pistes Song ON** ;
- lecture / pause / stop ;
- annonce de la position ;
- mesure précédente / suivante ;
- déplacement de 5 mesures ;
- accès direct à une mesure ;
- boucle A/B ;
- annonce du nom et de la longueur du Song ;
- métronome ;
- volume Song ;
- tempo ;
- transpose.

### Style

- mute/unmute des 8 parties ;
- annonces distinctes des pistes Song : `Mute Rythme 1`, `Mute Basse`, etc. ;
- **`) / °` = toutes les parties Style ON** ;
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

### Parties clavier

- Layer / Dual ON/OFF ;
- Left ON/OFF ;
- volume Main ;
- lecture du nom des Voices Main / Layer / Left.

### Accessibilité et voix

- au démarrage, une fois MIDI + clavier + moteur vocal prêts : **« Dispositif Melody Music CVP Access opérationnel. »** ;
- `ESC` : annonce **« Relance du dispositif CVP Access. »**, attend la fin de l’annonce, puis relance le service ;
- clavier USB AZERTY configurable par TOML ;
- `CTRL + touche` = aide vocale sans exécution ;
- **M = mute/réactivation du guide vocal CVP Access** ;
- M agit uniquement sur nos WAV + Piper, pas sur le Guide Yamaha ;
- retour vocal Piper en français ;
- mode `hybrid` ;
- WAV pré-générés ;
- cache dynamique ;
- worker Piper préchargé ;
- carte clavier HTML générée depuis la configuration active.

Les annonces Song prévisibles sont composées de WAV. La banque de nombres destinée aux mesures est limitée à `0..150`. Les 16 annonces `Solo piste N` sont pré-générées.

## Layout clavier 1.5.2-RC1

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
) / ° = toutes les parties Style ON
```

### Pistes Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16

Maj + A..K = Solo de la piste correspondante
L          = toutes les pistes Song ON
```

Exemples :

```text
Maj + A = Solo piste 1
Maj + Z = Solo piste 2
Maj + E = Solo piste 3
...
Maj + K = Solo piste 16
```

### Informations / accessibilité

```text
W  = nom Style
X  = nom Song
C  = longueur Song
V  = Syncro Start
B  = Guide Yamaha ON/OFF
M  = mute/réactivation du guide vocal CVP Access
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

`CTRL` est réservé à l’aide. Exemple :

```text
CTRL + Maj + E
-> annonce la fonction Solo piste 3
-> n’exécute pas le Solo
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
Guide Yamaha
Guide vocal
Vol. guide vocal
Syncro Start
Mute Rythme 1
Solo piste 1
Pas de Song chargé.
```

## Maintenance autonome

CVP Access peut être maintenu même chez un client sans box ni Wi-Fi.

```text
Réseau Ethernet ou Wi-Fi normal disponible
  -> connexion normale prioritaire
  -> CVP-ACCESS reste arrêté

aucun réseau normal disponible après ~30 s
  -> point d'accès CVP-ACCESS
  -> Raspberry : 10.42.0.1
  -> portail : http://10.42.0.1
```

L'installateur crée le profil de secours, le service `cvp-wifi-fallback.service` et le portail Web local. Sur une installation neuve, un mot de passe Wi-Fi aléatoire est généré et conservé dans `/etc/cvp-access/hotspot-password`. Un profil CVP-ACCESS existant conserve son mot de passe.

Le dashboard affiche l'état de CVP Access, le réseau, les interfaces MIDI, l'audio Yamaha, le clavier USB et les événements utiles. Il permet aussi de lancer le Doctor, relancer CVP Access et sélectionner l'interface MIDI ou le clavier à utiliser lorsqu'il existe plusieurs candidats.

Le portail est également accessible lorsque le Raspberry est connecté à un Wi-Fi normal, depuis le même sous-réseau, via `http://<hostname>.local` ou son adresse IPv4.

Depuis le dashboard, un technicien peut rechercher les réseaux Wi-Fi, sélectionner un SSID et saisir son mot de passe. CVP Access quitte alors le hotspot pour tenter la connexion. En cas d'échec, `CVP-ACCESS` est immédiatement réactivé ; le service de fallback reste une deuxième sécurité.

Les préférences matérielles sont mémorisées dans `/etc/cvp-access/hardware.toml` par identité stable, et non par numéro ALSA `hw:X,Y,Z`.

Le dashboard affiche aussi les accès de maintenance sous forme **cliquable pour copie** :

```text
Web réseau local : http://<hostname>.local
Web hotspot       : http://10.42.0.1

Mac / Linux :
smb://<hostname>.local/CVP_access
smb://<hostname>.local/CVP_config
smb://10.42.0.1/CVP_access
smb://10.42.0.1/CVP_config

Windows :
\\<hostname>.local\CVP_access
\\<hostname>.local\CVP_config
```

Les partages Samba officiels sont `CVP_access` pour le projet et `CVP_config` pour la configuration. Sur macOS, utiliser Finder → **Aller → Se connecter au serveur…** (`Cmd + K`) avec une URL `smb://...`. Sous Linux/GNOME/Zorin, utiliser également le format `smb://...` ; le backend GVFS SMB peut être requis.

La carte clavier reprend les blocs **Accès Web** et **Partages Samba** tout en restant conçue pour une impression sur **une seule page A4 paysage**.

Les actions de configuration nécessitent le mot de passe du hotspot `CVP-ACCESS`, utilisé comme mot de passe de maintenance. Le point d'accès fournit également les indications de portail captif destinées à proposer automatiquement le dashboard sur téléphone ou ordinateur. L'accès direct `http://10.42.0.1` reste toujours la référence en mode hotspot.

## Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_152.py
sudo bash cvp_access_installer/upgrade_1_5_2.sh
```

L’upgrade conserve les personnalisations existantes et n’ajoute les nouveaux raccourcis que si les combinaisons sont libres.

Le Doctor vérifie notamment le runtime, le layout, les WAV d’états, les WAV de mute Style, les 16 bindings Solo et les 16 WAV Solo.

## État de validation matérielle

Validé physiquement sur CVP-905 :

- déplacement Song par mesures ;
- F3 aller à une mesure ;
- boucles A/B ;
- transport Play/Pause ;
- restauration du métronome lors du transport ;
- arrêt propre du worker Piper ;
- lecture de plusieurs noms de Voices.

Implémenté et intégré à l’upgrade, mais à confirmer physiquement avant de le marquer validé matériellement :

- M : mute/réactivation du guide vocal CVP Access ;
- nouveaux libellés `Mute ...` des parties Style ;
- L : toutes les pistes Song ON ;
- `) / °` : toutes les parties Style ON ;
- Maj + piste : Solo Song.

## Documentation de reprise

Lire dans cet ordre :

```text
PROJECT_STATE.md
docs/CVP_ACCESS_1_5_2.md
docs/NETWORK_MAINTENANCE_PORTAL.md
AI_HANDOFF.md
docs/CVP_ACCESS_1_5_1.md
docs/KEY_ACTIONS_1_5_1.md
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
CVP905_PROTOCOL_CHECKPOINT_RC4.md
docs/FUNCTION_CATALOG.md
```

## Règles de protocole

Les recherches directes suivantes sont clôturées sauf nouvelle preuve :

```text
ACMP
Fingering
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu. Les résultats Genos constituent un laboratoire secondaire et ne doivent jamais être présentés comme une validation CVP sans test physique sur CVP-905.

## Licence

Voir `LICENSE`.
