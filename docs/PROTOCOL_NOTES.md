# Yamaha CVP-909 — Notes de protocole MIDI / SysEx

Ce document regroupe les commandes MIDI/SysEx découvertes et **validées expérimentalement sur un Yamaha CVP-909** dans le cadre du projet CVP Access.

Ces informations peuvent être utiles pour d'autres projets de contrôle externe, d'accessibilité ou de reverse engineering du CVP-909.

## Configuration utilisée

* Yamaha CVP-909
* Raspberry Pi
* interface MIDI USB Prodipe
* liaison MIDI DIN avec le CVP-909
* réception et émission via `amidi`

---

## 1. Protocole Yamaha moderne utilisé par le CVP-909

Header observé :

```text
F0 43 73 01 52 25 26
```

### GET

Structure :

```text
F0 43 73 01 52 25 26
01 00
PP PP PP PP
II
01 00
F7
```

* `PP PP PP PP` = propriété
* `II` = index

### Réponse INFO

```text
F0 43 73 01 52 25 26
00 00
PP PP PP PP
II
01 00
00 LL
DATA...
F7
```

### SET

Structure :

```text
F0 43 73 01 52 25 26
01 01
PP PP PP PP
II
01 00
00 LL
DATA...
F7
```

---

# 2. Mute / Active

Propriété :

```text
0C 00 01 01
```

Valeurs :

```text
00 = OFF
01 = ON
```

## Pistes Song 1–16

Indexes validés :

```text
Piste 1  = 10
Piste 2  = 11
...
Piste 16 = 1F
```

Soit :

```text
index = 0x0F + numéro de piste
```

Exemple GET piste 1 :

```text
F0 43 73 01 52 25 26
01 00
0C 00 01 01
10
01 00
F7
```

Les 16 pistes Song sont actuellement contrôlables individuellement en GET + SET.

---

# 3. Main / Dual / Left

La même propriété `Active` est utilisée :

```text
0C 00 01 01
```

Indexes identifiés :

```text
00 = Main
01 = Layer / Dual
02 = Left
```

Dual et Left ont été validés en :

```text
GET
SET OFF
SET ON
GET de contrôle
```

Exemple Dual OFF :

```text
F0 43 73 01 52 25 26
01 01
0C 00 01 01
01
01 00
00 01
00
F7
```

Dual ON :

```text
...
01
F7
```

Left utilise exactement la même structure avec l'index `02`.

---

# 4. Tempo

Propriété :

```text
08 00 00 01
```

Index :

```text
00
```

Valeur sur deux octets.

Plage observée/documentée :

```text
5 à 280 BPM
```

Le GET est validé sur CVP-909.

---

# 5. Transpose

Propriété :

```text
0A 00 00 01
```

Index :

```text
02
```

Codage :

```text
40 = 0
```

Donc :

```text
valeur réelle = octet - 0x40
```

Plage :

```text
-12 à +12
```

GET validé.

---

# 6. Volume du Style / accompagnement

Propriété :

```text
0C 00 00 01
```

Index :

```text
51
```

Plage :

```text
0 à 127
```

GET et SET validés.

Exemple GET :

```text
F0 43 73 01 52 25 26
01 00
0C 00 00 01
51
01 00
F7
```

Exemple de réponse pour un volume de 100 :

```text
F0 43 73 01 52 25 26
00 00
0C 00 00 01
51
01 00
00 01
64
F7
```

`0x64 = 100`.

---

# 7. Les 8 parties du Style

Une seconde famille de SysEx Yamaha, plus ancienne, reste compatible avec le CVP-909.

Commande validée :

```text
F0 43 73 01 51 05 00 00 08
XX XX XX XX XX XX XX XX
F7
```

Les 8 octets correspondent à :

```text
1. Rhythm 1
2. Rhythm 2
3. Bass
4. Chord 1
5. Chord 2
6. Pad
7. Phrase 1
8. Phrase 2
```

Valeurs :

```text
00 = OFF
01 = ON
```

Exemple : couper uniquement Rhythm 1 :

```text
F0 43 73 01 51 05 00 00 08
00 01 01 01 01 01 01 01
F7
```

Couper uniquement Bass :

```text
F0 43 73 01 51 05 00 00 08
01 01 00 01 01 01 01 01
F7
```

Tout remettre ON :

