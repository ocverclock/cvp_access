# CVP Access 1.6 — dictaphone MIDI accessible

État : **conception**, 24 septembre 2026.

La version 1.6 est prévue comme une évolution fonctionnelle majeure. Elle ne doit pas modifier le comportement validé de CVP Access 1.5.2 hors fonction dictaphone.

## Objectif

Ajouter un dictaphone MIDI utilisable par une personne non voyante avec un minimum de touches et un retour vocal systématique.

Le principe retenu pour la première version est volontairement simple :

- **une seule touche dédiée** pour armer, annuler, arrêter, sauvegarder, lire et arrêter la lecture ;
- démarrage réel de l'enregistrement au **premier événement musical** ;
- fichiers MIDI enregistrés dans un dossier dédié ;
- noms de fichiers contenant la date ;
- liste des enregistrements visible et sélectionnable depuis le portail Web ;
- accès au dossier depuis macOS/Linux/Windows via Samba.

## Touche unique — machine d'états

La touche dédiée retenue est **F15**.

F15 ne doit servir qu'au dictaphone MIDI dans le layout 1.6. Le comportement appui court / appui long décrit ci-dessous lui est exclusivement associé.

**Point technique :** le routeur clavier 1.5.2 ne déclare actuellement que F1 à F13. L'implémentation 1.6 devra donc ajouter explicitement F14/F15 au catalogue evdev et faire apparaître F15 sur la carte clavier avant d'activer le Recorder.

### Checkpoint matériel F15 — validé

Test réalisé sur le clavier Apple Extended USB connecté au Raspberry :

```text
KEY_F15 1
KEY_F15 2
KEY_F15 0
```

Interprétation :

- `1` = appui ;
- `2` = répétition automatique pendant maintien ;
- `0` = relâchement.

F15 est donc **VALIDÉE MATÉRIELLEMENT** comme touche exploitable pour le dictaphone. L'implémentation devra ignorer les événements `value=2` pour éviter les doubles commandes.

Le routeur commun accepte maintenant F14 et F15. La carte clavier affiche aussi F14/F15 ; tant que la 1.6 n'est pas activée, F15 porte la mention « Réservé dictaphone MIDI 1.6 ».

### État repos

Appui court :

```text
un morceau est sélectionné
-> lecture du morceau

aucun morceau n'existe / n'est sélectionné
-> annonce vocale explicite
```

Appui long :

```text
-> armement d'un nouvel enregistrement
-> annonce : « Enregistrement prêt. »
```

Le seuil proposé pour l'appui long est d'environ **1,2 seconde**. Le seuil doit rester configurable.

### État armé, rien n'a encore été joué

Le premier événement MIDI musical déclenche réellement l'enregistrement.

Appui court avant le premier événement :

```text
-> annulation de l'armement
-> annonce : « Enregistrement annulé. »
```

Aucun fichier vide n'est créé.

### État enregistrement en cours

Appui court :

```text
-> arrêt de l'enregistrement
-> fermeture propre du fichier MIDI
-> sauvegarde
-> le fichier sauvegardé devient la sélection courante
-> annonce de la sauvegarde
```

Exemple :

```text
« Enregistrement du 24 septembre 2026, numéro 3, sauvegardé. »
```

### État lecture en cours

Appui court :

```text
-> arrêt immédiat de la lecture
```

Un nouvel appui court au repos relit le morceau sélectionné depuis le début.

Un nouvel appui long permet de préparer un nouvel enregistrement.

### Appui long pendant une lecture

Comportement recommandé :

```text
-> arrêt propre de la lecture
-> armement d'un nouvel enregistrement
-> annonce « Enregistrement prêt. »
```

Il ne doit jamais supprimer ni écraser le morceau en cours.

## ESC reste réservé

`ESC` conserve exclusivement sa fonction actuelle :

```text
ESC -> annonce de relance -> redémarrage de CVP Access via systemd
```

Le dictaphone **ne doit jamais utiliser ESC** pour annuler un armement ou arrêter un enregistrement. Cela évite toute ambiguïté et tout redémarrage accidentel dans le flux dictaphone.

