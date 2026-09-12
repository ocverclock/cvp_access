# AI_HANDOFF — CVP Access

## À lire en premier

Pour reprendre le projet :

1. lire `PROJECT_STATE.md` ;
2. lire `docs/CVP_ACCESS_1_5_1.md` ;
3. lire `docs/KEY_ACTIONS_1_5_1.md` ;
4. lire `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md` ;
5. consulter `docs/FUNCTION_CATALOG.md` ;
6. consulter `CVP905_PROTOCOL_CHECKPOINT_RC4.md` uniquement pour le protocole historique ;
7. ne pas relancer les recherches massives déjà clôturées.

## Version de départ

```text
CVP Access 1.5.1-RC3
Date de consolidation : 12 septembre 2026
Instrument de référence : Yamaha CVP-905 firmware 1.03
```

La base correcte reste **1.5.1-RC3**. Ne pas repartir d’une ancienne RC1, de la couche Caps Lock ou d’un ancien runtime `1.5-RC4-dev`.

## Runtime

```text
Repo            : ~/CVP_access
Runtime         : /opt/cvp-access
Entrée runtime  : /opt/cvp-access/cvp_access.py
Source courante : cvp_access_1_5_1.py
Base 1.5.1      : cvp_access_1_5_1_base.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Voix            : fr_FR-siwis-medium
Mode            : hybrid
```

Architecture transitoire actuelle :

```text
cvp_access_1_5_1.py
-> cvp_access_1_5_1_base.py
-> cvp_access_v1.5.py
-> cvp_access_v1.4.1.py
```

Le wrapper `cvp_access_1_5_1.py` ajoute les commandes globales et le Solo Song. `cvp_access_1_5_1_base.py` contient la consolidation 1.5.1 précédente : correctifs Song, Piper, accessibilité, Voice Name, Guide, métronome, etc.

Ne pas supprimer les moteurs historiques tant que cette architecture n’a pas été refactorisée.

## Layout de référence

### Parties Style / clavier

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

Terminologie vocale Style :

```text
OFF -> « Mute Rythme 1 », « Mute Basse », etc.
ON  -> « Rythme 1 activé », « Basse activée », etc.
```

### Pistes Song

```text
A Z E R T Y U I = Song 1..8
Q S D F G H J K = Song 9..16
L               = toutes les pistes Song ON
```

Solo :

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

Le Solo active d’abord la piste sélectionnée, coupe ensuite les 15 autres, puis relit les 16 états. L annonce `Toutes les pistes Song activées` et sert de retour rapide après un Solo.

### Informations / accessibilité

```text
W  = nom Style
X  = nom Song
C  = longueur Song
V  = Syncro Start
B  = Guide Yamaha ON/OFF
M  = mute/réactivation du guide vocal CVP Access
N  = nom Voice Main
,  = nom Voice Layer
;  = nom Voice Left
F7 = Métronome
```

Important :

```text
Guide Yamaha (B) != guide vocal CVP Access (M)
```

M coupe uniquement les annonces CVP Access, donc **WAV + Piper**. Il ne touche ni au Guide Yamaha, ni au Song, ni au Style, ni au métronome, ni au son clavier. Le niveau du guide vocal est conservé.

### Song transport / navigation

```text
Espace      = Play / Pause
Entrée      = Stop
P           = position
← / →       = mesure -1 / +1
Maj+← / →   = mesure -5 / +5
F3          = aller à une mesure
F4          = point A
F5          = point B
F6          = boucle A/B
```

### Volumes

```text
Up / Down              = Vol. guide vocal
PageUp / PageDown      = Style ±1
Shift + PageUp/Down    = Style ±5
Home / End             = Song ±1
Shift + Home/End       = Song ±5
Insert / Delete        = Main ±1
Shift + Insert/Delete  = Main ±5
```

CTRL + touche annonce la fonction sans l’exécuter. Caps Lock n’est plus utilisé.

## Speech

