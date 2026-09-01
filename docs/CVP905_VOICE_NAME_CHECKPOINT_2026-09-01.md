# CVP-905 — checkpoint lecture du nom des Voices

Date : **1 septembre 2026**

Projet : **CVP Access**  
Version de référence : **1.5.1-RC3**

## 1. Matériel validé

```text
Yamaha CVP-905
Firmware 1.03
Raspberry Pi / Debian 13 arm64
Interface MIDI DIN Prodipe
USB Audio du CVP pour le retour vocal
CVP Access 1.5.1-RC3
```

## 2. Objectif

Permettre à un utilisateur non voyant de connaître la Voice actuellement utilisée par les trois parties clavier principales :

```text
Main
Layer
Left
```

L'annonce vocale doit prononcer uniquement le nom du son, sans préfixe inutile.

Exemples attendus :

```text
CFX Concert Grand
Seattle Strings
Suitcase Soft
```

Les termes `Main`, `Layer` et `Left` peuvent rester dans les logs de diagnostic.

## 3. Propriété CSP validée

La propriété suivante permet de lire l'identité MIDI de la Voice :

```text
02 00 01 01
```

Indexes validés sur CVP-905 :

```text
00 = Main
01 = Layer
02 = Left
```

API runtime utilisée :

```python
VoiceController.get_cvp_midi_raw(index)
```

Implémentation existante :

```python
PROP_VOICE_MIDI = [0x02, 0x00, 0x01, 0x01]
```

## 4. Réponses physiquement observées

Test réalisé directement sur le Yamaha CVP-905 firmware 1.03.

Résultats :

```text
MAIN  : 03 30 00 00
LAYER : 00 20 42 31
LEFT  : 03 20 0E 04
```

Valeurs décimales correspondantes :

```text
MAIN  : [3, 48, 0, 0]
LAYER : [0, 32, 66, 49]
LEFT  : [3, 32, 14, 4]
```

## 5. Décodage Yamaha 4 × 7 bits

Le payload ne contient pas directement trois octets MSB / LSB / Program.

Yamaha encode ici une valeur de 24 bits sous forme de quatre groupes de 7 bits compatibles SysEx MIDI.

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

Le `program` est présenté en **1..128**, comme dans la Yamaha Data List.

## 6. Correspondances validées

### Main

Réponse brute :

```text
03 30 00 00
```

Décodage :

```text
MSB     = 108
LSB     = 0
Program = 1
```

Voice :

```text
CFX Concert Grand
```

### Layer

Réponse brute :

```text
00 20 42 31
```

Décodage :

```text
MSB     = 8
LSB     = 33
Program = 50
```

Voice :

```text
Seattle Strings
```

### Left

Réponse brute :

```text
03 20 0E 04
```

Décodage :

```text
MSB     = 104
LSB     = 7
Program = 5
```

Voice :

```text
Suitcase Soft
```

Résumé :

```text
03 30 00 00 -> 108 / 0  / 1  -> CFX Concert Grand
00 20 42 31 ->   8 / 33 / 50 -> Seattle Strings
03 20 0E 04 -> 104 / 7  / 5  -> Suitcase Soft
```

Les noms et triplets correspondent à la Yamaha CVP-909/CVP-905 Data List.

## 7. Implémentation RC3

Nouveau module :

```text
cvp_voice_names.py
```

Il fournit :

```text
CVPVoiceId
decode_cvp_voice()
resolve_voice_name()
```

Structure :

```python
@dataclass(frozen=True)
class CVPVoiceId:
    msb: int
    lsb: int
    program: int
```

Le module contient actuellement une table locale limitée aux Voices physiquement identifiées pendant cette validation :

```python
VOICE_NAMES = {
    CVPVoiceId(108, 0, 1): "CFX Concert Grand",
    CVPVoiceId(8, 33, 50): "Seattle Strings",
    CVPVoiceId(104, 7, 5): "Suitcase Soft",
}
```

## 8. Actions runtime

Actions ajoutées :

```text
announce_main_voice_name
announce_layer_voice_name
announce_left_voice_name
```

Indexes utilisés :

```text
announce_main_voice_name  -> index 00
announce_layer_voice_name -> index 01
announce_left_voice_name  -> index 02
```

Le runtime :

