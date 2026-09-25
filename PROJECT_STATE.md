# CVP Access — état de référence du projet

Dernière consolidation : **24 septembre 2026**.

Version de référence : **CVP Access 1.5.2-RC1**.

Instrument de référence : **Yamaha CVP-905 firmware 1.03**.

## 1. Matériel principal

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN : ProdipeMIDIlilo ou USB MIDI Interface
USB Audio du CVP
Clavier Apple Extended USB
Piper fr_FR-siwis-medium
```

Toute validation dite matérielle doit provenir du CVP-905 de référence ou être explicitement requalifiée. Les résultats Genos restent secondaires.

## 2. Runtime courant

```text
Repo            : ~/CVP_access
Runtime         : /opt/cvp-access
Entrée runtime  : /opt/cvp-access/cvp_access.py
Source courante : cvp_access_1_5_2.py
Base 1.5.1      : cvp_access_1_5_1_base.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Speech mode     : hybrid
Voix            : fr_FR-siwis-medium
```

Architecture transitoire :

```text
cvp_access_1_5_2.py
    -> cvp_access_1_5_1_base.py
        -> cvp_access_v1.5.py
            -> cvp_access_v1.4.1.py
```

Le wrapper courant ajoute les commandes globales et le Solo Song. La base conserve les correctifs Song, Piper, Voice Name, Guide Yamaha, métronome et les fonctions 1.5.1.

## 3. Layout clavier consolidé

### 3.1 Parties Style et clavier

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

Terminologie vocale Style :

```text
OFF -> « Mute Rythme 1 », « Mute Basse », etc.
ON  -> « Rythme 1 activé », « Basse activée », etc.
```

`RPAREN` n'est pas un toggle : il force les huit parties Style sur ON.

### 3.2 Pistes Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
L               = toutes les pistes Song ON
```

Les touches simples restent des toggles individuels ON/OFF.

### 3.3 Solo Song — modificateur Maj

Le Solo utilise **Maj**, pas Alt.

```text
Maj + A = Solo piste 1
Maj + Z = Solo piste 2
Maj + E = Solo piste 3
Maj + R = Solo piste 4
Maj + T = Solo piste 5
Maj + Y = Solo piste 6
Maj + U = Solo piste 7
Maj + I = Solo piste 8
Maj + Q = Solo piste 9
Maj + S = Solo piste 10
Maj + D = Solo piste 11
Maj + F = Solo piste 12
Maj + G = Solo piste 13
Maj + H = Solo piste 14
Maj + J = Solo piste 15
Maj + K = Solo piste 16
```

Affectations techniques :

```text
SHIFT+A .. SHIFT+K = song_track_solo:1 .. song_track_solo:16
```

Comportement :

1. la piste choisie est activée ;
2. les quinze autres sont coupées ;
3. les seize états sont relus ;
4. une seule annonce `Solo piste N` est prononcée.

`L` remet les seize pistes Song sur ON et sert de sortie rapide du Solo.

L'ancien profil `ALT+...` est migré automatiquement lors de l'upgrade : une ancienne affectation ALT n'est supprimée que si elle correspond exactement au Solo officiel. Les personnalisations différentes sont conservées.

**Validation matérielle :** le 12 septembre 2026, le comportement `Maj + piste = piste choisie ON, 15 autres OFF` a été confirmé sur le Yamaha CVP-905 firmware 1.03. Le Solo Song avec Maj est donc **VALIDÉ MATÉRIELLEMENT**.

### 3.4 Informations / accessibilité

```text
W  = annonce nom Style
X  = annonce nom Song
C  = annonce longueur Song
V  = Syncro Start ON/OFF
B  = Guide Yamaha ON/OFF
M  = mute/réactivation du guide vocal CVP Access
N  = annonce nom Voice Main
,  = annonce nom Voice Layer
;  = annonce nom Voice Left
F7 = Métronome ON/OFF
```

Important :

```text
Guide Yamaha (B) != guide vocal CVP Access (M)
```

M agit uniquement sur les annonces CVP Access : WAV + Piper. Il ne modifie ni le Guide Yamaha, ni le Song, ni le Style, ni le métronome, ni le son du clavier. Le niveau du guide vocal reste mémorisé.

### 3.5 Song navigation / transport