## Gestion technique de l'appui long

Le routeur clavier actuel déclenche les actions sur `EV_KEY value=1` et ignore les relâchements. Le dictaphone a besoin de distinguer appui court et appui long.

La touche dictaphone doit donc être interceptée avant le routage normal, avec les événements bruts evdev :

```text
KEY_DOWN
-> lancer un timer monotonic

touche toujours tenue après ~1,2 s
-> déclencher l'appui long une seule fois

KEY_UP avant le seuil
-> déclencher l'appui court

KEY_UP après un appui long déjà déclenché
-> aucune deuxième action

KEY_REPEAT
-> ignoré
```

Cette logique doit rester confinée au contrôleur du dictaphone afin de ne pas changer le comportement des autres touches CVP Access.

## Fichiers et nommage

Dossier proposé :

```text
/home/<utilisateur>/CVP_Recordings/
```

Format de nom proposé :

```text
AAAA-MM-JJ_NNN.mid
```

Exemples :

```text
2026-09-24_001.mid
2026-09-24_002.mid
2026-09-25_001.mid
```

Avantages :

- tri chronologique naturel dans Finder ;
- date visible et lisible par VoiceOver ;
- numéro simple dans la journée ;
- aucun nom arbitraire nécessaire pendant l'enregistrement ;
- absence d'écrasement : le prochain numéro libre est utilisé.

Une évolution ultérieure pourra permettre de renommer un morceau depuis le portail Web.

## Risque important : date et heure hors ligne

Le nom repose sur l'heure système du Raspberry. Chez un client sans réseau Internet, NTP ne garantit pas une date correcte après un arrêt prolongé.

Avant validation production, choisir au moins une solution fiable :

1. RTC matériel (solution la plus robuste pour un appareil autonome) ;
2. RTC intégré + batterie lorsque le modèle de Raspberry le permet ;
3. synchronisation de l'heure depuis le Mac via le portail Web comme solution complémentaire.

Ne pas présenter la date du fichier comme fiable tant que ce point n'est pas validé sur le Raspberry client.

## Portail Web — liste des morceaux

La 1.6 doit ajouter une section **Enregistrements MIDI**.

Première étape :

- liste des fichiers ;
- date ;
- numéro ;
- heure si disponible ;
- taille ;
- durée si facilement calculable ;
- morceau actuellement sélectionné ;
- bouton `Sélectionner`.

Évolution possible :

- Lecture ;
- Stop ;
- Renommer ;
- Télécharger ;
- Supprimer avec confirmation.

La sélection Web doit mettre à jour la même sélection courante que la touche physique.

## Samba — dossier dédié

Ajouter un troisième partage officiel :

```text
CVP_recordings -> /home/<utilisateur>/CVP_Recordings
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

Le dossier doit contenir uniquement les enregistrements utilisateur afin que VoiceOver ne mélange pas fichiers techniques et morceaux.

## Enregistrement MIDI — première portée

Première version fonctionnelle proposée :

```text
canal MIDI 1
-> enregistrement
-> fichier Standard MIDI File
-> lecture
```

L'architecture doit toutefois accepter une future extension aux 16 canaux.

## Architecture MIDI retenue

L'analyse du runtime 1.5.2 montre que `cvp_access_v1.4.1.py::midi_receiver()` lit déjà en permanence **le flux MIDI brut complet** via `amidi -d`.

Ce récepteur sait déjà distinguer :

- les SysEx Yamaha, envoyés vers `midi_queue` ;
- les messages MIDI de canal et le running status ;
- les Program Change utilisés pour détecter les changements de Style.

Il n'est donc **pas nécessaire ni souhaitable d'ouvrir une deuxième fois le port ALSA MIDI** pour le Recorder.

Architecture retenue pour 1.6 :

```text
interface MIDI physique
        |
        v
midi_receiver() unique
        |
        +--> SysEx Yamaha -> moteur CVP Access existant
        |
        +--> messages MIDI canal -> listener/tap Recorder
