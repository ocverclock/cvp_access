# CVP-905 — checkpoint protocole RC3

Testé sur Yamaha CVP-905 firmware 1.03.

## Validé GET + SET

### Métronome

- Propriété : `07 00 00 01`
- Index : `00`
- `00` = OFF
- `01` = ON
- GET validé
- SET validé

Comportement CVP observé : une navigation Song vers une mesure antérieure
coupe le métronome. `cvp_song.py` mémorise désormais son état avant une
navigation arrière et le remet ON uniquement s'il était ON auparavant.

Cela couvre :
- LEFT : mesure -1
- SHIFT+LEFT : mesure -5
- F3 : aller à une mesure inférieure à la position courante

### Song position

- Propriété : `04 00 0A 01`
- Index : `00`
- DATA : mesure 14-bit + temps 14-bit

### Song Loop A/B

- Propriété : `04 00 0D 01`
- Index : `00`
- Mémoire A/B locale conservée quand Loop passe OFF.

## Observé GET, SET à valider

### Style Start/Stop

- Propriété candidate : `06 00 03 01`
- Index de référence : `00`
- STOP = `00`
- START = `01`
- Diff STOP -> START -> STOP reproductible
- SET non encore validé : ne pas intégrer au runtime avant validation.

## Non trouvé pour le moment

### Chord Fingering Type

Aucun changement reproductible détecté :
- Fingered -> AI Full Keyboard -> Fingered
- brute-force 1 048 576 couples dans l'espace testé
- retest avec ACMP + Style actif : aucun candidat

À reprendre plus tard par une autre voie, notamment diff de Registration/Backup.
