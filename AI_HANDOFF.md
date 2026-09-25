# AI_HANDOFF — CVP Access

Dernière consolidation : **25 septembre 2026**.

## 1. À lire en premier

Ordre de reprise :

1. `PROJECT_STATE.md`
2. `docs/CVP_ACCESS_1_7_MAPPING_UI_DESIGN.md` pour le chantier courant 1.7
3. `docs/CVP_ACCESS_1_6_1.md`
4. `docs/FEEDBACK_POLICY_1_6_1.md`
5. `docs/CVP_ACCESS_1_5_2.md`
6. `docs/NETWORK_MAINTENANCE_PORTAL.md`
7. `AI_HANDOFF.md`
8. `docs/CVP_ACCESS_1_5_1.md` pour la base fonctionnelle
9. `docs/KEY_ACTIONS_1_5_1.md`
10. `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md`
11. `CVP905_PROTOCOL_CHECKPOINT_RC4.md` pour le protocole historique
12. `docs/FUNCTION_CATALOG.md`
13. `docs/MIDI_RECORDER_1_6.md` pour l'historique du dictaphone 1.6

Ne pas relancer les scans massifs déjà clôturés sans nouvelle hypothèse.

## 2. Point de départ obligatoire

```text
CVP Access 1.6.1-RC2
Yamaha CVP-905 firmware 1.03
Raspberry Pi / Debian 13 arm64
```

Ne pas repartir de RC1, de la couche Caps Lock ou du runtime expérimental `1.5-RC4-dev`.

## 3. Runtime

```text
Repo            : ~/CVP_access
Runtime         : /opt/cvp-access
Entrée runtime  : /opt/cvp-access/cvp_access.py
Source courante : cvp_access_1_6_1.py
Base 1.5.1      : cvp_access_1_5_1_base.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Voix            : fr_FR-siwis-medium
Mode            : hybrid
```

Architecture :

```text
cvp_access_1_6_1.py
-> cvp_access_1_5_2.py
-> cvp_access_1_5_1_base.py
-> cvp_access_v1.5.py
-> cvp_access_v1.4.1.py
```

Le wrapper 1.6.1 active le Recorder F14/F15/F16. La couche 1.5.2 ajoute les commandes globales L / RPAREN et le Solo Maj. La base contient les correctifs Song, Piper, Voice Name, Guide Yamaha, métronome et accessibilité. La release courante est déclarée dans `cvp_access_installer/release.env`.

## 4. Layout de référence

### Style / clavier

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

Nom interne de `) / °` : `RPAREN`.

Terminologie Style :

```text
OFF -> Mute Rythme 1 / Mute Basse / ...
ON  -> Rythme 1 activé / Basse activée / ...
```

### Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
L               = toutes les pistes Song ON
```

Solo :

```text
Maj+A = Solo piste 1
Maj+Z = Solo piste 2
Maj+E = Solo piste 3
Maj+R = Solo piste 4
Maj+T = Solo piste 5
Maj+Y = Solo piste 6
Maj+U = Solo piste 7
Maj+I = Solo piste 8
Maj+Q = Solo piste 9
Maj+S = Solo piste 10
Maj+D = Solo piste 11
Maj+F = Solo piste 12
Maj+G = Solo piste 13
Maj+H = Solo piste 14
Maj+J = Solo piste 15
Maj+K = Solo piste 16
```

Le Solo active d'abord la piste choisie, coupe les quinze autres, relit les seize états puis annonce `Solo piste N`. L remet les seize pistes sur ON.

**Le Solo Maj est validé matériellement sur CVP-905 firmware 1.03.** La confirmation utilisateur du 12 septembre 2026 valide le comportement : piste choisie ON, 15 autres OFF.

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

Règle essentielle :

```text
Guide Yamaha (B) != guide vocal CVP Access (M)
```

M coupe uniquement nos WAV + Piper. Le volume mémorisé reste inchangé.

### Transport / navigation

```text
Espace      = Play/Pause
Entrée      = Stop
P           = position
← / →       = mesure -1 / +1
Maj+← / →   = mesure -5 / +5
F3          = aller à une mesure
F4          = point A
F5          = point B
F6          = boucle A/B
```

### Volumes

```text
Up / Down              = Vol. guide vocal
PageUp / PageDown      = Style ±1
Shift + PageUp/Down    = Style ±5
Home / End             = Song ±1
Shift + Home/End       = Song ±5
Insert / Delete        = Main ±1
Shift + Insert/Delete  = Main ±5
```

CTRL + touche = aide vocale sans exécution. Caps Lock n'est plus utilisé.

## 5. Speech

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> cache du résultat
```

