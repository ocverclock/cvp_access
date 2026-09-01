# CVP Access — état de référence du projet

Dernière consolidation : **1 septembre 2026**.

Version de référence : **CVP Access 1.5.1-RC2**.

---

## 1. Matériel de référence

Toutes les validations CVP de ce projet doivent être interprétées comme réalisées sur :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP pour les annonces vocales
Clavier Apple Extended USB
```

Les anciennes mentions de **CVP-909** sont historiques et ne doivent plus être utilisées comme preuve de validation.

---

## 2. État logiciel validé

```text
Runtime          : CVP Access 1.5.1-RC2
Service          : cvp-access.service
Runtime installé : /opt/cvp-access
Configuration    : /etc/cvp-access/keyboard.toml
Map clavier      : /etc/cvp-access/keyboard-map.html
Voix             : Piper fr_FR-siwis-medium
Mode vocal       : hybrid
Génération WAV   : configured
Cache dynamique  : activé
```

Le runtime 1.5.1 est fourni par :

```text
cvp_access_1_5_1.py
```

et installé sous :

```text
/opt/cvp-access/cvp_access.py
```

Le moteur historique reste nécessaire :

```text
cvp_access_v1.5.py
cvp_access_v1.4.1.py
```

Ne pas supprimer `cvp_access_v1.4.1.py` tant que l'architecture transitoire n'a pas été remplacée.

---

## 3. Validation de reproductibilité RC2

Le **1 septembre 2026**, le dépôt courant a été renommé puis un clone GitHub neuf a été créé.

Procédure validée :

```bash
mv ~/CVP_access ~/CVP_access_RC2_working
git clone https://github.com/ocverclock/cvp_access.git ~/CVP_access
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Résultat :

```text
service : active
VERSION = "1.5.1-RC2"

CVP Access Doctor 1.5.1
========================================================================
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC2
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           8 présents
========================================================================
```

Le démarrage complet depuis le clone GitHub neuf a également été validé :

```text
CVP ACCESS V1.5.1-RC2
Affectations : 61
Voix Piper : fr_FR-siwis-medium
Mode vocal : hybrid
Génération WAV : configured
Préchargement Piper...
Piper runtime chargé : fr_FR-siwis-medium
MIDI : Prodipe
Audio : Clavinova USB
Clavier configurable prêt.
```

**Conclusion : la RC2 est reproductible depuis GitHub par l'upgrade 1.5.1.**

Une installation réellement vierge depuis une nouvelle carte Raspberry Pi OS reste un test futur intéressant mais n'est plus bloquante pour la RC2.

---

## 4. Principes d'accessibilité RC2

Le clavier est une interface d'accessibilité complémentaire au panneau physique du CVP.

Décision UX :

- privilégier les fonctions réellement utiles à un utilisateur non voyant ;
- ne pas dupliquer sans raison les boutons déjà accessibles physiquement ;
- conserver dans le catalogue les fonctions validées mais non attribuées ;
- afficher les actions disponibles mais non attribuées sous la map clavier.

### Aide CTRL

```text
CTRL + touche
```

annonce la fonction de la touche **sans exécuter l'action**.

La couche `Caps Lock` utilisée dans la RC1 a été abandonnée.

---

## 5. Layout clavier RC2

### Parties Style

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
```

### Pistes Song

```text
A Z E R T Y U I = pistes 1..8
Q S D F G H J K = pistes 9..16
```

### Informations / accessibilité

```text
W  = annonce nom Style
X  = annonce nom Song
C  = annonce longueur Song
V  = Syncro Start ON/OFF
B  = Guide ON/OFF
F7 = Métronome ON/OFF
```

Si aucun Song n'est chargé, `X` et `C` annoncent :

```text
Pas de Song chargé.
```

### Song

```text
Espace       = lecture / pause
Entrée       = stop
P            = annonce position
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
Page ↑ / Page ↓        = Volume Style +1 / -1
Maj + Page ↑ / Page ↓  = Volume Style +5 / -5
Origine / Fin          = Volume Song +1 / -1
Maj + Origine / Fin    = Volume Song +5 / -5
Inser / Suppr          = Volume Main +1 / -1
Maj + Inser / Suppr    = Volume Main +5 / -5
```

### Actions implémentées mais volontairement non attribuées

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights ON/OFF
```