```text
Espace       = lecture / pause
Entrée       = stop
P            = position
← / →        = mesure -1 / +1
Maj + ← / →  = mesure -5 / +5
F3           = aller à une mesure
F4           = point A
F5           = point B
F6           = boucle A/B
```

### 3.6 Volumes

```text
↑ / ↓                  = Vol. guide vocal + / -
Page ↑ / Page ↓        = Style +1 / -1
Maj + Page ↑ / Page ↓  = Style +5 / -5
Origine / Fin          = Song +1 / -1
Maj + Origine / Fin    = Song +5 / -5
Inser / Suppr          = Main +1 / -1
Maj + Inser / Suppr    = Main +5 / -5
```

### 3.7 Aide CTRL

`CTRL + touche` annonce la fonction sans l'exécuter. Exemple : `CTRL + Maj + E` annonce l'aide du Solo piste 3 sans modifier les pistes.

La couche Caps Lock expérimentale de RC1 est abandonnée.

### 3.8 Démarrage vocal

Après initialisation du MIDI, du clavier USB et du moteur vocal, CVP Access annonce une seule fois :

```text
Dispositif Melody Music CVP Access opérationnel.
```

Le WAV `system/startup_ready.wav` est pré-généré pendant l'installation et contrôlé par le Doctor. L'annonce n'est pas émise si l'initialisation matérielle n'atteint pas l'état prêt.

`ESC` annonce synchroniquement `Relance du dispositif CVP Access.` via `system/restart_device.wav`, attend la fin de la lecture, puis quitte le processus afin que `systemd` le relance.

**Validation matérielle — 24 septembre 2026 :** installation sur Raspberry Pi neuf Debian 13 arm64, annonce `Dispositif Melody Music CVP Access opérationnel.` et séquence `ESC -> annonce de relance -> redémarrage systemd -> annonce opérationnel` confirmées en fonctionnement réel.

## 4. Speech / Piper

Configuration :

```toml
[speech]
mode = "hybrid"
generation = "configured"
cache = true
voice = "fr_FR-siwis-medium"
length_scale = 0.85
```

Ordre :

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> cache du résultat
```

Cache : `~/.cache/cvp-access/tts/`.

Piper est préchargé au démarrage et reste résident.

### 4.1 WAV pré-générés

Banque numérique destinée aux mesures : `0..150`.

Sont notamment pré-générés :

```text
états 1.5.1 ON/OFF
mutes des 8 parties Style
Solo piste 1..16
transport Song
fragments mesure / temps / boucle / longueur Song
```

Les WAV Solo ne dépendent pas du modificateur clavier : le passage Alt -> Maj ne nécessite pas de nouvelle synthèse de ces 16 fichiers.

### 4.2 Lecture audio sérialisée

L'ancien moteur interrompait brutalement `aplay` à chaque nouvelle annonce. Le frontend 1.5.1 laisse l'annonce active se terminer et les `replace_key` éliminent les annonces obsolètes avant lecture.

### 4.3 Mute du guide vocal

Le mute M est logiciel et s'applique à toute la sortie vocale CVP Access : WAV et Piper. À l'entrée en mute, une annonce en cours peut être interrompue pour obtenir le silence immédiatement. À la sortie, `Guide vocal activé` est annoncé.

## 5. Arrêt Piper propre — VALIDÉ MATÉRIELLEMENT

```text
SIGTERM / SIGINT
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt Piper
```

Validations : arrêt après préchargement et arrêt pendant preload sans SIGKILL.

## 6. Voice Name — VALIDÉ PARTIELLEMENT

Propriété : `02 00 01 01`.

Indexes :

```text
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

La table `cvp_voice_names.py` reste partielle. Une Voice inconnue doit utiliser le fallback numérique, jamais un nom supposé.

## 7. Song — protocole utile

```text
Nom/path      : 04 00 01 01 | 00
Play state    : 04 00 05 01 | 00
Position      : 04 00 0A 01 | 00
Loop A/B      : 04 00 0D 01 | 00
Longueur      : 04 00 1B 01 | 00
Tracks active : 0C 00 01 01 | 10..1F
Métronome     : 07 00 00 01 | 00
```

Le déplacement par mesure, F3, la boucle A/B, le transport et le Solo Song avec Maj ont été testés physiquement sur le CVP-905. Le métronome est restauré par CVP Access lorsqu'un transport ou une navigation le coupe alors qu'il était actif.