Piper est préchargé et reste résident.

Cache :

```text
~/.cache/cvp-access/tts/
```

Les annonces Song prévisibles utilisent des fragments WAV. Nombres de mesure pré-générés : `0..150`.

Les 16 annonces `Solo piste N` sont pré-générées.

La lecture audio est sérialisée pour éviter les coupures/craquements dus à la terminaison brutale d'`aplay`. Les `replace_key` permettent d'abandonner les annonces obsolètes.

## 6. Piper shutdown — validé

```text
SIGTERM / SIGINT
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt Piper
```

Validé physiquement : arrêt normal et arrêt pendant preload sans SIGKILL.

## 7. Voice Name — validation partielle

```text
Propriété : 02 00 01 01
00 = Main
01 = Layer
02 = Left
```

Correspondances physiquement validées :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

`cvp_voice_names.py` reste partiel. Ne jamais inventer un nom absent de la table.

## 8. Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_161.py
sudo bash cvp_access_installer/upgrade_1_6_1.sh
```

L'upgrade RC2 réutilise encore les migrations historiques 1.5.1/1.5.2, génère la carte et les WAV, installe la maintenance, lance le Doctor et redémarre le service. Attention pour le chantier 1.7 : ces migrations ajoutent encore certaines affectations officielles lorsqu'elles sont absentes. Ce comportement devra être remplacé avant de considérer une désaffectation Web comme persistante.

## 9. Doctor — checkpoint confirmé le 12 septembre 2026

Résultat observé sur le Raspberry de référence après migration ALT -> Maj :

```text
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC3
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           10 présents
OK    WAV mute Style            8 présents
OK    WAV Solo Song             16 présents
```

Les banques vocales étaient complètes :

```text
Generated: 0; already present: 863
Generated: 0; existing: 262
```

## 10. Validation matérielle

### Déjà validé sur CVP-905

```text
navigation Song LEFT/RIGHT et ±5
F3 aller à la mesure
boucles A/B
Play/Pause
restauration métronome
arrêt Piper propre
lecture de plusieurs noms de Voice
Maj+... = Solo Song
```

### À tester fonctionnellement sur le CVP-905

```text
M       = mute/réactivation guide vocal
libellés Style Mute ...
L       = toutes pistes Song ON
) / °   = toutes parties Style ON
```

## 11. Actions non attribuées par défaut

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights
```

## 12. Recherches fermées

Ne pas rouvrir sans nouvelle preuve :

