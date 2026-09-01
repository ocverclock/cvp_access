# AI_HANDOFF — CVP Access

## À lire en premier

Pour reprendre le projet :

1. lire `PROJECT_STATE.md` ;
2. lire `docs/CVP_ACCESS_1_5_1.md` ;
3. lire `docs/KEY_ACTIONS_1_5_1.md` ;
4. lire `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md` ;
5. consulter `docs/FUNCTION_CATALOG.md` ;
6. consulter `CVP905_PROTOCOL_CHECKPOINT_RC4.md` uniquement pour le protocole historique ;
7. ne pas relancer les recherches massives déjà clôturées.

## Version de départ

```text
CVP Access 1.5.1-RC3
Date de référence : 1 septembre 2026
Instrument validé : Yamaha CVP-905 firmware 1.03
```

**La base correcte est 1.5.1-RC3.**

Ne pas repartir d'une ancienne RC1, de la couche Caps Lock ou d'un ancien runtime `1.5-RC4-dev`.

## Runtime

```text
Repo            : ~/CVP_access
Runtime         : /opt/cvp-access
Entrée runtime  : /opt/cvp-access/cvp_access.py
Source 1.5.1    : cvp_access_1_5_1.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Voix            : fr_FR-siwis-medium
Mode            : hybrid
```

## RC3 — arrêt Piper

Le SIGKILL systemd observé en RC2 est corrigé.

Le runtime intercepte :

```text
SIGTERM
SIGINT
```

et provoque une sortie Python normale.

Chaîne attendue :

```text
signal
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt Piper
```

`atexit.register(self.close)` est enregistré avant le préchargement Piper.

Tests physiques validés :

```text
arrêt après préchargement : aucun SIGKILL
arrêt pendant preload     : aucun SIGKILL
```

Ne pas augmenter `TimeoutStopSec` pour masquer le problème.

## RC3 — Voice Name

Propriété CSP :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Payload :

```text
4 octets 7 bits
```

Décodage :

```python
packed = (b0 << 21) | (b1 << 14) | (b2 << 7) | b3
msb = (packed >> 16) & 0xFF
lsb = (packed >> 8) & 0xFF
program = (packed & 0xFF) + 1
```

Validations physiques :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

Module :

```text
cvp_voice_names.py
```

Actions :

```text
announce_main_voice_name
announce_layer_voice_name
announce_left_voice_name
```

Touches :

```text
N = Main
, = Layer
; = Left
```

La voix prononce uniquement le nom du son.

Exemple :

```text
CFX Concert Grand
```

et pas :

```text
Main CFX Concert Grand
```

Le log peut conserver le nom de la partie.

### Limite importante

La table `cvp_voice_names.py` n'est pas encore complète.

Elle contient actuellement les trois noms physiquement validés.

Une Voice non référencée doit utiliser le fallback MSB / LSB / Program.

Prochaine évolution logique :

> importer la table complète des Voices preset du CVP-905 depuis la Yamaha Data List.

Voir :

```text
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
```

## Layout RC3

```text
1..8 = mutes parties Style
9    = Layer / Dual
0    = Left

A Z E R T Y U I = Song 1..8
Q S D F G H J K = Song 9..16

W = nom Style
X = nom Song
C = longueur Song
V = Syncro Start
B = Guide
N = nom Voice Main
, = nom Voice Layer
; = nom Voice Left
F7 = Métronome
```

Song :

```text
Espace      = Play / Pause
Entrée      = Stop
P           = position
← / →       = mesure -1 / +1
Maj+← / →   = mesure -5 / +5
F3          = aller à une mesure
F4          = point A
F5          = point B
F6          = boucle A/B
```

Volumes :

```text
Up / Down              = Vol. guide vocal
PageUp / PageDown      = Style ±1
Shift + PageUp/Down    = Style ±5
Home / End             = Song ±1
Shift + Home/End       = Song ±5
Insert / Delete        = Main ±1
Shift + Insert/Delete  = Main ±5
```

CTRL + touche annonce la fonction sans l'exécuter.

Caps Lock n'est plus utilisé.

## Terminologie utilisateur

Toujours utiliser :

```text
Syncro Start
Vol. guide vocal
Pas de Song chargé.
```

Ne pas renommer l'identifiant interne :

```text
sync_start_toggle
```

Les documents protocole Yamaha peuvent conserver le terme officiel :

```text
Sync Start
```

## Speech

Piper est préchargé au démarrage.

Le worker reste résident.

Cache dynamique :

```text
~/.cache/cvp-access/tts/
```

Ordre :

```text
WAV pré-généré
-> cache dynamique
-> synthèse Piper
-> stockage cache
```

## Installation / upgrade

Validation courante :

```bash
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Attendu :

```text
CVP Access 1.5.1 RC3 package: OK
```

Upgrade :

```text
[CVP Access] Upgrade runtime -> 1.5.1-RC3
[CVP Access] 1.5.1-RC3 installed.
```

Doctor :

```text
OK Runtime 1.5.1
OK Version runtime 1.5.1-RC3
OK Layout accessibilité
OK WAV états 1.5.1
```

## Reproductibilité

La RC2 a été validée depuis un clone GitHub neuf.

Après push de la RC3, refaire la même validation avec :

```bash
mv ~/CVP_access ~/CVP_access_RC3_working
git clone https://github.com/ocverclock/cvp_access.git ~/CVP_access
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

## Actions non attribuées

Restent implémentées mais volontairement sans touche par défaut :

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights
```

## Points à ne pas rouvrir sans nouvelle preuve

Recherche directe clôturée :

```text
ACMP
Fingering
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

Pour ACMP et Fingering, utiliser les mécanismes Registration déjà validés.

Ne pas refaire les scans massifs précédents.

## Genos 1

Le Genos est un banc secondaire.

Aucune commande Genos ne doit être présentée comme validée CVP sans test physique sur CVP-905.

## Sources de vérité

Ordre de priorité :

1. `PROJECT_STATE.md`
2. `AI_HANDOFF.md`
3. `docs/CVP_ACCESS_1_5_1.md`
4. `docs/KEY_ACTIONS_1_5_1.md`
5. `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md`
6. `CVP905_PROTOCOL_CHECKPOINT_RC4.md`
7. `docs/FUNCTION_CATALOG.md`
8. runtime et modules
9. anciens checkpoints de recherche

## Prochain travail recommandé

Priorités :

1. compléter la table des noms de Voice ;
2. pousser la RC3 sur GitHub ;
3. faire un clone GitHub neuf + upgrade ;
4. éventuellement tester sur carte Raspberry Pi réellement vierge ;
5. continuer progressivement la séparation du moteur historique.

## Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## Règle de reprise

**Le point de départ obligatoire est CVP Access 1.5.1-RC3.**