## 8. Style — protocole utile

```text
Nom/path/source : 06 00 00 01 | 00
Start/Stop      : 06 00 03 01 | 00
Sync Start      : 06 00 07 01 | 00
```

Commande globale des huit parties :

```text
F0 43 73 01 51 05 00 00 08 <8 états> F7
```

Ordre : `RHY1 RHY2 BASS CHD1 CHD2 PAD PHR1 PHR2`.

Le protocole Style ne fournit pas de GET validé pour ces huit états. Le cache est donc déterministe : tout ON au démarrage, remis à tout ON après changement de Style détecté et après la commande globale `RPAREN`.

## 9. Guide Yamaha

```text
04 03 00 01 | 00
```

GET/SET bool validé. Le mute du guide vocal CVP Access n'utilise aucune propriété Yamaha.

## 10. Registration Memory

Recall 1..8 validé :

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
XX = 00..07
```

Workarounds Registration validés :

```text
ACMP      : GPm07 payload[2]  00=OFF / 7F=ON
Fingering : GPm07 payload[8]  03=AI Fingered / 04=Fingered / 0C=AI Full Keyboard
```

## 11. Recherches directes clôturées

```text
ACMP direct
Fingering direct
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

## 12. Actions implémentées mais non attribuées par défaut

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights ON/OFF
```

## 13. Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_152.py
sudo bash cvp_access_installer/upgrade_1_5_2.sh
```

L'upgrade :

- conserve les personnalisations ;
- migre les anciens Solo ALT officiels vers `SHIFT+...` ;
- ajoute M, L, RPAREN et les 16 Solo Maj si les combinaisons sont libres ;
- génère la map et les WAV ;
- lance le Doctor ;
- redémarre le service.


## 13.1 Réseau de maintenance autonome — VALIDÉ SUR RASPBERRY

Le dispositif ne doit pas dépendre de la présence d'une box ou d'un Wi-Fi chez le client.

Comportement retenu :

```text
démarrage Raspberry
-> si Ethernet ou Wi-Fi normal est connecté : réseau normal prioritaire
-> CVP-ACCESS reste arrêté
-> si aucun réseau normal n'est disponible après ~30 s
-> activation automatique du point d'accès CVP-ACCESS
```

Configuration validée le 24 septembre 2026 :

```text
SSID          : CVP-ACCESS
mode          : access point
bande         : 2,4 GHz (bg)
IPv4          : shared
Raspberry AP  : 10.42.0.1/24
SSH           : pi@10.42.0.1
service       : cvp-wifi-fallback.service
script        : /usr/local/sbin/cvp-wifi-fallback
```

Le profil `CVP-ACCESS` ne doit pas s'autoconnecter directement : le service de fallback le démarre uniquement lorsqu'aucune connexion Ethernet ou Wi-Fi normale n'est active. Une connexion réseau normale reste prioritaire. Si le hotspot est actif puis qu'un réseau normal apparaît, le hotspot est arrêté. Sans interface Wi-Fi disponible, aucune tentative de hotspot n'est faite.

Validation réelle : Wi-Fi magasin coupé volontairement, apparition automatique de `CVP-ACCESS`, connexion au point d'accès et accès SSH à `10.42.0.1` confirmés.

### Interface Web de maintenance — implémentée

Objectif : exposer une page locale d'état et de configuration accessible sans Internet.

Fonctions implémentées :

- état du service CVP Access ;
- modèle/version runtime ;
- interface MIDI détectée et port ALSA courant ;
- périphériques USB détectés ;
- clavier USB détecté ;
- audio CVP détecté ;
- état de connexion au piano / dernier échange utile ;
- journaux récents filtrés ;
- redémarrage du service CVP Access ;
- affectation explicite d'un périphérique lorsqu'il y a plusieurs candidats ;
- diagnostic Doctor depuis l'interface ;
- accès à la carte clavier et à la configuration.

Accès cible :

```text
http://10.42.0.1
http://cvp-access.local
```

Le portail captif est implémenté via le dnsmasq de la connexion partagée NetworkManager, DNS wildcard et option DHCP 114. L'ouverture automatique dépend du système client et reste un confort : l'URL locale directe doit toujours fonctionner.

La sélection dynamique des périphériques doit suivre la règle : périphérique connu prioritaire, candidat unique accepté automatiquement, plusieurs candidats ambigus présentés dans l'interface Web plutôt que choisis au hasard.

