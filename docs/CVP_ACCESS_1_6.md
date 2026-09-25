# CVP Access 1.6.0-RC1 — dictaphone MIDI accessible

Date : 24 septembre 2026

## Objet

CVP Access 1.6.0-RC1 ajoute un dictaphone MIDI accessible à une seule touche, sans ouvrir un second port MIDI et sans modifier le chemin SysEx Yamaha validé.

La base reste la pile 1.5.2 :

```text
cvp_access_1_6_0.py
 -> cvp_access_1_5_2.py
 -> cvp_access_1_5_1_base.py
 -> cvp_access_v1.5.py
 -> cvp_access_v1.4.1.py
```

## Touche F15

F15 a été validée physiquement sur l'Apple Extended USB :

```text
KEY_F15 1
KEY_F15 2
KEY_F15 0
```

Le runtime ignore la répétition `value=2`.

Comportement :

```text
REPOS
  F15 court -> lecture du morceau sélectionné
  F15 long  -> armement

ARMÉ
  première Note On canal 1 -> début réel de l'enregistrement
  F15 court avant toute note -> annulation

ENREGISTREMENT
  F15 court -> arrêt + sauvegarde + sélection du nouveau fichier

LECTURE
  F15 court -> stop
  F15 long  -> stop puis armement d'un nouveau morceau
```

CTRL+F15 conserve la règle d'accessibilité globale : annonce de la fonction sans exécution.

## Capture MIDI

Le récepteur permanent `midi_receiver()` reste l'unique lecteur du port MIDI brut.

```text
MIDI physique
  -> midi_receiver()
      -> SysEx Yamaha existant
      -> copie des messages canal vers Recorder
```

Le tap canal 1 a été validé matériellement avec Note On / Note Off, accords et notes chevauchées.

## Fichiers

Dossier :

```text
~/CVP_Recordings/
```

Nommage :

```text
AAAA-MM-JJ_NNN.mid
```

Exemple :

```text
2026-09-24_001.mid
```

Le fichier est un Standard MIDI File type 0. La première RC enregistre le canal 1 et mémorise le tempo courant au moment de l'armement.

Une Note Off forcée, Sustain Off et All Notes Off sont ajoutés à la fin si nécessaire afin d'éviter les notes bloquées.

## Lecture

La lecture utilise `aplaymidi` et cherche automatiquement la sortie ALSA correspondant au périphérique MIDI courant.

Cette partie doit encore être validée matériellement sur le CVP de référence.

## Retour vocal

Les annonces courtes essentielles sont pré-générées :

- Enregistrement prêt ;
- Enregistrement annulé ;
- aucun enregistrement disponible ;
- lecture ;
- lecture arrêtée ;
- lecture terminée ;
- sortie MIDI introuvable ;
- erreur de sauvegarde.

L'annonce de sauvegarde avec date et numéro reste dynamique.

## Portail Web

Le dashboard affiche une section **Enregistrements MIDI** :

- liste des fichiers ;
- fichier sélectionné ;
- taille ;
- bouton **Sélectionner**.

Le morceau sélectionné dans le Web est celui que F15 court lit au repos.

## Samba

Nouveau partage :

```text
CVP_recordings
```

Mac / Linux :

```text
smb://<hostname>.local/CVP_recordings
smb://10.42.0.1/CVP_recordings
```

Windows :

```text
\\<hostname>.local\CVP_recordings
\\10.42.0.1\CVP_recordings
```

## Keyboard map

La carte clavier 1.6.0-RC1 affiche F14/F15. F15 est clairement marquée **Dictaphone MIDI** avec le résumé appui court / appui long.

La carte conserve sa cible A4 paysage sur une page, à confirmer en aperçu d'impression après installation.

## Installation / upgrade

Le bouton **Mettre à jour depuis GitHub** doit sélectionner automatiquement :

```text
VERIFY_PACKAGE_160.py
cvp_access_installer/upgrade_1_6_0.sh
```

Installation manuelle équivalente :

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_160.py
sudo bash cvp_access_installer/upgrade_1_6_0.sh
```

## État de validation

Validé matériellement :

- F15 détectée ;
- capture Note On / Note Off canal 1 ;
- tap MIDI interne sans deuxième port d'entrée.

À valider sur le CVP :

- armement vocal F15 long ;
- annulation F15 court ;
- démarrage sur première note ;
- sauvegarde .mid ;
- nom daté ;
- sélection Web ;
- lecture via `aplaymidi` ;
- stop lecture ;
- partage Samba `CVP_recordings` ;
- non-régression des commandes SysEx pendant usage Recorder.


## Validation matérielle — F15 armement / annulation

Test réalisé le 25 septembre 2026 sur le Raspberry de référence avec CVP Access 1.6.0-RC1 :

```text
F15 long  -> « Enregistrement prêt »
F15 court -> « Enregistrement annulé »
```

Journal observé :

```text
Recorder : Enregistrement prêt.
Recorder : Enregistrement annulé.
```

Statut :

- F15 long -> « Enregistrement prêt » : VALIDÉ ;
- F15 court à l'état armé -> annulation : VALIDÉ ;
- aucun enregistrement vide ne doit être créé dans ce scénario.


## Validation matérielle — enregistrement et sauvegarde

Test réalisé le 25 septembre 2026 sur CVP Access 1.6.0-RC1.

Journal observé :

```text
Recorder : Enregistrement prêt.
Recorder : enregistrement démarré (tempo 100)
Recorder : Enregistrement du 25 septembre 2026, numéro 1, sauvegardé.
```

Statut :

- F15 long -> armement : VALIDÉ ;
- première Note On -> démarrage : VALIDÉ ;
- tempo lu au moment de l'armement (100 BPM) : VALIDÉ ;
- F15 court pendant enregistrement -> arrêt + sauvegarde : VALIDÉ ;
- annonce vocale datée + numéro : VALIDÉ ;
- existence et lecture du fichier .mid restent à vérifier explicitement.


## Retour immédiat à l'arrêt d'enregistrement

Retour d'usage du 25 septembre 2026 : l'annonce dynamique complète de sauvegarde est trop longue pour servir de confirmation instantanée après F15.

Comportement retenu :

```text
F15 court pendant enregistrement
-> lecture directe du WAV « Stop. »
-> écriture / fermeture du fichier MIDI
-> annonce « Enregistrement du …, numéro …, sauvegardé. »
```

Le WAV `recorder/stop.wav` est pré-généré et joué directement hors file d'attente afin de donner une confirmation perceptible immédiatement. La phrase longue de sauvegarde vient ensuite.

La keyboard-map 1.6 reflète désormais ce comportement avec « Stop + sauver » sur F15.
