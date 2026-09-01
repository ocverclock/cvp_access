# CVP Access — état de référence du projet

Dernière consolidation : **1 septembre 2026**.

Version de référence : **CVP Access 1.5.1-RC3**.

## 1. Matériel principal

Toutes les validations CVP de référence ont été réalisées sur :

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP pour le retour vocal
Clavier Apple Extended USB
Piper fr_FR-siwis-medium
```

Les résultats Genos restent secondaires et ne constituent jamais une validation CVP sans test physique sur CVP-905.

## 2. Runtime

```text
Source           : cvp_access_1_5_1.py
Version          : 1.5.1-RC3
Runtime installé : /opt/cvp-access/cvp_access.py
Service          : cvp-access.service
Configuration    : /etc/cvp-access/keyboard.toml
Map clavier      : /etc/cvp-access/keyboard-map.html
Speech mode      : hybrid
Génération WAV   : configured
Cache dynamique  : activé
```

Architecture transitoire :

```text
cvp_access_1_5_1.py
        |
        +-- cvp_access_v1.5.py
        |       |
        |       `-- cvp_access_v1.4.1.py
        |
        +-- cvp_midi.py
        +-- cvp_song_151.py
        +-- cvp_speech.py
        +-- cvp_speech_151.py
        +-- cvp_piper_worker.py
        +-- cvp_style.py
        +-- cvp_voice.py
        +-- cvp_voice_names.py
        +-- cvp_registration.py
        +-- cvp_keyboard.py
        +-- cvp_keyboard_map.py
        `-- cvp_yamaha.py
```

Ne pas supprimer les moteurs historiques tant que cette architecture transitoire n'a pas été remplacée.

## 3. RC3 — arrêt Piper propre

Le problème suivant a été physiquement reproduit en RC2 :

```text
systemd:
Killing process (...) with signal SIGKILL
```

Cause :

- systemd envoyait SIGTERM au runtime ;
- le processus principal quittait sans assurer le nettoyage Python attendu ;
- le worker Piper restait vivant ;
- après `TimeoutStopSec=5`, systemd terminait le worker avec SIGKILL.

Correction RC3 :

```text
SIGTERM / SIGINT
-> gestionnaire de signal Python
-> SystemExit
-> arrêt Python normal
-> atexit
-> SpeechManager.close()
-> arrêt du worker Piper
```

`atexit.register(self.close)` est maintenant enregistré **avant** le préchargement Piper.

Cette position est importante : elle garantit le nettoyage même si l'arrêt arrive pendant le chargement du modèle Piper.

### Validation physique — arrêt normal

Résultat :

```text
Arrêt propre demandé (signal 15).
Récepteur MIDI arrêté.
Deactivated successfully.
Stopped cvp-access.service
```

Aucun SIGKILL.

### Validation physique — arrêt pendant le préchargement Piper

Test avec le worker Piper détecté comme enfant du runtime.

Résultat :

```text
Préchargement Piper...
Arrêt propre demandé (signal 15).
Deactivated successfully.
Stopped cvp-access.service
```

Aucun SIGKILL.

Conclusion :

**le problème d'arrêt du worker Piper est corrigé en RC3.**

Ne pas masquer ce problème en augmentant `TimeoutStopSec`.

## 4. RC3 — lecture des noms de Voice

Propriété CSP validée :

```text
02 00 01 01
```

Indexes :

```text
00 = Main
01 = Layer
02 = Left
```

Réponses physiquement observées :

```text
MAIN  : 03 30 00 00
LAYER : 00 20 42 31
LEFT  : 03 20 0E 04
```

Le payload est constitué de quatre groupes 7 bits représentant une valeur de 24 bits.

Décodage :

```python
packed = (
    (b0 << 21)
    | (b1 << 14)
    | (b2 << 7)
    | b3
)

msb = (packed >> 16) & 0xFF
lsb = (packed >> 8) & 0xFF
program = (packed & 0xFF) + 1
```

Correspondances validées :

```text
108 / 0  / 1  = CFX Concert Grand
8   / 33 / 50 = Seattle Strings
104 / 7  / 5  = Suitcase Soft
```

Nouveau module :

```text
cvp_voice_names.py
```

Fonctions :

```text
CVPVoiceId
decode_cvp_voice()
resolve_voice_name()
```

Actions :

```text
announce_main_voice_name
announce_layer_voice_name
announce_left_voice_name
```

Touches RC3 :

```text
N = nom Voice Main
, = nom Voice Layer
; = nom Voice Left
```

La synthèse vocale prononce uniquement le nom de la Voice.

Exemples :

```text
CFX Concert Grand
Seattle Strings
Suitcase Soft
```

Les termes `Main`, `Layer` et `Left` restent utilisables dans les logs de diagnostic mais ne sont pas prononcés.

### Limite actuelle

Le mécanisme de lecture et le décodage sont validés.

La table locale RC3 contient actuellement seulement les trois Voices physiquement identifiées pendant les tests.

Une Voice absente de la table locale est annoncée par son identité MIDI numérique plutôt qu'avec un nom supposé.

Voir :

```text
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
```

## 5. Layout clavier RC3

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
N  = annonce nom Voice Main
,  = annonce nom Voice Layer
;  = annonce nom Voice Left
F7 = Métronome ON/OFF
```