### Implémentation dépôt — 24 septembre 2026

Les éléments suivants sont intégrés au dépôt :

```text
cvp_access_installer/install_maintenance.sh
cvp_access_installer/network/cvp-wifi-fallback
cvp_access_installer/systemd/cvp-wifi-fallback.service.in
cvp_access_installer/systemd/cvp-web.service.in
cvp_access_installer/tools/cvp_web.py
```

Le portail Web fonctionne sur le port HTTP 80 et accepte localhost, le hotspot `10.42.0.0/24` et les sous-réseaux IPv4 privés directement connectés au Raspberry (Ethernet ou Wi-Fi). Il expose un dashboard d'état, les interfaces MIDI disponibles, l'audio Yamaha, le clavier USB, les périphériques USB, les événements utiles, le Doctor, le redémarrage du service CVP Access et le redémarrage du Raspberry.

Une sélection MIDI faite dans le dashboard est écrite dans :

```text
/etc/cvp-access/hardware.toml
```

Le moteur historique `cvp_access_v1.4.1.py` lit cette préférence avant les règles automatiques. Le nom d'interface est mémorisé, jamais le numéro ALSA `hw:X,Y,Z`.

Le portail captif utilise le dnsmasq de la connexion partagée NetworkManager avec DNS wildcard vers `10.42.0.1` et l'option DHCP 114. Les endpoints usuels Apple/Android/Windows sont redirigés vers le dashboard. Cette ouverture automatique reste à valider sur les différents OS.

### Mise à jour GitHub depuis le portail

Le dashboard possède désormais le bouton **Mettre à jour depuis GitHub**.

Fonctionnement :

```text
confirmation utilisateur
-> service systemd transitoire cvp-access-github-update
-> refus si le dépôt contient des modifications locales
-> git pull --ff-only sous l'utilisateur CVP
-> VERIFY_PACKAGE_* le plus récent
-> upgrade_* le plus récent
-> installation et redémarrage des services
```

Le processus continue même lorsque `cvp-web.service` est redémarré par l'upgrade. Le portail affiche ensuite l'état et les dernières lignes du journal `/run/cvp-access-update.log`.

Fichier installé :

```text
/usr/local/sbin/cvp-update-from-github
```

### Authentification portail — temporairement suspendue

Pour faciliter les essais sur le Raspberry de référence, la protection par mot de passe des boutons du portail est suspendue par défaut :

```text
CVP_WEB_REQUIRE_AUTH=0
```

Les actions restent limitées aux réseaux locaux autorisés. Le code d'authentification est conservé et peut être réactivé avec `CVP_WEB_REQUIRE_AUTH=1` puis redémarrage de `cvp-web.service`.

### Accès Web et Samba — 1.5.2-RC1

Le dashboard et la carte clavier affichent les adresses de maintenance. Sur la page Web, elles sont cliquables pour les copier dans le presse-papiers.

```text
Web réseau normal : http://<hostname>.local
Web hotspot       : http://10.42.0.1

Mac / Linux :
smb://<hostname>.local/CVP_access
smb://<hostname>.local/CVP_config
smb://10.42.0.1/CVP_access
smb://10.42.0.1/CVP_config

Windows :
\\<hostname>.local\CVP_access
\\<hostname>.local\CVP_config
\\10.42.0.1\CVP_access
\\10.42.0.1\CVP_config
```

Partages Samba officiels :

```text
CVP_access -> dépôt/projet
CVP_config -> configuration client
```

Sur macOS, utiliser Finder → Aller → Se connecter au serveur (`Cmd + K`) avec `smb://...`. Sous Linux/GNOME/Zorin, utiliser aussi `smb://...`; le backend `gvfs-backends` peut être nécessaire.

La carte clavier conserve ces deux blocs en bas de page et reste formatée pour **une seule page A4 paysage**.


## 14. Vérification du paquet

`VERIFY_PACKAGE_152.py` compile le wrapper 1.5.2, la base 1.5.1, les moteurs historiques, les modules et les outils. Il vérifie notamment :

```text
M
L
RPAREN
SHIFT+A .. SHIFT+K
```

Il vérifie aussi que le layout officiel ne conserve plus d'ancien binding `ALT+... = song_track_solo:*`.

Résultat attendu :

