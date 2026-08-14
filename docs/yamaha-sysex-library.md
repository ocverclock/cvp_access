Oui. Je créerais un fichier **`docs/yamaha-sysex-library.md`**. L’objectif est différent du README : ici, on conserve **tout ce qu’on connaît du protocole**, même les fonctions que nous n’utilisons pas encore.

Je distinguerais clairement :

* ✅ **testé sur notre CVP-909**
* 🟡 **présent dans ConPianist, pas encore testé sur CVP-909**
* ⚠️ **point à vérifier / incohérence dans le code source**

ConPianist définit six types d’actions et 38 propriétés Yamaha distinctes ; il fournit aussi les index de canaux et les plages de valeurs utilisées par son contrôleur. 

# Yamaha CVP/CSP SysEx Library

## 1. Préfixe général

Le protocole identifié par ConPianist utilise ce préfixe propriétaire Yamaha :

```text
43 73 01 52 25 26
```

Sur le câble MIDI, le message SysEx complet est encadré par :

```text
F0 43 73 01 52 25 26 ... F7
```

Le code ConPianist construit ensuite le message avec une action de 2 octets, une propriété de 4 octets, puis selon l’action un index, une longueur et une valeur. 

---

## 2. Actions connues

| Action   | Octets  | Fonction                                      |
| -------- | ------- | --------------------------------------------- |
| GET      | `01 00` | Demander une valeur au piano                  |
| SET      | `01 01` | Modifier une valeur                           |
| INFO     | `00 00` | Valeur envoyée par le piano                   |
| RESPONSE | `00 01` | Réponse du piano après SET                    |
| RESET    | `04 01` | Remettre une propriété à sa valeur par défaut |
| EVENTS   | `02 00` | Demander au piano de signaler les changements |

Ces signatures et leurs formats sont directement définis dans `PianoMessage.cpp`. 

### GET

```text
F0
43 73 01 52 25 26
01 00
PP PP PP PP
II
01 00
F7
```

avec :

```text
PP PP PP PP = propriété
II          = index
```

### SET

```text
F0
43 73 01 52 25 26
01 01
PP PP PP PP
II
01 00
LL LL
VALEUR...
F7
```

Pour une valeur d’un octet :

```text
LL LL = 00 01
```

Pour deux octets :

```text
LL LL = 00 02
```

Les nombres multi-octets sont encodés par ConPianist en groupes de **7 bits**, ce qui est important notamment pour le tempo. 

---

# 3. Index des canaux

ConPianist définit notamment ces index : 

| Partie      | Index |
| ----------- | ----: |
| Main        |  `00` |
| Layer       |  `01` |
| Left        |  `02` |
| MIDI 1      |  `10` |
| MIDI 2      |  `11` |
| MIDI 3      |  `12` |
| MIDI 4      |  `13` |
| MIDI 5      |  `14` |
| MIDI 6      |  `15` |
| MIDI 7      |  `16` |
| MIDI 8      |  `17` |
| MIDI 9      |  `18` |
| MIDI 10     |  `19` |
| MIDI 11     |  `1A` |
| MIDI 12     |  `1B` |
| MIDI 13     |  `1C` |
| MIDI 14     |  `1D` |
| MIDI 15     |  `1E` |
| MIDI 16     |  `1F` |
| Micro       |  `40` |
| Aux In      |  `41` |
| Wave        |  `44` |
| MIDI Master |  `50` |
| Style       |  `51` |

Pour notre projet :

```text
index piste = 0x0F + numéro de piste
```

---

# 4. Bibliothèque des propriétés

## Identification

ConPianist expose deux propriétés d’identification à longueur variable. 

| Fonction         | Propriété     | Valeur | CVP-909 |
| ---------------- | ------------- | ------ | ------- |
| Modèle du piano  | `0F 01 18 01` | texte  | 🟡      |
| Version firmware | `0F 01 0B 01` | texte  | 🟡      |

Cela pourrait permettre plus tard à CVP Access d’annoncer ou journaliser automatiquement :

```text
Yamaha CVP-909
Firmware x.xx
```

---

# 5. Song — lecture

Ces propriétés sont utilisées par ConPianist pour contrôler et suivre la lecture du Song. 