```text
ACMP direct
Fingering direct
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

ACMP et Fingering disposent de workarounds Registration validés.

## 13. Priorités suivantes

1. test matériel M ;
2. test matériel libellés Style `Mute ...` ;
3. test matériel L ;
4. test matériel `) / °` ;
5. si la latence vocale reste sensible alors que les WAV sont complets, identifier les annonces encore dynamiques et mesurer le chemin audio ;
6. compléter `cvp_voice_names.py` ;
7. refaire un clone GitHub neuf + upgrade.

## 14. Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## 15. Règle de reprise

**Le point de départ obligatoire est CVP Access 1.6.1-RC2 consolidé le 25 septembre 2026. Pour le chantier courant, lire ensuite `docs/CVP_ACCESS_1_7_MAPPING_UI_DESIGN.md`. Ne pas repartir de 1.5.1-RC3 comme version courante.**


## Maintenance autonome 1.5.2

La maintenance réseau fait partie du paquet courant. Référence complète : `docs/CVP_ACCESS_1_5_2.md` et `docs/NETWORK_MAINTENANCE_PORTAL.md`.

Règles à conserver :

```text
Ethernet ou Wi-Fi normal actif -> pas de CVP-ACCESS
aucun réseau normal -> CVP-ACCESS après ~30 s
hotspot -> Web http://10.42.0.1
Mac/Linux Samba -> smb://...
Windows Samba -> \\...
```

Le dashboard et la carte clavier doivent afficher les adresses Web/Samba copiables. La carte doit rester imprimable sur une seule page A4 paysage.

Le chemin d'upgrade courant est :

```bash
python3 VERIFY_PACKAGE_152.py
sudo bash cvp_access_installer/upgrade_1_5_2.sh
```


## Historique de conception 1.6 — ne pas utiliser comme état courant

La conception initiale du Dictaphone est conservée dans `docs/MIDI_RECORDER_1_6.md`. L'état courant est désormais 1.6.1-RC2 : F14/F15/F16 sont implémentées et réservées, et le listener MIDI interne est intégré. Cette section est historique ; ne pas réappliquer ses anciennes étapes de développement.


## Mise à jour depuis le portail

Le dashboard 1.5.2 possède un bouton **Mettre à jour depuis GitHub**. Il lance `/usr/local/sbin/cvp-update-from-github` dans un service systemd transitoire.

Le helper :

```text
refuse un dépôt avec modifications locales
-> git pull --ff-only
-> dernier VERIFY_PACKAGE_*.py
-> dernier upgrade_*.sh
```

Ne remplacer cette logique par un simple `git pull` exécuté dans le processus Web : l'upgrade peut redémarrer `cvp-web.service` et doit survivre à ce redémarrage.


### Checkpoints Recorder validés / en cours

F15 a été testée physiquement sur l'Apple Extended USB :

```text
KEY_F15 1 / KEY_F15 2 / KEY_F15 0
```

Le routeur prend désormais F14/F15 en charge et la keyboard map affiche F15 comme réservée au dictaphone 1.6.

Le moteur MIDI possède maintenant `register_midi_channel_listener()` et `dispatch_midi_channel_message()`. Le probe `CVP_RECORDER_PROBE=1` permet de vérifier les Note On/Note Off du canal 1 sans ouvrir un second port ALSA.


Capture canal 1 validée matériellement le 24 septembre 2026 avec `CVP_RECORDER_PROBE=1` : Note On / Note Off reçus correctement sur le CVP de référence, sans second port ALSA. Il reste à confirmer explicitement une commande SysEx pendant que le probe est actif avant de passer à l'écriture SMF.


## CVP Access 1.6.0-RC1

CVP Access 1.6.0-RC1 est maintenant implémenté dans le dépôt. Lire `docs/CVP_ACCESS_1_6.md` puis `docs/MIDI_RECORDER_1_6.md`.

Le Recorder est dans `cvp_recorder.py`, activé uniquement par le frontend `cvp_access_1_6_0.py`. F15 est interceptée avant le routeur générique ; CTRL+F15 conserve l'aide vocale sans exécution.

Le prochain travail est **validation matérielle**, pas redesign : installer via `VERIFY_PACKAGE_160.py` + `upgrade_1_6_0.sh`, tester F15 long/court, créer un .mid, vérifier la liste Web, puis tester lecture/stop et SysEx.


F14/F16 servent maintenant à la navigation Recorder : F14 précédent (glissando descendant), F16 suivant (glissando montant), action dès l'enfoncement ; maintien ~0,8 s annonce la sélection depuis fragments WAV. Les cues sont générés par SoX pendant l'upgrade. F16 est supportée dans `cvp_keyboard.py` et la keyboard map, mais F14/F16 doivent être validées physiquement avant de déclarer ce checkpoint terminé.


## Projet 1.7 — chantier courant

Référence de conception :

```text
docs/CVP_ACCESS_1_7_MAPPING_UI_DESIGN.md
```

Audit préalable effectué sur 1.6.1-RC2. Points à traiter avant toute écriture Web :

- centraliser catalogue d'actions et métadonnées clavier ;
- conserver F14/F15/F16 comme touches réservées et CTRL comme aide ;
- ne pas exposer Caps Lock dans l'éditeur simple RC1 ;
- rendre les désaffectations persistantes face aux futures mises à jour ;
- définir un unique mapping usine canonique ;
- adapter le Doctor aux mappings personnalisés ;
- protéger obligatoirement les endpoints d'écriture Web ;
- les profils nommés font partie du périmètre 1.7 : créer, enregistrer sous, renommer, dupliquer, ouvrir et activer explicitement ;
- conserver `keyboard.toml` comme fichier réellement chargé par le runtime, les profils étant une couche de gestion autour ;
- conserver le moteur Yamaha/SysEx validé sans refonte simultanée.
