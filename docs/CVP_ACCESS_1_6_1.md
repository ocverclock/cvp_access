# CVP Access 1.6.1-RC2 — consolidation

Date : 25 septembre 2026.

## Objet

1.6.1-RC2 consolide les ajouts du dictaphone MIDI et de la maintenance Web sans
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
CVP_RELEASE_VERSION=1.6.1-RC2
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


## Détection Wi-Fi dynamique

La maintenance ne suppose plus que l'interface s'appelle `wlan0`.

Ordre de sélection :

1. `CVP_WIFI_DEVICE` si explicitement défini ;
2. interface liée au profil `CVP-ACCESS` si elle existe encore ;
3. première interface Wi-Fi NetworkManager utilisable.

Cette logique est appliquée à l'installation maintenance, au fallback hotspot,
à l'assistant de connexion Wi-Fi et au portail Web. Elle couvre notamment les
adaptateurs USB nommés `wlx...`.

## Nommage des outils

`cvp_doctor.py` devient le nom canonique du diagnostic pour la release
courante. Le fichier historique `cvp_doctor_151.py` est conservé dans le dépôt
pour compatibilité avec les anciens vérificateurs, mais les nouveaux upgrades et
le portail utilisent le nom générique.


## Robustesse du nombre d'enregistrements

Le suffixe quotidien reste affiché avec au moins trois chiffres
(`001`, `002`, etc.) mais le parseur accepte désormais trois chiffres ou
plus. Au-delà de 999 enregistrements dans une même journée, le Recorder produit
donc `1000`, `1001`, etc. sans revenir à `1000` ni écraser un fichier.

Le Doctor indique également le nombre de fichiers MIDI, leur taille cumulée et
l'espace disque libre. La navigation F14/F16 conserve pendant deux secondes le
catalogue trié en mémoire afin que des centaines de fichiers n'imposent pas un
`glob + sort` à chaque pression ; les modifications externes par Samba sont
réévaluées périodiquement.


## Audit de consolidation

Revue globale effectuée avant validation terrain de 1.6.1-RC2.

### Cohérence des noms

Terminologie publique retenue :

- **Dictaphone MIDI** : fonction F14/F15/F16 ;
- **Enregistrements MIDI** : fichiers enregistrés, Web et Samba ;
- **Morceau** : fichier actuellement sélectionné ;
- **Guide vocal** : voix et signaux CVP Access ;
- **Recorder** : terme réservé au code, aux logs et aux noms internes.

### Politique voix / son / silence

Le comportement a été vérifié contre `docs/FEEDBACK_POLICY_1_6_1.md`.

Le chemin normal du Dictaphone n'attend plus Piper pour :

- F14/F16 court : cues SoX ;
- F14/F16 long : date + numéro depuis fragments WAV ;
- F15 armement / annulation : WAV fixe ;
- F15 arrêt enregistrement : « Stop » WAV direct ;
- confirmation de sauvegarde : fragments WAV « Enregistrement du » + jour + mois + « numéro » + index + « sauvegardé ».

Piper reste un fallback pour les valeurs hors banque ou les fichiers au nom non standard.

### Nombre de fichiers

Il n'existe pas de limite artificielle du nombre total d'enregistrements.

- le suffixe quotidien accepte trois chiffres ou plus ;
- aucun fichier n'est supprimé automatiquement ;
- la navigation garde un cache de catalogue de 2 s ;
- le portail affiche les 100 fichiers les plus récents et conserve toujours la sélection courante visible ;
- le portail indique désormais le nombre total et la taille cumulée ;
- le Doctor indique nombre de fichiers, taille cumulée et espace disque libre.

### Robustesse installation / mise à jour

L'audit a détecté et corrigé une corruption de structure dans les blocs de fallback de :

- `cvp_access_installer/install.sh` ;
- `cvp_access_installer/update.sh` ;
- `cvp_access_installer/tools/cvp_update_from_github`.

Le chemin normal utilisant `release.env` restait le modèle voulu, mais ces blocs auraient pu casser une installation ou un fallback.

`VERIFY_PACKAGE_161.py` exécute maintenant aussi `bash -n` sur les scripts shell principaux afin qu'une erreur de syntaxe de ce type bloque le paquet avant installation.


### Mise à jour sans interface Wi-Fi

Correction après validation terrain : l'absence temporaire ou permanente d'une
interface Wi-Fi utilisable ne doit jamais faire échouer une mise à jour CVP
Access.

`install_maintenance.sh` installe désormais le portail Web, les helpers et les
services même si aucun périphérique Wi-Fi n'est disponible. Dans ce cas, seule
la création/modification du hotspot `CVP-ACCESS` est ignorée pour cette
exécution. Le portail reste accessible par Ethernet/LAN et le service de
fallback pourra redétecter une interface Wi-Fi ultérieurement.