Ordre :

```text
WAV pré-généré
-> cache dynamique
-> synthèse Piper
-> stockage cache
```

Piper est préchargé au démarrage. Le worker reste résident. Cache :

```text
~/.cache/cvp-access/tts/
```

Les annonces Song prévisibles utilisent des fragments WAV. Les nombres destinés aux mesures vont de `0` à `150`. Les 16 annonces `Solo piste N` sont pré-générées.

Le moteur audio sérialise les annonces afin de ne plus tuer brutalement `aplay` entre deux phrases rapides.

## RC3 — arrêt Piper

Le SIGKILL systemd observé en RC2 est corrigé. Le runtime intercepte `SIGTERM` / `SIGINT` et provoque une sortie Python normale :

```text
signal
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt Piper
```

Tests physiques validés : arrêt normal et arrêt pendant preload sans SIGKILL.

## RC3 — Voice Name

Propriété CSP :

```text
02 00 01 01
00 = Main
01 = Layer
02 = Left
```

Validations physiques :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

La table `cvp_voice_names.py` reste partielle. Une Voice inconnue utilise le fallback MSB / LSB / Program.

## Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

L’upgrade :

- conserve les personnalisations existantes ;
- ajoute M, L, `RPAREN` et les 16 bindings ALT seulement si les combinaisons sont libres ;
- copie le wrapper et sa base 1.5.1 ;
- génère les WAV configurés ;
- génère les WAV `Mute ...` et `Solo piste N` ;
- lance le Doctor ;
- redémarre le service.

Doctor attendu, au minimum :

```text
OK Runtime 1.5.1
OK Version runtime 1.5.1-RC3
OK Layout accessibilité
OK WAV états 1.5.1
OK WAV mute Style
OK Solo Song
OK WAV Solo Song
```

## État de validation matérielle au 12 septembre 2026

Validé physiquement sur le CVP-905 :

```text
navigation LEFT/RIGHT et ±5
F3 aller à la mesure
boucles A/B
Play/Pause
restauration métronome pendant transport
arrêt Piper propre
lecture de plusieurs noms de Voice
```

Implémenté et intégré à l’upgrade, mais encore à confirmer physiquement avant de le marquer validé :

```text
M = mute/réactivation guide vocal
libellés Style « Mute ... »
L = toutes pistes Song ON
) / ° = toutes parties Style ON
ALT + piste = Solo Song
```

## Actions non attribuées par défaut

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights
```

## Terminologie utilisateur

Toujours préférer :

```text
Syncro Start
Guide Yamaha
Guide vocal
Vol. guide vocal
Mute Rythme 1
Solo piste 1
Pas de Song chargé.
```

## Points à ne pas rouvrir sans nouvelle preuve

```text
ACMP direct
Fingering direct
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu. Le Genos reste un banc secondaire : aucune commande Genos ne devient validation CVP sans test physique sur CVP-905.

## Sources de vérité

1. `PROJECT_STATE.md`
2. `AI_HANDOFF.md`
3. `docs/CVP_ACCESS_1_5_1.md`
4. `docs/KEY_ACTIONS_1_5_1.md`
5. `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md`
6. `CVP905_PROTOCOL_CHECKPOINT_RC4.md`
7. `docs/FUNCTION_CATALOG.md`
8. runtime et modules
9. anciens checkpoints comme historique

## Prochain travail recommandé

1. déployer le HEAD consolidé sur le CVP-905 ;
2. valider physiquement M, L, `) / °`, les annonces `Mute ...` et les Solo ALT ;
3. corriger uniquement les écarts réellement observés ;
4. compléter la table des noms de Voice ;
5. refaire un clone GitHub neuf + upgrade ;
6. poursuivre ensuite la simplification de l’architecture transitoire.

## Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## Règle de reprise

**Le point de départ obligatoire est le `main` courant de CVP Access 1.5.1-RC3, consolidé le 12 septembre 2026.**
