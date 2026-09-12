# CVP Access 1.5.1 — référence technique consolidée

Dernière consolidation : **12 septembre 2026**.

Version de référence : **CVP Access 1.5.1-RC3**.

Instrument de référence : **Yamaha CVP-905 firmware 1.03**.

## 1. Matériel de référence

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP
Clavier Apple Extended USB
Piper fr_FR-siwis-medium
```

Les résultats Genos restent secondaires et ne constituent jamais une validation CVP sans test physique sur CVP-905.

## 2. Architecture runtime

Runtime installé :

```text
/opt/cvp-access/cvp_access.py
```

Source courante :

```text
cvp_access_1_5_1.py
```

Architecture transitoire :

```text
cvp_access_1_5_1.py
    -> cvp_access_1_5_1_base.py
        -> cvp_access_v1.5.py
            -> cvp_access_v1.4.1.py
```

Le wrapper `cvp_access_1_5_1.py` ajoute les commandes globales et le Solo Song. La base `cvp_access_1_5_1_base.py` conserve les fonctions 1.5.1 précédentes : Song, Style, Voice Name, Guide Yamaha, métronome, Piper et accessibilité.

Modules principaux :

```text
cvp_keyboard.py
cvp_song_151.py
cvp_speech.py
cvp_speech_151.py
cvp_piper_worker.py
cvp_midi.py
cvp_yamaha.py
cvp_style.py
cvp_voice.py
cvp_voice_names.py
cvp_registration.py
```

Ne pas supprimer les moteurs historiques avant refactorisation complète.

## 3. Layout clavier de référence

### Parties Style et clavier

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

Le nom interne de la touche `) / °`, située immédiatement à droite du `0`, est :

```text
RPAREN
```

Le raccourci `RPAREN` n'est pas un toggle : il force toujours les huit parties Style sur ON.

Terminologie vocale des parties Style :

```text
OFF -> « Mute Rythme 1 », « Mute Basse », etc.
ON  -> « Rythme 1 activé », « Basse activée », etc.
```

### Pistes Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
L               = toutes les pistes Song ON
```

Les touches simples restent des toggles ON/OFF individuels.

### Solo Song

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

Le Solo :

1. active d'abord la piste sélectionnée ;
2. coupe ensuite les 15 autres ;
3. relit les 16 états ;
4. annonce une seule fois `Solo piste N`.

`L` sert de sortie rapide du Solo en remettant les 16 pistes sur ON.

### Informations et accessibilité

```text
W  = nom Style
X  = nom Song
C  = longueur Song
V  = Syncro Start ON/OFF
B  = Guide Yamaha ON/OFF
M  = mute/réactivation du guide vocal CVP Access
N  = nom Voice Main
,  = nom Voice Layer
;  = nom Voice Left
F7 = Métronome ON/OFF
```

Important :

```text
Guide Yamaha (B) != guide vocal CVP Access (M)
```

M coupe uniquement les annonces produites par CVP Access : WAV pré-générés et Piper. Il ne modifie ni le Guide Yamaha, ni le Song, ni le Style, ni le métronome, ni le son du clavier. Le volume du guide vocal reste mémorisé.

### Song transport / navigation

```text
Espace       = Play / Pause
Entrée       = Stop
P            = position
← / →        = mesure -1 / +1
Maj + ← / →  = mesure -5 / +5
F3           = aller à une mesure
F4           = point A
F5           = point B
F6           = boucle A/B
```

### Volumes

```text
↑ / ↓                  = Vol. guide vocal + / -
Page ↑ / Page ↓        = Style +1 / -1
Maj + Page ↑ / Page ↓  = Style +5 / -5
Origine / Fin          = Song +1 / -1
Maj + Origine / Fin    = Song +5 / -5
Inser / Suppr          = Main +1 / -1
Maj + Inser / Suppr    = Main +5 / -5
```

### Aide CTRL

```text
CTRL + touche
```

annonce la fonction sans exécuter l'action.

Exemple :

```text
CTRL + ALT + E
-> annonce l'aide du Solo piste 3
-> ne modifie aucune piste
```

La couche Caps Lock expérimentale de RC1 est abandonnée.

## 4. Synthèse vocale

Configuration de référence :

```toml
[speech]
mode = "hybrid"
generation = "configured"
cache = true
voice = "fr_FR-siwis-medium"
length_scale = 0.85
```

Ordre de résolution :

```text
WAV pré-généré
-> cache dynamique
-> synthèse Piper
-> stockage cache
```

Cache dynamique :

```text
~/.cache/cvp-access/tts/
```

Piper est préchargé au démarrage et reste résident.

### WAV pré-générés

Les annonces prévisibles doivent éviter Piper dynamique autant que possible.