Elles doivent apparaître dans la section :

```text
Actions disponibles mais non attribuées
```

de la map clavier.

---

## 6. Synthèse vocale RC2

Le mode vocal est :

```text
hybrid
```

Politique :

1. utiliser un WAV pré-généré s'il existe ;
2. sinon réutiliser un WAV dynamique déjà présent dans le cache ;
3. sinon synthétiser avec Piper ;
4. conserver le résultat dynamique dans le cache.

Le cache dynamique est situé dans :

```text
~/.cache/cvp-access/tts/
```

### Préchargement Piper

Piper est désormais préchargé au démarrage du service.

Objectif :

> déplacer le temps de chargement du modèle au démarrage du service afin que la première commande dynamique de l'utilisateur ne présente plus un délai anormal.

Le worker Piper reste résident pendant le fonctionnement du service.

### Terminologie utilisateur

Utiliser :

```text
Vol. guide vocal
Syncro Start
Pas de Song chargé.
```

Important :

- le nom utilisateur est **Syncro Start** ;
- l'identifiant interne reste `sync_start_toggle` ;
- les documents protocole Yamaha conservent le nom officiel **Sync Start**.

---

## 7. Map clavier

Générateur :

```text
cvp_keyboard_map.py
```

Sortie runtime :

```text
/etc/cvp-access/keyboard-map.html
```

La map est générée depuis la configuration réellement active et doit afficher :

- CTRL = aide vocale ;
- toutes les affectations actives ;
- Maj quand une variante ±5 existe ;
- Vol. guide vocal ;
- Syncro Start ;
- actions disponibles mais non attribuées ;
- format A4 paysage.

---

## 8. Installateur / upgrade

Upgrade RC2 :

```bash
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

L'upgrade :

- copie le runtime 1.5.1 ;
- copie les modules nécessaires ;
- installe le générateur de map ;
- installe les générateurs vocaux ;
- migre l'ancien layout RC1 CAPS uniquement lorsque les anciennes affectations correspondent exactement au profil officiel ;
- préserve les personnalisations utilisateur ;
- migre l'ancien PageUp/PageDown vers le volume Style ±1 ;
- ajoute les nouvelles affectations RC2 manquantes ;
- génère la map après migration ;
- génère les WAV configurés ;
- lance le Doctor ;
- redémarre le service.

Vérificateur du paquet :

```bash
python3 VERIFY_PACKAGE_151.py
```

Résultat attendu :

```text
CVP Access 1.5.1 RC2 package: OK
```

---

## 9. Architecture transitoire

```text
cvp_access_1_5_1.py
        |
        +-- cvp_access_v1.5.py
        |       |
        |       `-- cvp_access_v1.4.1.py
        |
        +-- cvp_midi.py
        +-- cvp_song_151.py
        +-- cvp_speech_151.py
        +-- cvp_style.py
        +-- cvp_voice.py
        +-- cvp_registration.py
        +-- cvp_keyboard.py
        +-- cvp_keyboard_map.py
        `-- cvp_yamaha.py