Si aucun Song n'est chargé :

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

## 6. Aide CTRL

```text
CTRL + touche
```

annonce la fonction sans exécuter l'action.

La couche Caps Lock expérimentale de RC1 est abandonnée.

## 7. Actions implémentées mais non attribuées

```text
Intro Style 1..3
Main Style A..D
Fill Style A..D
Break Style
Ending Style 1..3
Registration Memory 1..8
Stream Lights ON/OFF
```

Elles doivent apparaître dans la map sous :

```text
Actions disponibles mais non attribuées
```

## 8. Synthèse vocale

Mode :

```text
hybrid
```

Politique :

```text
WAV pré-généré
-> cache dynamique
-> Piper
-> cache du résultat
```

Le worker Piper est préchargé au démarrage et reste résident pendant le fonctionnement du service.

Cache :

```text
~/.cache/cvp-access/tts/
```

Terminologie utilisateur :

```text
Vol. guide vocal
Syncro Start
Pas de Song chargé.
```

Pour les actions Voice, prononcer uniquement le nom du son.

## 9. Installation / upgrade RC3

Commande :

```bash
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Résultat paquet attendu :

```text
CVP Access 1.5.1 RC3 package: OK
```

Libellés upgrade attendus :

```text
[CVP Access] Upgrade runtime -> 1.5.1-RC3
[CVP Access] 1.5.1-RC3 installed.
```

Doctor attendu :

```text
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC3
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           8 présents
```

## 10. Reproductibilité

La RC2 a déjà été validée depuis un clone GitHub neuf.

Après consolidation et push de la RC3, refaire :

```bash
mv ~/CVP_access ~/CVP_access_RC3_working
git clone https://github.com/ocverclock/cvp_access.git ~/CVP_access
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Objectif :

**valider que la RC3 est entièrement reproductible depuis GitHub.**

## 11. Sources de vérité

En cas de contradiction :

1. `PROJECT_STATE.md`
2. `AI_HANDOFF.md`
3. `docs/CVP_ACCESS_1_5_1.md`
4. `docs/KEY_ACTIONS_1_5_1.md`
5. `docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md`
6. `CVP905_PROTOCOL_CHECKPOINT_RC4.md`
7. `docs/FUNCTION_CATALOG.md`
8. runtime et modules
9. checkpoints de recherche datés
10. anciens documents RC uniquement comme historique

Un script de recherche n'est jamais une source de vérité à lui seul.

## 12. Protocole CVP-905 utile au runtime

Header CSP :

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

### Guide

```text
04 03 00 01 | 00
```

### Voice

```text
02 00 01 01 | 00 = Main
02 00 01 01 | 01 = Layer
02 00 01 01 | 02 = Left
```

### Registration Recall

```text
F0 43 73 01 52 25 11 00 02 00 XX F7
XX = 00..07
```

## 13. Recherches directes clôturées

Ne pas relancer sans nouvelle preuve indépendante :

```text
ACMP direct
Fingering direct
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

Workaround Registration ACMP :

```text
GPm07 payload[2]

00 = OFF
7F = ON
```

Workaround Registration Fingering :

```text
GPm07 payload[8]

03 = AI Fingered
04 = Fingered
0C = AI Full Keyboard
```

## 14. Genos 1

Le Genos reste un laboratoire secondaire.

Règle absolue :

> Une commande validée sur Genos n'est jamais considérée comme validée sur CVP-905 avant test physique sur le CVP.

## 15. Prochaines étapes

Priorités raisonnables :

1. compléter `cvp_voice_names.py` avec la table Yamaha CVP-905 ;
2. pousser la RC3 sur GitHub ;
3. refaire un clone GitHub neuf + upgrade RC3 ;
4. installation future sur carte Raspberry Pi réellement vierge ;
5. poursuivre progressivement la séparation du moteur historique.

Ne pas relancer de scan massif de protocole sans nouvelle hypothèse.

## 16. Rollback

Retour au runtime historique :

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

## 17. Checkpoint

**CVP Access 1.5.1-RC3 est le point de référence au 1 septembre 2026.**
