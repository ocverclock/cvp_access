# CVP Access — état de référence du projet

Dernière consolidation : **12 septembre 2026**.

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

Toutes les validations CVP revendiquées comme matérielles doivent provenir de ce CVP-905 ou être explicitement requalifiées. Les résultats Genos restent secondaires et ne deviennent jamais automatiquement des validations CVP.

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

Le wrapper courant ajoute les commandes globales et le Solo Song. La base conserve les correctifs Song, Piper, Voice Name, Guide Yamaha, métronome et autres fonctions 1.5.1.

Ne pas supprimer les moteurs historiques avant refactorisation complète.

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

Nom interne de la touche `) / °` :

```text
RPAREN
```

Les annonces des parties Style doivent rester distinctes des pistes Song :

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

Les touches simples A..K restent des toggles individuels ON/OFF.

### 3.3 Solo Song

```text
ALT + A = Solo piste 1
ALT + Z = Solo piste 2
ALT + E = Solo piste 3
ALT + R = Solo piste 4
ALT + T = Solo piste 5
ALT + Y = Solo piste 6
ALT + U = Solo piste 7
ALT + I = Solo piste 8
ALT + Q = Solo piste 9
ALT + S = Solo piste 10
ALT + D = Solo piste 11
ALT + F = Solo piste 12
ALT + G = Solo piste 13
ALT + H = Solo piste 14
ALT + J = Solo piste 15
ALT + K = Solo piste 16
```

Comportement :

1. la piste choisie est activée ;
2. les quinze autres sont coupées ;
3. les seize états sont relus ;
4. une seule annonce `Solo piste N` est prononcée.

`L` remet les seize pistes Song sur ON et sert de sortie rapide du Solo.

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

M agit uniquement sur les annonces produites par CVP Access : WAV + Piper. Il ne modifie ni le Guide Yamaha, ni le Song, ni le Style, ni le métronome, ni le son du clavier. Le niveau du guide vocal reste mémorisé pendant le mute.

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

```text
CTRL + touche
```

annonce la fonction sans l'exécuter. La couche Caps Lock expérimentale de RC1 est abandonnée.

## 4. Speech / Piper

Configuration de référence :

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

Cache :

```text
~/.cache/cvp-access/tts/
```

Piper est préchargé au démarrage et reste résident.

### 4.1 WAV pré-générés

Les annonces prévisibles doivent utiliser des WAV plutôt que Piper dynamique.

Banque numérique destinée aux mesures :

```text
0..150
```

Les annonces suivantes sont notamment pré-générées :

```text
états 1.5.1 ON/OFF
mutes des 8 parties Style
Solo piste 1..16
transport Song
fragments de mesure / temps / boucle / longueur Song
```

### 4.2 Lecture audio sérialisée

L'ancien moteur interrompait brutalement `aplay` à chaque nouvelle annonce, ce qui pouvait produire des coupures/craquements. Le frontend 1.5.1 sérialise désormais la lecture. Les `replace_key` éliminent les annonces devenues obsolètes avant lecture.

### 4.3 Mute du guide vocal

Le mute M est logiciel et s'applique à toute la sortie vocale CVP Access : WAV et Piper. À l'entrée en mute, une annonce en cours peut être interrompue pour obtenir le silence immédiatement. À la sortie, `Guide vocal activé` est annoncé.

## 5. Arrêt Piper propre — VALIDÉ MATÉRIELLEMENT

Le problème SIGKILL de RC2 est corrigé.

```text
SIGTERM / SIGINT
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt Piper
```

Validations :

```text
arrêt après préchargement : aucun SIGKILL
arrêt pendant preload     : aucun SIGKILL
```

## 6. Voice Name — VALIDÉ PARTIELLEMENT

Propriété :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Décodage :

```python
packed = (b0 << 21) | (b1 << 14) | (b2 << 7) | b3
msb = (packed >> 16) & 0xFF
lsb = (packed >> 8) & 0xFF
program = (packed & 0xFF) + 1
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

Le déplacement par mesure, F3, la boucle A/B et le transport ont été testés physiquement sur le CVP-905.

La navigation arrière peut couper le métronome côté CVP ; CVP Access le restaure lorsqu'il était actif. Même principe appliqué au transport Play/Pause.

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

Ordre :

```text
RHY1 RHY2 BASS CHD1 CHD2 PAD PHR1 PHR2
```

Le protocole Style ne fournit pas de GET validé pour ces huit états. Le cache est donc déterministe : tout ON au démarrage, remis à tout ON après changement de Style détecté et après la commande globale `RPAREN`.

Section Control validé :

```text
F0 43 7E 00 ss 7F F7

00..02 = Intro 1..3
08..0B = Main A..D
10..13 = Fill A..D
18     = Break
20..22 = Ending 1..3
```

## 9. Guide Yamaha

```text
04 03 00 01 | 00
```

GET/SET bool validé.

Le mute du guide vocal CVP Access n'utilise aucune propriété Yamaha.

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

Ne pas relancer sans nouvelle preuve indépendante :

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

Elles doivent rester visibles dans la map sous `Actions disponibles mais non attribuées`.

## 13. Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

L'upgrade conserve les personnalisations et ajoute M, L, RPAREN et les 16 ALT+touches uniquement si les combinaisons sont libres.

## 14. Vérification du paquet

`VERIFY_PACKAGE_151.py` compile désormais :

```text
wrapper cvp_access_1_5_1.py
base cvp_access_1_5_1_base.py
moteurs historiques
modules Song / Speech / MIDI / Voice / Style
outils de génération et Doctor
```

Il vérifie aussi le layout courant, notamment :

```text
M
L
RPAREN
ALT+A .. ALT+K
```

Résultat attendu :

```text
CVP Access 1.5.1 RC3 package: OK
```

## 15. Doctor — VALIDATION INSTALLATION DU 12 SEPTEMBRE 2026

Le Doctor exécuté sur le Raspberry de référence après déploiement du layout courant a renvoyé :

```text
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC3
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           10 présents
OK    WAV mute Style            8 présents
OK    WAV Solo Song             16 présents
```

Conclusion : **runtime, layout et banques WAV du layout courant sont cohérents sur l'installation de référence.**

Cette validation de paquet/install ne doit pas être confondue avec une validation fonctionnelle matérielle de chaque raccourci.

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
```

### Implémenté + installé + Doctor OK, mais test fonctionnel encore requis

```text
M       = mute/réactivation guide vocal
libellés Style « Mute ... »
L       = toutes pistes Song ON
) / °   = toutes parties Style ON
ALT+... = Solo Song
```

Ne marquer ces fonctions `VALIDÉES MATÉRIELLEMENT` qu'après confirmation explicite sur le CVP-905.

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

## 18. Prochaines étapes raisonnables

1. tester physiquement M ;
2. tester les libellés Style `Mute ...` ;
3. tester L ;
4. tester `) / °` ;
5. tester ALT + piste Song ;
6. si la latence vocale reste perceptible malgré les WAV complets, identifier les annonces encore dynamiques et mesurer la latence playback/Piper ;
7. compléter progressivement la table `cvp_voice_names.py` ;
8. refaire un clone GitHub neuf + upgrade ;
9. tester plus tard une installation réellement vierge.

## 19. Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## 20. Checkpoint

**CVP Access 1.5.1-RC3, layout M/L/RPAREN/Solo et banques WAV associées sont consolidés sur `main` au 12 septembre 2026.**
