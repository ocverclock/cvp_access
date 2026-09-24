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

La touche n'est pas encore figée. **F8 est le candidat principal** car elle est actuellement libre dans le layout officiel et se trouve à l'extrémité du groupe F5–F8, ce qui peut faciliter le repérage tactile. La validation ergonomique avec l'utilisateur reste nécessaire avant de rendre ce choix définitif.

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

## Risque technique à valider avant codage complet

CVP Access utilise déjà l'interface MIDI pour les échanges SysEx avec le piano. Il faut confirmer qu'un deuxième lecteur peut écouter les événements MIDI musicaux sans prendre le port en exclusivité ni perturber le contrôle SysEx.

Checkpoint obligatoire avant implémentation :

```text
CVP Access actif
+ écoute MIDI musicale parallèle
-> aucune perte de SysEx
-> aucune coupure de CVP Access
-> notes reçues correctement
```

Si le périphérique ne permet pas l'ouverture concurrente, il faudra centraliser l'entrée MIDI dans un seul service et distribuer les messages au moteur CVP Access et au Recorder, plutôt que d'ouvrir le même port deux fois.

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

1. valider la touche physique et l'ergonomie ;
2. tester l'écoute MIDI parallèle sans perturber CVP Access ;
3. implémenter la machine d'états à une touche ;
4. enregistrer un fichier canal 1 ;
5. lecture / stop ;
6. nommage date + index et annonces vocales ;
7. partage `CVP_recordings` ;
8. liste et sélection sur le portail Web ;
9. validation avec VoiceOver sur le Mac du client ;
10. seulement ensuite envisager le multi-canal.
