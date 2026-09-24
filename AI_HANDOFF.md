# AI_HANDOFF — CVP Access

Dernière consolidation : **24 septembre 2026**.

## 1. À lire en premier

Ordre de reprise :

1. `PROJECT_STATE.md`
2. `docs/CVP_ACCESS_1_5_2.md`
3. `docs/NETWORK_MAINTENANCE_PORTAL.md`
4. `AI_HANDOFF.md`
5. `docs/CVP_ACCESS_1_5_1.md` pour la base fonctionnelle
6. `docs/KEY_ACTIONS_1_5_1.md`
7. `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md`
8. `CVP905_PROTOCOL_CHECKPOINT_RC4.md` pour le protocole historique
9. `docs/FUNCTION_CATALOG.md`

Ne pas relancer les scans massifs déjà clôturés sans nouvelle hypothèse.

## 2. Point de départ obligatoire

```text
CVP Access 1.5.2-RC1
Yamaha CVP-905 firmware 1.03
Raspberry Pi / Debian 13 arm64
```

Ne pas repartir de RC1, de la couche Caps Lock ou du runtime expérimental `1.5-RC4-dev`.

## 3. Runtime

```text
Repo            : ~/CVP_access
Runtime         : /opt/cvp-access
Entrée runtime  : /opt/cvp-access/cvp_access.py
Source courante : cvp_access_1_5_2.py
Base 1.5.1      : cvp_access_1_5_1_base.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Voix            : fr_FR-siwis-medium
Mode            : hybrid
```

Architecture :

```text
cvp_access_1_5_2.py
-> cvp_access_1_5_1_base.py
-> cvp_access_v1.5.py
-> cvp_access_v1.4.1.py
```

Le wrapper courant ajoute les commandes globales L / RPAREN et le Solo Maj. La base contient les correctifs Song, Piper, Voice Name, Guide Yamaha, métronome et accessibilité.

## 4. Layout de référence

### Style / clavier

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

Terminologie Style :

```text
OFF -> Mute Rythme 1 / Mute Basse / ...
ON  -> Rythme 1 activé / Basse activée / ...
```

### Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
L               = toutes les pistes Song ON
```

Solo :

```text
Maj+A = Solo piste 1
Maj+Z = Solo piste 2
Maj+E = Solo piste 3
Maj+R = Solo piste 4
Maj+T = Solo piste 5
Maj+Y = Solo piste 6
Maj+U = Solo piste 7
Maj+I = Solo piste 8
Maj+Q = Solo piste 9
Maj+S = Solo piste 10
Maj+D = Solo piste 11
Maj+F = Solo piste 12
Maj+G = Solo piste 13
Maj+H = Solo piste 14
Maj+J = Solo piste 15
Maj+K = Solo piste 16
```

Le Solo active d'abord la piste choisie, coupe les quinze autres, relit les seize états puis annonce `Solo piste N`. L remet les seize pistes sur ON.

**Le Solo Maj est validé matériellement sur CVP-905 firmware 1.03.** La confirmation utilisateur du 12 septembre 2026 valide le comportement : piste choisie ON, 15 autres OFF.

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

Règle essentielle :

```text
Guide Yamaha (B) != guide vocal CVP Access (M)
```

M coupe uniquement nos WAV + Piper. Le volume mémorisé reste inchangé.

### Transport / navigation

```text
Espace      = Play/Pause
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

CTRL + touche = aide vocale sans exécution. Caps Lock n'est plus utilisé.

## 5. Speech

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> cache du résultat
```

Piper est préchargé et reste résident.

Cache :

```text
~/.cache/cvp-access/tts/
```

Les annonces Song prévisibles utilisent des fragments WAV. Nombres de mesure pré-générés : `0..150`.

Les 16 annonces `Solo piste N` sont pré-générées.

La lecture audio est sérialisée pour éviter les coupures/craquements dus à la terminaison brutale d'`aplay`. Les `replace_key` permettent d'abandonner les annonces obsolètes.

## 6. Piper shutdown — validé

```text
SIGTERM / SIGINT
-> SystemExit
-> atexit
-> SpeechManager.close()
-> arrêt Piper
```

Validé physiquement : arrêt normal et arrêt pendant preload sans SIGKILL.

## 7. Voice Name — validation partielle

```text
Propriété : 02 00 01 01
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

`cvp_voice_names.py` reste partiel. Ne jamais inventer un nom absent de la table.

## 8. Installation / upgrade

```bash
cd ~/CVP_access
git pull --ff-only origin main
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

L'upgrade :

- préserve les personnalisations ;
- migre les anciens Solo ALT officiels vers Maj ;
- ajoute M, L, RPAREN et les 16 bindings SHIFT seulement si libres ;
- copie wrapper + base ;
- génère map et WAV ;
- lance Doctor ;
- redémarre le service.

## 9. Doctor — checkpoint confirmé le 12 septembre 2026

Résultat observé sur le Raspberry de référence après migration ALT -> Maj :

```text
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC3
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           10 présents
OK    WAV mute Style            8 présents
OK    WAV Solo Song             16 présents
```

Les banques vocales étaient complètes :

```text
Generated: 0; already present: 863
Generated: 0; existing: 262
```

## 10. Validation matérielle

### Déjà validé sur CVP-905

```text
navigation Song LEFT/RIGHT et ±5
F3 aller à la mesure
boucles A/B
Play/Pause
restauration métronome
arrêt Piper propre
lecture de plusieurs noms de Voice
Maj+... = Solo Song
```

### À tester fonctionnellement sur le CVP-905

```text
M       = mute/réactivation guide vocal
libellés Style Mute ...
L       = toutes pistes Song ON
) / °   = toutes parties Style ON
```

## 11. Actions non attribuées par défaut

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights
```

## 12. Recherches fermées

Ne pas rouvrir sans nouvelle preuve :

```text
ACMP direct
Fingering direct
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

ACMP et Fingering disposent de workarounds Registration validés.

## 13. Priorités suivantes

1. test matériel M ;
2. test matériel libellés Style `Mute ...` ;
3. test matériel L ;
4. test matériel `) / °` ;
5. si la latence vocale reste sensible alors que les WAV sont complets, identifier les annonces encore dynamiques et mesurer le chemin audio ;
6. compléter `cvp_voice_names.py` ;
7. refaire un clone GitHub neuf + upgrade.

## 14. Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## 15. Règle de reprise

**Le point de départ obligatoire est le HEAD `main` consolidé au 12 septembre 2026, basé sur CVP Access 1.5.1-RC3, avec Solo Song Maj validé matériellement.**


## Maintenance autonome 1.5.2

La maintenance réseau fait partie du paquet courant. Référence complète : `docs/CVP_ACCESS_1_5_2.md` et `docs/NETWORK_MAINTENANCE_PORTAL.md`.

Règles à conserver :

```text
Ethernet ou Wi-Fi normal actif -> pas de CVP-ACCESS
aucun réseau normal -> CVP-ACCESS après ~30 s
hotspot -> Web http://10.42.0.1
Mac/Linux Samba -> smb://...
Windows Samba -> \\...
```

Le dashboard et la carte clavier doivent afficher les adresses Web/Samba copiables. La carte doit rester imprimable sur une seule page A4 paysage.

Le chemin d'upgrade courant est :

```bash
python3 VERIFY_PACKAGE_152.py
sudo bash cvp_access_installer/upgrade_1_5_2.sh
```