Sont notamment pré-générés :

- états ON/OFF du guide vocal et des booléens 1.5.1 ;
- mutes des huit parties Style ;
- `Solo piste 1` à `Solo piste 16` ;
- transports Song ;
- nombres et fragments utilisés pour les mesures / positions / boucles.

La banque de nombres destinée aux mesures est limitée à :

```text
0..150
```

### Lecture audio

Le frontend 1.5.1 sérialise les annonces afin d'éviter que chaque nouvelle annonce tue brutalement `aplay` au milieu d'un mot. Les `replace_key` permettent d'abandonner les annonces devenues obsolètes dans une séquence rapide.

## 5. Arrêt Piper propre

Le problème de SIGKILL observé en RC2 est corrigé.

Chaîne de fermeture attendue :

```text
SIGTERM / SIGINT
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt du worker Piper
```

Validé physiquement :

```text
arrêt après préchargement Piper : aucun SIGKILL
arrêt pendant préchargement     : aucun SIGKILL
```

## 6. Voice Name

Propriété CSP :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Décodage 4 × 7 bits :

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

La table `cvp_voice_names.py` reste partielle. Une Voice inconnue utilise le fallback numérique MSB / LSB / Program.

## 7. Protocole utile au runtime

### Song

```text
Nom/path      : 04 00 01 01 | 00
Play state    : 04 00 05 01 | 00
Position      : 04 00 0A 01 | 00
Loop A/B      : 04 00 0D 01 | 00
Longueur      : 04 00 1B 01 | 00
Tracks active : 0C 00 01 01 | 10..1F
Métronome     : 07 00 00 01 | 00
```

### Style

```text
Nom/path/source : 06 00 00 01 | 00
Start/Stop      : 06 00 03 01 | 00
Sync Start      : 06 00 07 01 | 00
```

Mute des huit parties :

```text
F0 43 73 01 51 05 00 00 08 <8 états> F7
```

Le protocole Style ne fournit pas de GET validé pour les huit mutes. CVP Access maintient donc un cache déterministe, initialisé à tout ON et remis à tout ON après la commande globale.

### Guide Yamaha

```text
04 03 00 01 | 00
```

Le mute du guide vocal CVP Access est purement logiciel et n'utilise aucune propriété Yamaha.

## 8. Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

L'upgrade :

- conserve les personnalisations existantes ;
- ajoute M, L, RPAREN et les 16 ALT+touches uniquement si les combinaisons sont libres ;
- copie le wrapper et sa base ;
- compile les modules ;
- génère la map clavier ;
- génère les WAV configurés et les WAV 1.5.1 ;
- lance le Doctor ;
- redémarre le service.

## 9. Vérification du paquet

```bash
python3 VERIFY_PACKAGE_151.py
```

Le vérificateur compile maintenant le wrapper, sa base et les modules principaux, puis contrôle notamment :

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

## 10. Doctor — état confirmé le 12 septembre 2026

Sur le Raspberry de référence, le Doctor a été exécuté après déploiement du layout courant et a renvoyé :

```text
OK Runtime 1.5.1             modules complets
OK Version runtime           1.5.1-RC3
OK Layout accessibilité      présente
OK WAV états 1.5.1           10 présents
OK WAV mute Style            8 présents
OK WAV Solo Song             16 présents
```

Cela valide la cohérence de l'installation, du layout et des banques WAV. Ce résultat ne remplace pas un test fonctionnel matériel de chaque nouvelle commande sur le CVP-905.

## 11. État de validation matérielle

Validé physiquement sur CVP-905 :

```text
navigation Song par mesures
F3 aller à une mesure
boucles A/B
Play/Pause
restauration du métronome pendant le transport
arrêt Piper propre
lecture de plusieurs noms de Voice
```

Implémenté, installé et contrôlé par le Doctor, mais encore à confirmer fonctionnellement sur le CVP-905 avant de le marquer validé matériellement :

```text
M       = mute/réactivation guide vocal
libellés Style « Mute ... »
L       = toutes pistes Song ON
) / °   = toutes parties Style ON
ALT+... = Solo Song
```

## 12. Actions disponibles mais non attribuées

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights ON/OFF
```

## 13. Terminologie utilisateur

Toujours distinguer :

```text
Guide Yamaha
Guide vocal
Vol. guide vocal
Piste Song
Rythme 1 / Basse / Accord 1... pour les parties Style
Solo piste N
Syncro Start
Pas de Song chargé.
```

## 14. Reproductibilité

Le test de référence futur reste un clone GitHub neuf suivi de :

```bash
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Une installation réellement vierge depuis une nouvelle carte Raspberry Pi OS reste un test séparé.