```text
F0 43 73 01 51 05 00 00 08
01 01 01 01 01 01 01 01
F7
```

Les huit positions ont été testées individuellement et validées sur le CVP-909.

## Limitation importante

Aucune commande GET fiable n'a encore été trouvée pour récupérer directement les huit états.

La commande SET réécrit les huit valeurs en même temps.

CVP Access maintient donc un cache local des huit états.

---

# 8. Comportement lors d'un changement de Style

Une observation importante a été validée :

**changer de Style sur le CVP-909 réactive automatiquement les huit parties Style.**

Donc après un changement de Style :

```text
RHY1 = ON
RHY2 = ON
BASS = ON
CHD1 = ON
CHD2 = ON
PAD = ON
PHR1 = ON
PHR2 = ON
```

Cela permet de resynchroniser le cache local sans disposer d'un GET des huit parties.

---

# 9. Détection d'un changement de Style

Le CVP-909 envoie un ensemble important de messages MIDI lors d'un changement de Style.

Un marqueur particulièrement utile est la réception de Program Change sur les huit canaux MIDI correspondant aux parties Style :

```text
Canal 9  = Rhythm 1
Canal 10 = Rhythm 2
Canal 11 = Bass
Canal 12 = Chord 1
Canal 13 = Chord 2
Canal 14 = Pad
Canal 15 = Phrase 1
Canal 16 = Phrase 2
```

En MIDI brut, les Program Change correspondants utilisent :

```text
C8
C9
CA
CB
CC
CD
CE
CF
```

Lorsqu'un Program Change est reçu sur les huit canaux dans une courte fenêtre temporelle, CVP Access considère qu'un changement de Style vient d'avoir lieu.

Le cache des parties Style est alors automatiquement remis à :

```text
[ON, ON, ON, ON, ON, ON, ON, ON]
```

Sur les essais réalisés, les huit Program Change ont été reçus en environ `0,1 seconde`.

---

# 10. Principe de fiabilité utilisé par CVP Access

Lorsque le CVP permet un GET, l'état mémorisé par le Raspberry n'est pas considéré comme la source de vérité.

La logique utilisée est :

```text
GET état réel
→ calcul de la nouvelle valeur
→ SET
→ GET de vérification
→ annonce vocale
```

Ce principe est notamment utilisé pour :

```text
pistes Song
Dual
Left
volume Style
```

Il évite les désynchronisations lorsqu'un réglage est modifié directement depuis le CVP.

Pour les huit parties Style, aucun GET fiable n'étant actuellement disponible, le projet utilise :

```text
état initial connu
+
cache local
+
détection automatique du changement de Style
```

---

# 11. Mapping clavier actuel de CVP Access

Clavier AZERTY :

```text
&  é  "  '  (  -  è  _  ç  à
│  │  │  │  │  │  │  │  │  │
R1 R2 Bass C1 C2 Pad P1 P2 Dual Left
```

Pistes Song :

```text
A Z E R T Y U I  → Song 1–8
Q S D F G H J K  → Song 9–16
```

Autres commandes :

```text
↑ / ↓             volume de la voix
Page Up/Down      volume Style ±5
F1                annonce du tempo réel
F2                annonce du transpose réel
ESC               fermeture / redémarrage de l'application
```

---

# 12. État actuel des recherches

Validé sur CVP-909 :

```text
Song 1–16 Active        GET + SET
Dual / Layer Active     GET + SET
Left Active             GET + SET
Tempo                    GET
Transpose                GET
Volume Style             GET + SET
8 parties Style          SET
Changement de Style      détection MIDI
```

À rechercher :

```text
GET direct des 8 parties Style
sélection / identification du Style courant
commandes Start / Stop / Sync Start
Intro / Ending
Main A / B / C / D
Fill
autres paramètres utiles à l'accessibilité
```

---

## Remarque

Le CVP-909 semble accepter simultanément plusieurs générations de protocoles Yamaha :

```text
F0 43 73 01 52 25 26 ...
```

pour le protocole utilisé notamment par les fonctions modernes de contrôle,

et :

```text
F0 43 73 01 51 ...
F0 43 10 4C ...
```

pour différentes familles historiques de paramètres Yamaha/XG.

Cette compatibilité descendante ouvre probablement encore de nombreuses possibilités de contrôle qui ne sont pas documentées explicitement pour le CVP-909.