```

---

## 10. Sources de vérité — ordre de priorité

En cas de contradiction :

1. `PROJECT_STATE.md`
2. `docs/CVP_ACCESS_1_5_1.md`
3. `docs/KEY_ACTIONS_1_5_1.md`
4. `CVP905_PROTOCOL_CHECKPOINT_RC4.md`
5. `docs/FUNCTION_CATALOG.md`
6. `docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md`
7. runtime 1.5.1 et modules
8. documents de recherche datés
9. anciens documents RC1 / RC3 uniquement comme historique

Un script de recherche n'est jamais une source de vérité à lui seul.

---

## 11. Protocole CVP-905 — éléments validés utiles au runtime

Header CSP moderne :

```text
F0 43 73 01 52 25 26
```

Actions :

```text
GET    01 00
SET    01 01
INFO   00 00
EVENTS 02 00
```

### Song

```text
Nom/path      : 04 00 01 01 | 00
Position      : 04 00 0A 01 | 00
Longueur      : 04 00 1B 01 | 00
Loop A/B      : 04 00 0D 01 | 00
Tracks        : 04 01 00 01 | 10..1F
Métronome     : 07 00 00 01 | 00
```

Décodage texte Yamaha validé :

```text
1 octet masque des bits hauts + jusqu'à 7 octets de données
```

L'ancienne hypothèse d'une longueur 14-bit au début du texte est invalide pour ces réponses.

### Style

```text
Nom/path/source : 06 00 00 01 | 00
Start/Stop      : 06 00 03 01 | 00
Sync Start      : 06 00 07 01 | 00
```

Section Control :

```text
F0 43 7E 00 ss 7F F7

00..02 = Intro 1..3
08..0B = Main A..D
10..13 = Fill A..D
18     = Break
20..22 = Ending 1..3
```

Mute des huit parties Style :

```text
F0 43 73 01 51 05 00 00 08
Rhy1 Rhy2 Bass Chd1 Chd2 Pad Phr1 Phr2
F7
```

### Guide

```text
04 03 00 01 | 00
```

GET/SET bool validé.

### Registration

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
```

`XX=00..07`.

---

## 12. Recherches directes clôturées

Ne pas relancer de scans massifs sans nouvelle preuve indépendante.

### ACMP direct

Recherche directe clôturée.

Workaround validé via Registration :

```text
GPm07 payload[2]
00 = OFF
7F = ON
```

### Fingering direct

Recherche directe clôturée.

Valeurs Registration validées :

```text
GPm07 payload[8]

03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

### Auto Fill In

Recherche directe clôturée.

### Synchro Stop

Recherche directe clôturée.

### OTS Link

Non résolu.

---

## 13. Genos 1 — laboratoire secondaire

Le Genos 1 reste un banc Yamaha complémentaire.

Règle absolue :

> Une commande validée sur Genos n'est jamais considérée comme validée sur CVP-905 avant test physique sur le CVP.

Résultats Genos utiles mais non validés CVP :

- XG Voice Right1/2/3/Left GET/SET ;
- sélection directe Style famille Yamaha 51 ;
- CSP moderne CVP : négatif sur Genos.

Voir :

```text
docs/GENOS1_MIDI_CHECKPOINT_2026-08-29.md
```

---

## 14. Points futurs possibles

La RC2 est figée. Les développements futurs doivent partir de cette base.

Pistes raisonnables :

1. test d'installation réellement vierge sur une nouvelle carte Raspberry Pi OS ;
2. amélioration éventuelle de l'arrêt du worker Piper si le `SIGKILL` systemd observé devient systématique ;
3. fonctions d'accessibilité supplémentaires sur les touches encore libres (`N`, `,`, `;`) seulement si elles apportent une vraie valeur ;
4. poursuite de la séparation propre du moteur historique ;
5. tests CVP ciblés de commandes Genos uniquement si l'intérêt utilisateur est réel.

Ne pas rouvrir les recherches massives ACMP/Fingering sans nouvelle preuve.

---

## 15. Rollback

Retour au runtime v1.5 historique :

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

---

## 16. État final RC2

**CVP Access 1.5.1-RC2 est le point de référence validé au 1 septembre 2026.**

Validé :

- fonctionnement physique sur CVP-905 ;
- nouveau layout accessibilité ;
- aide CTRL ;
- informations Style/Song ;
- Syncro Start ;
- Guide ;
- Métronome ;
- volume Style ±1/±5 ;
- terminologie vocale ;
- préchargement Piper ;
- cache dynamique ;
- map A4 ;
- upgrade RC2 ;
- Doctor ;
- vérification paquet ;
- réinstallation depuis un clone GitHub neuf.