| Fonction        | Propriété     | Valeur                        | CVP-909 |
| --------------- | ------------- | ----------------------------- | ------- |
| Play/Stop/Pause | `04 00 05 01` | `0` Stop, `1` Play, `2` Pause | 🟡      |
| Position        | `04 00 0A 01` | mesure + beat, 4 octets       | 🟡      |
| Longueur Song   | `04 00 1B 01` | mesure + beat, 4 octets       | 🟡      |
| Nom du Song     | `04 00 01 01` | texte                         | 🟡      |
| Reset Song      | `04 00 00 01` | aucune valeur                 | 🟡      |
| Boucle A/B      | `04 00 0D 01` | 9 octets                      | 🟡      |

### Play

```text
00 = Stop
01 = Play
02 = Pause
```

La même propriété sert donc aux trois commandes.

---

# 6. Song — pistes 1 à 16

## Active / Mute ✅

```text
Propriété : 0C 00 01 01
```

Valeur :

```text
00 = inactive / mute
01 = active / unmute
```

Cette propriété est définie comme `Active` dans ConPianist et est utilisée en GET et SET. 

### Statut CVP-909

**✅ GET validé**
**✅ SET validé**

### Piste 1 OFF

```text
F0 43 73 01 52 25 26
01 01
0C 00 01 01
10
01 00
00 01
00
F7
```

### Piste 1 ON

```text
F0 43 73 01 52 25 26
01 01
0C 00 01 01
10
01 00
00 01
01
F7
```

### GET piste 1

```text
F0 43 73 01 52 25 26
01 00
0C 00 01 01
10
01 00
F7
```

Réponse réellement obtenue sur le CVP-909 :

```text
F0 43 73 01 52 25 26
00 00
0C 00 01 01
10
01 00
00 01
01
F7
```

Dernier octet :

```text
01 = active
00 = coupée
```

---

## Présence d'une piste

```text
Propriété : 04 01 00 01
```

Valeurs :

```text
00 = canal absent du fichier MIDI
01 = canal présent dans le Song MIDI
```

ConPianist interroge cette propriété pour chacune des pistes MIDI 1 à 16. 

**CVP-909 : 🟡 à tester**

Très intéressant pour CVP Access : on pourrait annoncer seulement les pistes réellement utilisées.

---

# 7. Volume des canaux

```text
Propriété : 0C 00 00 01
Index : canal
Valeur : 0–127
```

ConPianist fournit GET, SET et RESET pour cette propriété. 

**CVP-909 : 🟡 à tester**

Potentiellement :

```text
Volume piste 4 : 96
```

---

# 8. Panoramique

```text
Propriété : 0C 00 03 01
Index : canal
Valeur brute : 0–127
Centre : 0x40
```

ConPianist ajoute `0x40` à la valeur logique lors d’un SET et la retire à la réception. 

**CVP-909 : 🟡**

---

# 9. Réverbération par canal

```text
Propriété : 0C 00 04 01
Index : canal
Valeur : 0–127
```

GET, SET et RESET existent dans ConPianist. 

**CVP-909 : 🟡**

---

# 10. Octave

```text
Propriété : 0C 00 12 01
Index : canal
Valeur logique : -2 à +2
Base : 0x40
```

Donc :

```text
3E = -2
3F = -1
40 =  0
41 = +1
42 = +2
```

ConPianist utilise cette propriété principalement pour `Main`, `Layer` et `Left`. 

**CVP-909 : 🟡**

---

# 11. Tempo ✅

```text
Propriété : 08 00 00 01
Valeur : 5–280 BPM
Longueur : 2 octets
```

ConPianist permet GET, SET et RESET du tempo. 

**✅ GET validé sur CVP-909**

### GET

```text
F0 43 73 01 52 25 26
01 00
08 00 00 01
00
01 00
F7
```

Réponse réellement obtenue :

```text
F0 43 73 01 52 25 26
00 00
08 00 00 01
00
01 00
00 02
00 64
F7
```

```text
00 64 = 100 BPM
```

Nous avons également lu correctement :

```text
83 BPM
```

après modification du tempo sur le CVP.