```

Le Recorder recevra une copie des messages canal complets depuis le récepteur déjà actif. En l'absence de listener Recorder, le comportement 1.5.2 doit rester strictement inchangé.

Le hook devra être léger et protégé : une exception du Recorder ne doit jamais arrêter `midi_receiver()`.

Checkpoint obligatoire avant l'enregistrement de fichiers :

```text
CVP Access actif
-> listener Recorder attaché au midi_receiver existant
-> Note On / Note Off reçus correctement
-> SysEx continue de fonctionner
-> aucune ouverture ALSA MIDI supplémentaire
```

Cette architecture supprime le principal risque d'exclusivité/concurrence du port MIDI.

## Module cible

Architecture proposée :

```text
cvp_recorder.py
  RecorderController
    - idle
    - armed
    - recording
    - playing

    - arm()
    - cancel_arm()
    - start_on_first_musical_event()
    - record_event()
    - stop_and_save()
    - select_recording()
    - play_selected()
    - stop_playback()
    - handle_short_press()
    - handle_long_press()
```

Le module doit rester indépendant du protocole Yamaha autant que possible.

## Priorités de réalisation

1. ajouter F15 au routeur clavier et à la carte clavier, puis valider la détection physique ;
2. ajouter un listener/tap interne au récepteur MIDI existant et valider Note On / Note Off sans perturber les SysEx ;
3. implémenter la machine d'états à une touche ;
4. enregistrer un fichier canal 1 ;
5. lecture / stop ;
6. nommage date + index et annonces vocales ;
7. partage `CVP_recordings` ;
8. liste et sélection sur le portail Web ;
9. validation avec VoiceOver sur le Mac du client ;
10. seulement ensuite envisager le multi-canal.


## Probe MIDI intégré — checkpoint suivant

Le runtime possède maintenant un tap de messages MIDI canal dans le récepteur permanent. Aucun second port ALSA n'est ouvert.

Un probe de développement, désactivé par défaut, permet de vérifier les Note On / Note Off du canal 1 :

```text
CVP_RECORDER_PROBE=1
```

Sortie attendue dans le journal :

```text
Recorder probe : actif sur canal MIDI 1
Recorder probe : CH1 NOTE_ON note=... velocity=...
Recorder probe : CH1 NOTE_OFF note=... velocity=...
```

Ce probe ne sauvegarde encore aucun fichier. Il sert uniquement à valider le chemin de capture avant d'activer la machine d'états et l'écriture SMF.


### Checkpoint capture MIDI canal 1 — validé matériellement

Test réalisé le 24 septembre 2026 sur le CVP de référence avec le runtime 1.5.2-RC1 et `CVP_RECORDER_PROBE=1`.

Résultat observé dans `journalctl -fu cvp-access.service` :

```text
Recorder probe : actif sur canal MIDI 1
Recorder probe : CH1 NOTE_ON note=60 velocity=58
Recorder probe : CH1 NOTE_ON note=62 velocity=73
Recorder probe : CH1 NOTE_OFF note=60 velocity=77
Recorder probe : CH1 NOTE_ON note=64 velocity=82
Recorder probe : CH1 NOTE_OFF note=62 velocity=68
...
```

Plusieurs Note On / Note Off successifs, accords et chevauchements ont été reçus correctement sur le canal 1.

**Statut : capture MIDI canal 1 VALIDÉE MATÉRIELLEMENT.**

Le prochain checkpoint reste la non-régression SysEx pendant que le tap Recorder est actif : lancer au moins une commande CVP Access qui fait une lecture/écriture Yamaha (par exemple annonce du tempo ou changement d'état d'une piste) et confirmer que le comportement reste normal.


### Navigation F14 / F16

- F14 : précédent, bip descendant immédiat ;
- F16 : suivant, bip montant immédiat ;
- maintien ~0,8 s : annonce du morceau sélectionné via fragments WAV, sans Piper dans le cas normal ;
- navigation cyclique ;
- sons générés automatiquement par SoX pendant installation / upgrade ;
- F14/F16 doivent encore être validées physiquement sur le clavier de référence, F15 étant déjà validée.