1. lit `02 00 01 01` ;
2. décode les quatre octets 7 bits ;
3. obtient MSB / LSB / Program ;
4. cherche le nom dans la table locale ;
5. annonce uniquement le nom du son.

## 9. Affectations clavier RC3

```text
N = nom de la Voice Main
, = nom de la Voice Layer
; = nom de la Voice Left
```

Noms TOML :

```text
"N"         = "announce_main_voice_name"
"COMMA"     = "announce_layer_voice_name"
"SEMICOLON" = "announce_left_voice_name"
```

## 10. Aide CTRL

La règle générale du projet reste inchangée :

```text
CTRL + touche
```

annonce la fonction sans exécuter l'action.

Exemples :

```text
CTRL + N
-> annonce l'aide de la touche Main
-> ne lance pas la lecture du nom de la Voice

CTRL + ,
-> annonce l'aide de la touche Layer

CTRL + ;
-> annonce l'aide de la touche Left
```

## 11. Politique vocale

Pour les trois actions Voice, la synthèse ne prononce pas :

```text
Main CFX Concert Grand
Layer Seattle Strings
Left Suitcase Soft
```

Elle prononce seulement :

```text
CFX Concert Grand
Seattle Strings
Suitcase Soft
```

Ce choix évite une diction trop compacte entre le nom de la partie et le nom de la Voice.

## 12. Logs de diagnostic

Les logs peuvent conserver le contexte de partie :

```text
Main : CFX Concert Grand (108/0/1)
Layer : Seattle Strings (8/33/50)
Left : Suitcase Soft (104/7/5)
```

Cette information n'est pas destinée à être prononcée.

## 13. Fallback pour Voice inconnue

Le protocole de lecture et le décodage sont validés indépendamment de la table de noms.

Si une Voice valide n'est pas encore présente dans `VOICE_NAMES`, CVP Access ne doit pas inventer de nom.

Fallback :

```text
MSB / LSB / Program
```

Exemple de principe :

```text
banque 108, 3, programme 12
```

Cela permet de conserver une information fiable en attendant l'ajout du nom correspondant.

## 14. Limite actuelle

Statut RC3 :

```text
Lecture CSP             : VALIDÉE
Indexes Main/Layer/Left : VALIDÉS
Décodage 4 x 7 bits     : VALIDÉ
Correspondances testées : VALIDÉES
Annonce vocale          : VALIDÉE
Table complète Yamaha   : À FAIRE
```

La table locale RC3 ne contient actuellement que les trois Voices physiquement identifiées lors des tests.

## 15. Étape suivante recommandée

Compléter `cvp_voice_names.py` avec la table des Voices preset du CVP-905 issue de la Yamaha Data List.

Objectif :

```text
CVP-905
   |
   +-- GET 02 00 01 01
   |
   +-- décodage 4 x 7 bits
   |
   +-- MSB / LSB / PC#
   |
   +-- table locale Yamaha CVP-905
   |
   `-- annonce Piper du nom
```

Cette table doit rester locale afin que la fonction soit disponible hors ligne.

## 16. Règle de validation

Une correspondance issue de la Yamaha Data List peut être intégrée dans la table locale.

Cependant, toute nouvelle conclusion concernant le protocole ou un nouvel index doit rester considérée comme non validée tant qu'elle n'a pas été physiquement testée sur le CVP-905.

Les résultats Genos restent un laboratoire secondaire et ne constituent pas une validation CVP.

## 17. Fichiers concernés par la RC3

```text
cvp_access_1_5_1.py
cvp_voice.py
cvp_voice_names.py
cvp_keyboard.py
cvp_speech_151.py
config/default-1.5.1.toml
VERIFY_PACKAGE_151.py
cvp_access_installer/upgrade_1_5_1.sh
```

Documentation :

```text
PROJECT_STATE.md
AI_HANDOFF.md
docs/CVP_ACCESS_1_5_1.md
docs/KEY_ACTIONS_1_5_1.md
docs/FUNCTION_CATALOG.md
docs/CVP905_VOICE_NAME_CHECKPOINT_2026-09-01.md
```

## 18. Checkpoint

**La lecture de l'identité des Voices Main / Layer / Left et le décodage Yamaha 4 × 7 bits sont validés sur Yamaha CVP-905 firmware 1.03.**

**CVP Access 1.5.1-RC3 utilise désormais cette information pour annoncer le nom de la Voice au clavier.**