**SET : 🟡 pas encore testé sur CVP-909**

---

# 12. Transpose ✅

```text
Propriété : 0A 00 00 01
Index : 02
Valeur : -12 à +12
Base : 0x40
```

ConPianist encode le transpose comme `valeur + 0x40`. 

Exemples :

```text
34 = -12
3F = -1
40 =  0
41 = +1
47 = +7
4C = +12
```

**✅ GET validé sur CVP-909**

### GET

```text
F0 43 73 01 52 25 26
01 00
0A 00 00 01
02
01 00
F7
```

Valeurs réellement obtenues :

```text
40 → transpose 0
47 → transpose +7
```

**SET : 🟡 pas encore testé**

---

# 13. Instrument / Voice

Deux méthodes sont présentes dans ConPianist. 

### Voice Preset

```text
Propriété : 02 00 00 01
Index : canal
Valeur : nom/path du preset
```

Exemple de chemin utilisé par ConPianist :

```text
PRESET:/VOICE/Piano/Grand Piano/...
```

### Voice MIDI

```text
Propriété : 02 00 01 01
Index : canal
Longueur : 4 octets
```

Le contenu encode notamment :

```text
MSB
LSB
Program Change
```

**CVP-909 : 🟡**

C’est potentiellement très intéressant pour annoncer :

> « Piste 4 : Strings »

---

# 14. Parties Right / Left / Backing

### Activation

```text
Propriété : 04 00 0E 01
Valeur : 0/1
```

### Attribution d’un canal

```text
Propriété : 04 00 0F 01
```

### Attribution automatique

```text
Propriété : 04 00 10 01
Valeur : 0/1
```

ConPianist fournit GET et SET pour ces fonctions. 

**CVP-909 : 🟡**

⚠️ Il existe une petite incohérence dans le code source ConPianist concernant l’index `Backing` : un commentaire indique `3`, tandis que l’énumération du contrôleur utilise `2`. À tester avant utilisation. 

---

# 15. Guide Yamaha

Attention : il s’agit du **Guide pédagogique Yamaha**, pas du Voice Guide d’accessibilité.

### Guide

```text
Propriété : 04 03 00 01

00 = OFF
01 = ON
```

### Type de Guide

```text
Propriété : 04 03 01 01

00 = Correct Key
01 = Any Key
05 = Your Tempo
```

ConPianist expose les deux en GET/SET. 

**CVP-909 : 🟡**

---

# 16. Stream Lights

```text
ON/OFF :
04 02 00 01

00 = OFF
01 = ON
```

Vitesse :

```text
04 02 02 01

00 = Slow
01 = Fast
```

Ces fonctions sont présentes dans ConPianist pour les instruments compatibles Stream Lights. 

**CVP-909 : 🟡 probablement sans intérêt selon équipement**

---

# 17. Split Point

```text
Propriété : 09 00 00 01
Valeur : notes MIDI 21 (A1) à 108 (C7)
```

SET et réception sont implémentés dans ConPianist. 

**CVP-909 : 🟡**

---

# 18. Reverb Effect

```text
Propriété : 0C 01 00 01
Longueur : 3 octets
```

Le preset par défaut choisi par ConPianist correspond à `0x0118`, décrit dans son contrôleur comme **Recital Hall**. 

**CVP-909 : 🟡**

---

# 19. Piano Room

ConPianist contient toute une famille de propriétés liées au moteur piano. 

| Fonction         | Propriété     | Valeur                                   |
| ---------------- | ------------- | ---------------------------------------- |
| Lid Position     | `02 02 07 01` | `0` ouvert, `1` demi-ouvert, `2` fermé   |
| Environment      | `02 02 03 01` | `00–7F`                                  |
| Brightness       | `0C 00 0B 01` | `2E` Mellow → `40` Default → `7F` Bright |
| Touch Curve      | `00 00 00 01` | 0–4                                      |
| Fixed Curve      | `00 00 01 01` | 0/1 par Main/Layer/Left                  |
| Fixed Velocity   | `00 00 02 01` | `00–7F`                                  |
| Master Tune      | `03 00 00 01` | 2 octets                                 |
| VRM              | `02 02 00 01` | 0/1                                      |
| Damper Resonance | `02 02 01 01` | 0–10                                     |
| String Resonance | `02 02 02 01` | 0–10                                     |
| Key-Off Sampling | `02 02 06 01` | `00–50`                                  |