```text
CVP Access 1.5.2 RC1 package: OK
```

## 15. Doctor — VALIDÉ APRÈS MIGRATION ALT -> MAJ

Le Doctor exécuté après migration du layout a confirmé :

```text
OK    Runtime 1.5.x             modules complets
OK    Version runtime           1.5.2-RC1
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           10 présents
OK    WAV mute Style            8 présents
OK    WAV Solo Song             16 présents
OK    WAV système               démarrage + relance présents
```

Les deux générateurs ont également confirmé que toutes les banques étaient déjà présentes :

```text
Generated: 0; already present: 863
Generated: 0; existing: 262
```

## 16. État de validation fonctionnelle

### Validé physiquement sur CVP-905

```text
navigation Song LEFT/RIGHT et ±5
F3 aller à une mesure
boucles A/B
Play/Pause
restauration métronome pendant transport
arrêt Piper propre
lecture de plusieurs noms de Voice
Maj + piste = Solo Song
installation complète sur Raspberry Pi neuf Debian 13 arm64
annonce vocale de démarrage « Dispositif Melody Music CVP Access opérationnel. »
ESC : annonce de relance, redémarrage du service, puis annonce « opérationnel »
```

### Implémenté mais test fonctionnel encore requis

```text
M       = mute/réactivation guide vocal
libellés Style « Mute ... »
L       = toutes pistes Song ON
) / °   = toutes parties Style ON
```

## 17. Sources de vérité

Ordre de priorité :

1. `PROJECT_STATE.md`
2. `AI_HANDOFF.md`
3. `docs/CVP_ACCESS_1_5_1.md`
4. `docs/KEY_ACTIONS_1_5_1.md`
5. `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md`
6. `CVP905_PROTOCOL_CHECKPOINT_RC4.md`
7. `docs/FUNCTION_CATALOG.md`
8. runtime et modules
9. anciens checkpoints uniquement comme historique

## 18. Prochaines étapes

1. tester physiquement M ;
2. tester les libellés Style `Mute ...` ;
3. tester L ;
4. tester `) / °` ;
5. si la latence vocale reste perceptible malgré les WAV complets, identifier les annonces encore dynamiques et mesurer la latence playback/Piper ;
6. compléter progressivement `cvp_voice_names.py` ;
7. valider l'installation automatique du fallback Wi-Fi et du portail Web sur le Raspberry de référence ;
8. valider l'ouverture automatique du portail captif sur iOS, Android et ordinateur ;
9. valider l'affectation MIDI persistante depuis le dashboard avec les deux interfaces supportées ;
10. maintenir le test d’installation depuis un Raspberry neuf lors des prochaines versions majeures.

## 19. Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## 20. Checkpoint

**CVP Access 1.5.1-RC3 est le point de référence au 24 septembre 2026 : installation sur Raspberry Pi neuf Debian 13 arm64, Solo Song et annonces système démarrage/relance matériellement validés avec le CVP-905 de référence.**


## 17. Projet 1.6 — dictaphone MIDI

Spécification de conception :

```text
docs/MIDI_RECORDER_1_6.md
```

Principes retenus :

- une seule touche physique dédiée ;
- appui long = armement d'un nouvel enregistrement ;
- premier événement musical = début réel de l'enregistrement ;
- appui court avant le premier événement = annulation de l'armement ;
- appui court pendant l'enregistrement = arrêt + sauvegarde ;
- appui court au repos = lecture du morceau sélectionné ;
- appui court pendant lecture = stop ;
- `ESC` reste exclusivement réservé à la relance de CVP Access ;
- première portée : canal MIDI 1 ;
- fichiers `AAAA-MM-JJ_NNN.mid` dans `~/CVP_Recordings/` ;
- futur partage Samba `CVP_recordings` ;
- liste et sélection des morceaux dans le portail Web ;
- validation VoiceOver/macOS obligatoire ;
- fiabilité de l'horloge hors ligne à traiter avant production.

La touche dictaphone retenue est **F15**. Test matériel validé sur l'Apple Extended USB : `KEY_F15 1 / 2 / 0`. Le routeur commun accepte désormais F14/F15 et la carte clavier les affiche ; F15 est marquée « Réservé dictaphone MIDI 1.6 » tant que la fonction n'est pas activée.

