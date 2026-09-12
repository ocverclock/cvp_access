# CVP Access — Analyse du mode « dictaphone MIDI »

Date de réflexion : 12 septembre 2026

## Objectif

Ajouter à CVP Access une fonction de **dictaphone MIDI accessible**, utilisable sans écran par un musicien non-voyant.

Le Raspberry Pi doit pouvoir :

- recevoir le MIDI provenant du CVP ;
- enregistrer une interprétation dans un fichier `.mid` ;
- relire les enregistrements vers le CVP ;
- permettre de retrouver facilement un ancien enregistrement ;
- fournir une navigation entièrement vocale ;
- rendre les fichiers accessibles depuis un ordinateur connecté au réseau.

Cette fonction **n'est pas encore implémentée** dans CVP Access.

## Principe technique envisagé

Premier prototype avec les outils ALSA :

- `arecordmidi` pour enregistrer le flux MIDI ;
- `aplaymidi` pour relire un fichier MIDI vers le CVP.

Le moteur MIDI doit être validé indépendamment de l'interface accessible avant intégration dans CVP Access.

### Phase 1 — moteur MIDI

1. Identifier le port MIDI USB du CVP.
2. Capturer un flux MIDI avec `arecordmidi`.
3. Générer un fichier `.mid` valide.
4. Relire ce fichier avec `aplaymidi` vers le CVP.
5. Vérifier la fidélité de la lecture.
6. Vérifier la gestion du tempo.

Dans un premier temps, on cherche surtout un enregistrement MIDI simple et fiable. La question du multicanal, des styles, Program Change, SysEx, etc. sera étudiée ensuite.

## Tempo

Objectif : le **CVP reste maître du tempo**.

Le fichier MIDI doit conserver le tempo utilisé lors de l'enregistrement afin que la lecture reste cohérente avec le métronome et l'interprétation originale.

À vérifier expérimentalement : messages MIDI réellement transmis par le CVP et meilleure méthode pour inscrire/conserver le tempo dans le fichier MIDI.

## Ergonomie d'enregistrement

### Armer l'enregistrement

Un **appui long sur la touche REC** arme l'enregistreur.

Annonce vocale :

> « En attente d'enregistrement »

L'enregistrement ne doit idéalement commencer qu'à la première activité MIDI utile, afin de ne pas créer un silence arbitraire avant le morceau et de faciliter le jeu avec le métronome.

### Annuler avant de jouer

Lorsque l'enregistreur est armé mais que l'enregistrement n'a pas commencé :

- `Échap` annule l'opération ;
- dans cet état, `Échap` ne doit déclencher aucune autre fonction générale de CVP Access.

Annonce :

> « Annulation d'enregistrement »

### Arrêter et sauvegarder

Pendant l'enregistrement, un nouvel appui sur REC arrête et sauvegarde le fichier.

Annonce :

> « Enregistrement 28 sauvegardé »

La date n'a pas besoin d'être annoncée vocalement à ce moment : le numéro est le repère principal de l'utilisateur.

## Numérotation et fichiers

Chaque enregistrement reçoit un numéro **séquentiel permanent**.

Exemple :

`REC_0028_2026-09-12_19-24.mid`

Le numéro est placé au début du nom afin que le tri alphabétique conserve naturellement l'ordre des enregistrements.

Un numéro supprimé **n'est jamais réutilisé**.

Exemple : si 25 a été supprimé, la navigation peut donner :

- 28
- 27
- 26
- 24

La navigation doit parcourir les fichiers réellement présents, sans inventer ni renuméroter les trous.

## Retrouver un enregistrement

Deux méthodes complémentaires sont prévues.

### Navigation précédent / suivant

Des touches dédiées permettent de charger l'enregistrement précédent ou suivant existant.

Exemples d'annonces :

> « Enregistrement 27 »

> « Enregistrement 26 »

La sélection ne lance pas automatiquement la lecture.

### Accès direct par numéro

Une touche dédiée active la fonction **Aller à l'enregistrement**.

Annonce :

> « Saisissez le numéro de l'enregistrement »

L'utilisateur saisit par exemple `12`, puis `Entrée`.

Annonce :

> « Enregistrement 12 »

Le morceau est alors sélectionné et prêt à être lu.

Cette fonction est considérée comme essentielle : le numéro annoncé lors de la sauvegarde devient le repère durable de l'utilisateur.

