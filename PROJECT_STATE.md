# CVP Access — état de référence du projet

Dernière consolidation : **24 septembre 2026**.

Version de référence : **CVP Access 1.5.1-RC3**.

Instrument de référence : **Yamaha CVP-905 firmware 1.03**.

## 1. Matériel principal

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
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
Source courante : cvp_access_1_5_1.py
Base 1.5.1      : cvp_access_1_5_1_base.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Speech mode     : hybrid
Voix            : fr_FR-siwis-medium
```

Architecture transitoire :

```text
cvp_access_1_5_1.py
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
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

L'upgrade :

- conserve les personnalisations ;
- migre les anciens Solo ALT officiels vers `SHIFT+...` ;
- ajoute M, L, RPAREN et les 16 Solo Maj si les combinaisons sont libres ;
- génère la map et les WAV ;
- lance le Doctor ;
- redémarre le service.

## 14. Vérification du paquet

`VERIFY_PACKAGE_151.py` compile le wrapper, la base, les moteurs historiques, les modules et les outils. Il vérifie notamment :

```text
M
L
RPAREN
SHIFT+A .. SHIFT+K
```

Il vérifie aussi que le layout officiel ne conserve plus d'ancien binding `ALT+... = song_track_solo:*`.

Résultat attendu :

```text
CVP Access 1.5.1 RC3 package: OK
```

## 15. Doctor — VALIDÉ APRÈS MIGRATION ALT -> MAJ

Le Doctor exécuté après migration du layout a confirmé :

```text
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC3
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           10 présents
OK    WAV mute Style            8 présents
OK    WAV Solo Song             16 présents
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
7. refaire un clone GitHub neuf + upgrade.

## 19. Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## 20. Checkpoint

**CVP Access 1.5.1-RC3, layout Solo Maj, installation et Solo matériellement validés sur CVP-905, est le point de référence au 12 septembre 2026.**
