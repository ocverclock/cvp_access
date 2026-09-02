# Historique des versions — CVP Access

## v1.0

- mute/unmute 16 pistes ;
- lecture état réel ;
- tempo ;
- transpose ;
- voix.

## v1.1

- ajout volume accompagnement Page Up / Page Down.

## v1.1.3

- contrôle du volume Style ;
- GET réel avant modification ;
- vérification GET après SET ;
- correction du décalage de lecture ;
- protection mono-instance ;
- fermeture propre de `amidi` ;
- annonces vocales du volume Style.

## v1.2.1

- touches `& é " ' ( - è _` pour les 8 parties Style ;
- mute/unmute individuel avec retour vocal ;
- détection du changement de Style ;
- resynchronisation des 8 parties ;
- lecture réelle avant modification et vérification après SET ;
- verrou mono-instance déplacé vers `~/.cache`.

## v1.4.1

Ajout du contrôle du lecteur Song et de l’annonce de position.

- `Espace` = Play / Pause ;
- `Entrée` = Stop ;
- `P` = position ;
- lecture mesure / temps depuis le CVP ;
- validation Song par `GET -> SET -> GET` ;
- synthèse vocale modulaire ;
- correction du décodage Yamaha des valeurs multi-octets 7 bits.

## v1.5 — clavier configurable

Phase historique de modularisation du clavier.

- TOML de configuration clavier ;
- catalogue fermé d’actions ;
- combinaisons SHIFT / CTRL / ALT / ALTGR / META ;
- support clavier principal, fonctions, navigation et pavé numérique ;
- configuration client conservée lors des mises à jour ;
- validation par CVP Doctor.

La couche Caps Lock expérimentée pendant cette phase a ensuite été abandonnée dans 1.5.1.

## v1.5 RC2 — synthèse pilotée par TOML

Phase historique antérieure à la consolidation 1.5.1.

- section `[speech]` ;
- modes `pregenerated / hybrid / runtime` ;
- `generation = configured` ;
- worker Piper persistant ;
- cache dynamique ;
- choix voix et `length_scale` ;
- CVP Doctor adapté aux banques vocales configurées.

## v1.5 RC4-dev — recherches Style / Registration

Checkpoint de développement historique, antérieur au renommage de la branche consolidée en 1.5.1.

Validations matérielles CVP-905 :

```text
style_intro:1..3
style_main:1..4
style_fill:1..4
style_break
style_ending:1..3
registration_recall:1..8
```

Section Control :

```text
F0 43 7E 00 ss 7F F7
```

Registration Recall :

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

Ces résultats restent intégrés dans la branche 1.5.1.

## v1.5.1-RC2 — base accessibilité reproductible

Checkpoint de référence précédent.

- abandon de Caps Lock ;
- aide `CTRL + touche` sans exécution ;
- informations Style / Song ;
- Syncro Start ;
- Guide ;
- Métronome ;
- volume Style ±1 / ±5 ;
- map clavier A4 ;
- préchargement Piper ;
- cache dynamique ;
- upgrade 1.5.1 ;
- vérificateur de paquet ;
- Doctor ;
- reproduction validée depuis un clone GitHub neuf.

## v1.5.1-RC3 — arrêt Piper et lecture Voice

Date de consolidation : **1 septembre 2026**.

Validation matérielle : Yamaha CVP-905 firmware 1.03.

### Arrêt Piper

- gestion de SIGTERM / SIGINT ;
- sortie Python normale ;
- `atexit` enregistré avant le préchargement Piper ;
- arrêt après préchargement sans SIGKILL ;
- arrêt pendant préchargement sans SIGKILL.

### Voice Main / Layer / Left

Propriété CVP :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Le payload 4 × 7 bits est décodé en :

```text
MSB / LSB / PC#
```

Voices physiquement validées :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

Nouvelles touches :

```text
N = nom Voice Main
, = nom Voice Layer
; = nom Voice Left
```

La synthèse prononce uniquement le nom du son.

La table complète des Voices Yamaha CVP-905 reste une évolution future.

### Fichiers principaux concernés

```text
cvp_access_1_5_1.py
cvp_speech.py
cvp_speech_151.py
cvp_keyboard.py
cvp_voice_names.py
config/default-1.5.1.toml
VERIFY_PACKAGE_151.py
cvp_access_installer/upgrade_1_5_1.sh
```

### Checkpoint

**CVP Access 1.5.1-RC3 est le point de référence au 1 septembre 2026.**