## Lecture

Une touche dédiée **Play / Stop ou Play / Pause** doit permettre de lire l'enregistrement actuellement sélectionné.

Le comportement précis Play / Pause / Stop / retour au début reste à figer lors de la conception détaillée.

Il est préférable d'avoir une touche Play dédiée plutôt qu'une combinaison `Maj + touche` : l'utilisation tactile doit rester simple et fiable.

## Déplacement dans un morceau

Deux touches situées de part et d'autre de la touche de rappel/sélection sont envisagées pour :

- reculer dans le morceau ;
- avancer dans le morceau.

Première hypothèse : saut de `-5 s` / `+5 s`.

À étudier : en MIDI, une recherche temporelle correcte implique de restaurer l'état musical nécessaire au point de reprise (tempo, contrôleurs, Program Change, etc.). Il ne faut donc pas considérer ce point comme résolu tant que le prototype n'a pas été testé.

Une annonce de position temporelle pourra être ajoutée, par exemple :

> « 1 minute 25 »

## Cartographie clavier envisagée

Le clavier final sera un **clavier PC USB standard**, pas nécessairement le clavier Apple utilisé pendant le développement initial.

Une zone physique séparée doit être réservée au dictaphone MIDI.

Le bloc de six touches d'un clavier PC standard est une piste intéressante :

- `Insert`
- `Home`
- `Page Up`
- `Delete`
- `End`
- `Page Down`

Il est bien regroupé et facilement identifiable au toucher.

La cartographie définitive n'est **pas encore figée**. Avant toute implémentation, il faut auditer les touches déjà utilisées dans CVP Access et réserver officiellement le bloc dictaphone.

Fonctions nécessaires au minimum :

- REC / armement / arrêt ;
- précédent ;
- suivant ;
- Play ;
- aller directement à un numéro ;
- recul temporel ;
- avance temporelle.

Il faudra donc vérifier si le bloc choisi suffit ou si une touche supplémentaire facilement identifiable est nécessaire.

## Accès réseau aux fichiers

Les fichiers MIDI doivent être stockés dans un dossier dédié du Raspberry Pi, par exemple :

`Enregistrements_CVP/`

Ce dossier pourra être partagé sur le réseau afin que le client puisse, depuis son ordinateur adapté :

- consulter les fichiers ;
- les copier ;
- les archiver ;
- éventuellement les renommer ou les exploiter dans un logiciel MIDI.

Le protocole de partage (probablement SMB/Samba) sera choisi lors de l'implémentation.

## Machine à états à prévoir

L'implémentation ne doit pas être une accumulation de raccourcis clavier. Le dictaphone doit avoir une petite machine à états explicite, par exemple :

- `IDLE` — utilisation normale ;
- `REC_ARMED` — en attente de la première donnée MIDI ;
- `RECORDING` — capture active ;
- `BROWSE` — sélection d'un enregistrement ;
- `ENTER_NUMBER` — saisie d'un numéro ;
- `PLAYING` — lecture ;
- éventuellement `PAUSED`.

Cela permettra notamment de donner à `Échap` un comportement contextuel sûr.

## Ordre de développement proposé

1. **Ne pas commencer par l'interface clavier.**
2. Tester `arecordmidi` avec le CVP réel.
3. Tester `aplaymidi` vers le CVP.
4. Vérifier tempo et fidélité d'une piste simple.
5. Construire le gestionnaire de fichiers et la numérotation.
6. Construire la machine à états.
7. Ajouter les annonces vocales.
8. Auditer le mapping clavier existant.
9. Affecter les touches du dictaphone.
10. Tester l'ensemble sans écran.
11. Ensuite seulement étudier l'enregistrement complet : plusieurs canaux, styles, changements de sons, contrôleurs et SysEx.

## Point important pour la prochaine séance

Ne pas confondre deux chantiers :

**A. Moteur MIDI** : savoir enregistrer et relire correctement un `.mid` sur le Raspberry Pi.

**B. Interface accessible** : rendre ce moteur extrêmement simple à utiliser sans écran grâce aux touches, aux numéros et aux annonces vocales.

La prochaine séance doit commencer par la validation du moteur MIDI, puis figer l'ergonomie et la cartographie avant de modifier le code principal de CVP Access.
