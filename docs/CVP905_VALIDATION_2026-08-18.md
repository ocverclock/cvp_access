# Validation matérielle CVP-905 — 18 août 2026

## Matériel

- Yamaha **CVP-905**
- Firmware **1.03**
- Raspberry Pi / Debian
- Interface MIDI : ProdipeMIDIlilo en MIDI DIN
- Audio vocal : USB Audio du Clavinova

## Résumé

La campagne a confirmé sur le CVP-905 réel : transport Song, position mesure/temps, boucle A/B en GET et SET, Guide, plusieurs fonctions mixer, Voice MIDI, présence des pistes, modèle et firmware.

Elle a aussi montré que plusieurs signatures issues de ConPianist/CSP ne doivent pas être supposées identiques sur CVP-905.

## Transport Song

Signature `04 00 05 01`, index `00` :

```text
00 = Stop
01 = Play
02 = Pause
```

Validé avec un vrai Song chargé.

## Position Song

Signature `04 00 0A 01`, index `00`.

GET validé :

```text
bytes 0-1 = mesure 14-bit
bytes 2-3 = temps 14-bit
```

Exemples :

```text
00 01 00 01 = mesure 1, temps 1
00 01 00 04 = mesure 1, temps 4
00 02 00 01 = mesure 2, temps 1
00 05 00 01 = mesure 5, temps 1
```

Le SET direct reste à confirmer formellement avec lecture après écriture.

## Boucle A/B — résultat majeur

Signature `04 00 0D 01`, index `00`.

Structure 9 octets validée :

```text
byte 0      = état boucle
bytes 1-2   = mesure A
bytes 3-4   = temps A
bytes 5-6   = mesure B
bytes 7-8   = temps B
```

Exemple SET direct validé pour A=15:1 / B=16:1 :

```text
01 00 0F 00 01 00 10 00 01
```

Quand le Loop est désactivé, le CVP efface ses bornes et revient à :

```text
00 00 01 00 01 00 02 00 01
```

Un nouveau SET complet restaure immédiatement la boucle 15→16.

### Conséquence produit

CVP Access doit conserver `loop_A` et `loop_B` localement.

Fonctions prévues :

```text
Point A
Point B
Boucle ON/OFF
Mesure -
Mesure +
Shift + Mesure -
Shift + Mesure +
Aller à la mesure
```

Les points A/B seront placés au début des mesures, temps 1.

Cette fonction est utile aussi à un musicien voyant : elle évite de redéfinir manuellement la boucle après chaque arrêt.

## Guide

`04 03 00 01`, index `00` :

```text
00 = OFF
01 = ON
```

GET/SET validés. `guide_type` a également passé un test GET→SET→GET→restore.

## Mixer et Voice

Validé dynamiquement :

- Volume/Pan/Reverb Main ;
- Volume/Pan/Reverb Layer ;
- Voice MIDI Main/Layer/Left ;
- Type de réverb globale.

Voice MIDI : `02 00 01 01`, valeurs 4 octets dynamiques.

Exemple Main :

```text
03 30 00 00
→ 00 20 40 71
→ 00 20 40 1D
→ 00 20 46 01
→ 03 20 12 19
```

## Identification

Modèle :

```text
raw : 00 43 56 50 2D 39 30 35
→ CVP-905
```

Firmware :

```text
raw : 00 31 2E 30 33
→ 1.03
```

Le décodeur texte du probe doit être corrigé pour le format Yamaha par groupes de 7 caractères + masque.

## Détection de Song chargé

Sans Song :

- `song_name` EMPTY ;
- pistes présentes = false ;
- `song_length` renvoie malgré tout `1:1`.

Avec Song :

- `song_name` contient des données ;
- pistes présentes = true sur le fichier testé ;
- longueur réelle retournée.

Critère candidat :

```text
song_name EMPTY
ET
aucune piste présente
```

À intégrer au runtime pour annoncer « Aucun Song chargé ».

## SET fonctionnels validés

- Guide ON/OFF
- Guide Type
- Stream Lights
- Part Auto
- Parties pédagogiques indexes 00, 01, 02
- VRM
- Main Active
- Mic Active
- Lid Position
- Environment
- Damper Resonance
- String Resonance
- Volume Main/Layer/Left/Song1/Mic/AuxIn/Wave/MidiMaster
- Pan Main/Layer/Left/Song1/Style
- Reverb Main/Layer/Left/Song1/Style

## Alerte `0x31`

Ont produit `0x31` après un SET naïf :

- Active Wave index 44
- partie pédagogique index 03
- Stream Speed
- Brightness

Règle : arrêter le test et ne pas considérer la propriété comme bool/u7.

## Mis de côté / non résolu CVP-905

- Touch Curve
- Fixed Curve
- Fixed Velocity
- Master Tune
- Brightness
- Split Point
- Key-Off Sampling
- Stream Speed
- Octave Main/Layer/Left

Ces signatures restent utiles au catalogue Yamaha général et ne doivent pas être supprimées.

## Prochaines validations prioritaires

1. SET direct de Song Position avec GET de preuve.
2. Détection « aucun Song chargé » dans le runtime.
3. Implémentation du Loop mémorisé et navigation par mesures.
4. Correction du décodeur texte Yamaha.
5. Étendre Volume/Pan/Reverb aux 16 pistes seulement si nécessaire.
6. Décoder Voice MIDI uniquement si une fonction utilisateur en dépend.