Architecture Recorder retenue : ne pas ouvrir un second port MIDI. Le `midi_receiver()` historique reçoit déjà le flux brut complet et parse les messages de canal. Un listener/tap interne protégé est maintenant présent ; le probe `CVP_RECORDER_PROBE=1` a été validé matériellement sur le CVP de référence : Note On / Note Off canal 1 correctement reçus, y compris notes chevauchées. Prochain checkpoint : confirmer l'absence de régression SysEx pendant que le tap est actif.


## 21. CVP Access 1.6.0-RC1 — implémenté, validation matérielle en cours

Frontend :

```text
cvp_access_1_6_0.py
```

Architecture :

```text
cvp_access_1_6_0.py
 -> cvp_access_1_5_2.py
 -> cvp_access_1_5_1_base.py
 -> cvp_access_v1.5.py
 -> cvp_access_v1.4.1.py
```

Recorder :

- F15 court/long ;
- CTRL+F15 = aide sans exécution ;
- canal MIDI 1 ;
- démarrage à la première Note On ;
- fichiers `AAAA-MM-JJ_NNN.mid` ;
- dossier `~/CVP_Recordings/` ;
- lecture prévue via `aplaymidi` ;
- sélection persistante partagée avec le portail Web ;
- partage Samba `CVP_recordings` ;
- keyboard map 1.6 avec F15 ;
- annonces Recorder essentielles pré-générées.

Validé matériellement avant RC1 :

- F15 `KEY_F15 1/2/0` ;
- Note On / Note Off canal 1 via le tap interne.

À valider maintenant : armement, sauvegarde réelle, lecture, sélection Web/Samba et non-régression SysEx.

Upgrade :

```bash
python3 VERIFY_PACKAGE_160.py
sudo bash cvp_access_installer/upgrade_1_6_0.sh
```


Checkpoint Recorder 25 septembre 2026 : armement F15 long et annulation F15 court validés matériellement sur 1.6.0-RC1. Journal : « Recorder : Enregistrement prêt. » puis « Recorder : Enregistrement annulé. » Prochain test : première Note On -> enregistrement -> F15 court -> sauvegarde .mid datée.


Checkpoint Recorder 25 septembre 2026 : première Note On -> démarrage et F15 court -> sauvegarde validés matériellement sur 1.6.0-RC1. Tempo lu : 100 BPM. Annonce : « Enregistrement du 25 septembre 2026, numéro 1, sauvegardé. » Prochain test : vérifier le fichier généré puis lecture/stop via F15.


Amélioration ergonomique Recorder 25 septembre 2026 : ajout d'un « Stop. » pré-généré en lecture directe au F15 court pendant l'enregistrement, avant l'écriture disque et l'annonce dynamique « Enregistrement du … sauvegardé ». Objectif : supprimer la sensation de latence. Keyboard map mise à jour en « Stop + sauver ».


Ergonomie Recorder 25 septembre 2026 : relecture F15 sans annonce « Lecture ». Le fichier MIDI démarre immédiatement pour éviter toute latence ou masquage des premières notes.


Ergonomie portail 25 septembre 2026 : liste MIDI Web compactée en tableau scrollable avec filtre, compteur et sélection mise en évidence pour éviter l'allongement de la page quand le nombre de fichiers augmente.


Ergonomie portail 25 septembre 2026 : les panneaux Samba, MIDI, Enregistrements MIDI, Périphériques et Connexion Wi-Fi sont rétractables afin de garder la page de maintenance compacte. Ils sont repliés par défaut et restent entièrement accessibles via les éléments HTML `details/summary`.


Navigation Recorder F14/F16 implémentée : F14 précédent avec glissando descendant 90 ms, F16 suivant avec glissando montant 90 ms, déclenchement dès KEY_DOWN. Maintien ~0,8 s -> annonce « jour mois, numéro N » assemblée depuis WAV pré-générés, sans Piper dans le cas normal. Les cues sont produits automatiquement par SoX à l'installation/update via `generate_recorder_cues.sh`. Keyboard map étendue jusqu'à F16. Validation matérielle F14/F16 encore à faire.


Checkpoint 25 septembre 2026 : F14/F16 physiquement validés sur le clavier de référence. Les changements de sélection apparaissent correctement dans le journal (`2026-09-25_002.mid` puis `2026-09-25_003.mid`) et les glissandos précédent/suivant sont jugés très réactifs et clairement distincts.