**Toutes : 🟡 non testées sur CVP-909.**

### Touch Curve

```text
0 = Soft 2
1 = Soft 1
2 = Medium
3 = Hard 1
4 = Hard 2
```

### Master Tune

La documentation interne de ConPianist indique approximativement :

```text
raw 4       → 414.8 Hz
raw 1024    → 440.0 Hz
raw 2047    → 466.8 Hz
```

Le contrôleur applique une transformation autour d’une base `0x400`. 

---

# 20. Local Control

Celui-ci n’utilise **pas** le SysEx propriétaire précédent.

ConPianist utilise un MIDI Control Change standard :

```text
CC 122
```

sur le canal MIDI 1 :

```text
0   = Local Control OFF
127 = Local Control ON
```

Le contrôleur ConPianist construit explicitement ce message avec `controllerEvent(1, 122, ...)`. 

**CVP-909 : 🟡**

---

# 21. EVENTS — très intéressant

ConPianist peut demander au piano d’émettre automatiquement les changements de nombreuses propriétés avec :

```text
02 00
```

Le programme active notamment les événements pour :

```text
Volume
Pan
Reverb
Octave
Tempo
Transpose
Reverb Effect
Loop
Voice
Active
Present
Song Name
Split Point
Lid Position
Environment
Brightness
Touch Curve
Fixed Curve
Fixed Velocity
Master Tune
VRM
Damper Resonance
String Resonance
Key-Off Sampling
```



C’est probablement **une des fonctions les plus intéressantes à tester ensuite sur le CVP-909**.

Au lieu de faire :

```text
Raspberry → GET tempo
Raspberry → GET transpose
Raspberry → GET mute...
```

on pourrait potentiellement faire au démarrage :

```text
EVENTS Tempo
EVENTS Transpose
EVENTS Active
...
```

puis le CVP informerait spontanément le Raspberry lorsqu’un paramètre change.

Cela permettrait de rester synchronisé même lorsque l’utilisateur change quelque chose directement sur l’écran du CVP.

---

# 22. État de validation CVP-909

À ce stade :

| Fonction                | GET | SET |
| ----------------------- | --: | --: |
| Active pistes 1–16      |   ✅ |   ✅ |
| Tempo                   |   ✅ |  🟡 |
| Transpose               |   ✅ |  🟡 |
| Present                 |  🟡 |   — |
| Volume piste            |  🟡 |  🟡 |
| Pan                     |  🟡 |  🟡 |
| Reverb                  |  🟡 |  🟡 |
| Voice                   |  🟡 |  🟡 |
| Play/Pause/Stop         |  🟡 |  🟡 |
| Position                |  🟡 |  🟡 |
| Song Name               |  🟡 |   — |
| Guide                   |  🟡 |  🟡 |
| Part Right/Left/Backing |  🟡 |  🟡 |
| Split Point             |  🟡 |  🟡 |
| Piano Room              |  🟡 |  🟡 |
| EVENTS                  |  🟡 |   — |

**Important :** les ✅ ci-dessus correspondent à nos tests réels sur le CVP-909 via l’interface MIDI DIN Prodipe. Les 🟡 signifient seulement que la propriété existe et est utilisée par ConPianist ; cela ne prouve pas encore qu’elle fonctionne sur le CVP-909.

---

## Ce que je testerais ensuite

Trois commandes ont beaucoup plus de valeur que les autres pour notre projet :

**`Present`**, pour connaître automatiquement quelles pistes 1–16 existent réellement dans le morceau ; **`SongName`**, pour que le Raspberry puisse annoncer le titre chargé ; et surtout **`EVENTS`**, pour voir si le CVP peut notifier spontanément le Raspberry lorsqu’un mute, le tempo ou le transpose change.

Si `EVENTS` fonctionne sur le CVP-909, on améliore fortement l’architecture : on passe d’une interface qui **interroge le piano** à une interface qui **reste synchronisée en temps réel avec lui**. 

