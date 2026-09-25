# CVP Access 1.6.1-RC2

Date : 25 septembre 2026.

## Objet

Release candidate de consolidation du Dictaphone MIDI et de la maintenance
autonome. Cette RC2 reprend la base 1.6.1-RC1 et intègre les corrections
détectées pendant les tests réels sur le Raspberry atelier.

## Dictaphone MIDI

- F14 : morceau précédent ;
- F15 : lecture / stop / armement / enregistrement ;
- F16 : morceau suivant ;
- F14/F16 courts : glissandos SoX immédiats ;
- F14/F16 maintenus : annonce du morceau sans bip ;
- F15 lecture : démarrage MIDI sans annonce qui masque les premières notes ;
- arrêt d'enregistrement : « Stop » immédiat ;
- confirmation de sauvegarde assemblée depuis des WAV pré-générés dans le cas
  normal, sans attente Piper ;
- fichiers `AAAA-MM-JJ_NNN.mid`, avec suffixe quotidien extensible au-delà de
  999 ;
- navigation optimisée avec cache du catalogue ;
- cache du port `aplaymidi`, réinitialisé après erreur de lecture.

## Maintenance Web

- panneaux MIDI, Samba, Enregistrements MIDI, Périphériques, Connexion Wi-Fi,
  Doctor et journaux rétractables ;
- liste des enregistrements compacte et filtrable ;
- 100 fichiers récents affichés au maximum pour garder l'interface légère ;
- sélection courante toujours conservée dans la liste ;
- compteur total de fichiers et taille cumulée ;
- sélection Web partagée avec F14/F15/F16.

## Installation / mise à jour

Corrections importantes intégrées à RC2 :

- réparation des blocs de fin de `install.sh`, `update.sh` et
  `cvp_update_from_github` ;
- `VERIFY_PACKAGE_161.py` contrôle désormais la syntaxe Bash des scripts
  principaux avec `bash -n` ;
- absence d'interface Wi-Fi utilisable : avertissement uniquement. Le portail,
  les helpers et les services sont installés normalement ; seule la création ou
  modification du hotspot `CVP-ACCESS` est ignorée pour cette exécution ;
- `release.env` reste la source de vérité pour sélectionner frontend,
  vérificateur et upgrader.

## Validation déjà obtenue

Sur Raspberry atelier / Yamaha CVP-905 :

- F14 et F16 détectés ;
- navigation précédent/suivant validée ;
- cues montant/descendant validés ;
- maintien F14/F16 sans bip validé ;
- F15 armement / annulation validés ;
- démarrage de l'enregistrement sur première Note On validé ;
- tempo lu pendant l'armement ;
- sauvegarde MIDI validée ;
- fichier enregistré relu sur ordinateur.

## À valider avant version stable

- non-régression SysEx complète pendant l'usage du Dictaphone ;
- sortie MIDI après débranchement/rebranchement USB ;
- comportement de la date après démarrage prolongé hors réseau sans RTC.

La version de référence du dépôt est désormais **CVP Access 1.6.1-RC2**.
