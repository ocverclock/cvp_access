# CVP Access 1.6.1-RC1 — consolidation

Date : 25 septembre 2026.

## Objet

1.6.1-RC1 consolide les ajouts du dictaphone MIDI et de la maintenance Web sans
modifier le moteur Yamaha/SysEx validé.

La pile reste volontairement compatible :

```text
cvp_access_1_6_1.py
 -> cvp_access_1_5_2.py
 -> cvp_access_1_5_1_base.py
 -> cvp_access_v1.5.py
 -> cvp_access_v1.4.1.py
```

Cette pile est une dette technique assumée : elle évite un refactoring du
protocole Yamaha pendant la phase de validation client.

## Recorder consolidé

Touches réservées :

```text
F14 = morceau précédent
F15 = lecture / stop / armement / enregistrement
F16 = morceau suivant
```

Navigation :

- F14 court : sélection précédente + glissando descendant ;
- F16 court : sélection suivante + glissando montant ;
- maintien F14/F16 ~0,8 s : annonce de la sélection, sans bip ;
- sélection cyclique premier/dernier.

Enregistrement :

- F15 long : armement ;
- première Note On canal 1 : démarrage réel ;
- F15 court pendant enregistrement : « Stop » immédiat puis sauvegarde ;
- fichier : `AAAA-MM-JJ_NNN.mid` ;
- dossier : `~/CVP_Recordings/`.

Lecture :

- F15 court au repos : lecture immédiate sans phrase « Lecture » ;
- port ALSA de sortie mémorisé après la première résolution pour accélérer les
  relectures suivantes ;
- cache invalidé automatiquement si `aplaymidi` échoue.

## Retour sonore

Les deux cues de navigation sont générés automatiquement par SoX à
l'installation / mise à jour :

```text
previous.wav : 880 -> 600 Hz, ~90 ms
next.wav     : 600 -> 880 Hz, ~90 ms
```

Les nombres 0..150, les douze mois et « numéro » sont pré-générés pour annoncer
une sélection sans synthèse Piper dans le cas normal.

La politique complète est décrite dans
`docs/FEEDBACK_POLICY_1_6_1.md`.

## Portail Web

Consolidation de la page maintenance :

- panneaux MIDI, Samba, Enregistrements MIDI, Périphériques, Connexion Wi-Fi et
  Doctor rétractables ;
- liste MIDI compacte et scrollable ;
- filtre par nom ;
- nombre total de fichiers ;
- maximum de 100 fichiers récents affichés, avec ajout automatique du fichier
  sélectionné s'il est plus ancien ;
- sélection Web partagée avec F15.

## Release et mise à jour

Le fichier :

```text
cvp_access_installer/release.env
```

est la source de vérité pour la release courante :

```text
CVP_RELEASE_VERSION=1.6.1-RC1
CVP_RELEASE_FRONTEND=cvp_access_1_6_1.py
CVP_RELEASE_UPGRADER=upgrade_1_6_1.sh
CVP_RELEASE_VERIFIER=VERIFY_PACKAGE_161.py
```

Les installateurs et l'updater GitHub utilisent ce manifeste, avec fallback de
compatibilité pour les anciens clones.

## Doctor

Le Doctor 1.6.1 contrôle en plus :

- WAV Recorder fixes ;
- deux cues SoX ;
- douze mois + fragment « numéro » ;
- 151 nombres pré-générés (0..150) ;
- dossier `CVP_Recordings` lisible/inscriptible ;
- sélection courante ;
- nombre de fichiers MIDI ;
- présence de `aplaymidi` et `sox`.

## Validation matérielle déjà obtenue

Sur le Raspberry atelier / CVP-905 :

- F14/F16 détectés et changement de sélection validé ;
- glissandos précédent/suivant validés à l'usage ;
- F15 armement/annulation validés ;
- démarrage sur première note validé ;
- tempo 100 lu pendant le test ;
- sauvegarde MIDI validée ;
- fichier relu depuis ordinateur ;
- comportement long F14/F16 sans bip validé par retour utilisateur.

Restent notamment à surveiller avant une version stable :

- non-régression SysEx complète pendant l'usage Recorder ;
- robustesse de la sortie `aplaymidi` après débranchement/rebranchement USB ;
- date des fichiers lorsque le Raspberry démarre longtemps hors réseau sans RTC.
