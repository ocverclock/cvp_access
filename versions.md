# Historique des versions — CVP Access

## v1.0

- mute/unmute des 16 pistes Song ;
- lecture de l’état réel ;
- tempo ;
- transpose ;
- retour vocal.

## v1.1

- ajout du volume accompagnement avec Page Up / Page Down.

## v1.1.3

- contrôle du volume Style avec Page Up / Page Down ;
- GET réel avant modification ;
- vérification GET après SET ;
- correction du décalage de lecture ;
- protection mono-instance ;
- fermeture propre de `amidi` ;
- annonces vocales du volume Style.

## v1.2.1

- `& é " ' ( - è _` -> Rhythm 1, Rhythm 2, Bass, Chord 1, Chord 2, Pad, Phrase 1, Phrase 2 ;
- mute/unmute individuel des 8 parties Style avec retour vocal ;
- détection automatique du changement de Style ;
- resynchronisation des parties après changement de Style ;
- contrôle du volume Style ;
- lecture avant modification et vérification après SET ;
- protection contre plusieurs instances ;
- fermeture propre de la liaison MIDI ;
- fichier de verrouillage déplacé vers `~/.cache`.

## v1.4.1

- ajout du contrôle du lecteur Song ;
- `Espace` -> Play / Pause ;
- `Entrée` -> Stop ;
- `P` -> annonce mesure / temps ;
- lecture réelle de la position depuis le CVP ;
- validation des commandes Song par `GET -> SET -> GET` ;
- synthèse vocale modulaire mesure / nombre / temps ;
- correction du décodage Yamaha des valeurs multi-octets en 7 bits.

Cette version reste utilisée par la v1.5 comme moteur SysEx Yamaha validé.

## v1.5 — clavier configurable

- configuration clavier TOML ;
- catalogue fermé d’actions ;
- noms de touches AZERTY ;
- combinaisons SHIFT / ALT / ALTGR / META ;
- Caps Lock comme seconde couche ;
- support du clavier principal, navigation, pavé numérique et touches de fonction ;
- configuration client conservée lors des mises à jour ;
- validation de configuration avec `cvp_keyboard.py --check`.

## v1.5 RC2 — configuration et voix pilotées par TOML

- section `[speech]` ;
- modes `pregenerated`, `hybrid`, `runtime` ;
- `generation = configured` pour ne préparer que les annonces nécessaires ;
- cache des phrases générées à la demande ;
- worker Piper persistant ;
- choix de la voix et de `length_scale` depuis le TOML ;
- régénération des WAV si le profil Piper change.

## v1.5 RC3 — navigation, boucle, volumes et aide

Validation matérielle : Yamaha CVP-905 firmware 1.03.

### Song

- F3 : accès direct à une mesure ;
- flèches gauche/droite : mesure -1/+1 ;
- Maj + gauche/droite : mesure -5/+5 ;
- F4 : point A ;
- F5 : point B ;
- F6 : Loop A/B ;
- conservation automatique du métronome lors d’un déplacement vers l’arrière.

### Style

- F13 : Start / Stop ;
- protocole validé GET + SET :
  `06 00 03 01 | 00`, `00=STOP`, `01=START`.

### Volumes

- Song/MidiMaster :
  `0C 00 00 01 | 50`, plage 0..127 ;
- HOME / END : +1 / -1 ;
- Maj + HOME / END : +5 / -5 ;
- Main :
  `0C 00 00 01 | 00`, plage 0..127 ;
- INSERT / DELETE : +1 / -1 ;
- Maj + INSERT / DELETE : +5 / -5.

Les volumes utilisent un cache local de la dernière valeur confirmée et une vérification GET rapide avec fallback afin de réduire la latence.

### Retour vocal

- Piper déplacé hors de la boucle clavier principale ;
- synthèse/lecture dans un thread dédié ;
- les anciennes annonces de volume en attente deviennent obsolètes lorsqu’une valeur plus récente arrive ;
- `CTRL + touche affectée` annonce la fonction sans l’exécuter.

### Configuration et installation

- 53 affectations dans la configuration RC3 par défaut ;
- support F13 ;
- `cvp_song.py` installé explicitement avec la v1.5 ;
- `cvp_keyboard_map.py` installé lorsqu’il est présent ;
- génération de `keyboard-map.html` non bloquante ;
- générateur Piper mis à jour pour Style Start/Stop, volumes Song/Main et fonctions Song RC3 ;
- installateur et updater : version 0.3.2.

### Protocole documenté

Voir :

- `CVP905_PROTOCOL_CHECKPOINT_RC3.md` ;
- `RC3_NOTES.md`.

### Recherche suspendue

Le contrôle MIDI du Fingering Type / AI Full Keyboard n’a pas produit de candidat reproductible. La recherche est suspendue en attendant une approche Registration/Backup ou une autre méthode différentielle.
