# Politique de retour utilisateur — CVP Access 1.6.1-RC1

Date de consolidation : 25 septembre 2026.

## Principe

CVP Access distingue désormais trois types de retour :

1. **voix** pour une information, un état ou une confirmation qui n'est pas
   évidente sans écran ;
2. **signal sonore très court** pour une navigation qui doit rester instantanée ;
3. **silence volontaire** lorsque l'action produit immédiatement son propre
   résultat audible et qu'une annonce masquerait ce résultat.

Le chemin critique ne doit pas attendre une synthèse Piper.

## Clavier configuré

Le profil par défaut contient **83 affectations** correspondant à **37 actions
uniques**. Ces actions gardent le comportement vocal validé : états de pistes,
parties Style, volumes, informations Song/Style/Voice, tempo, transpose,
position, boucles, métronome, transport et relance.

Les actions Style Section / Registration non affectées par défaut conservent
également leur confirmation vocale lorsqu'elles sont configurées.

## Dictaphone MIDI

| Commande | Retour |
| --- | --- |
| F14 court | bip/glissando descendant, sans voix |
| F16 court | bip/glissando montant, sans voix |
| F14/F16 maintenu ~0,8 s | annonce du morceau sélectionné, sans bip |
| F15 court au repos | démarrage immédiat de la lecture, sans annonce |
| F15 court pendant lecture | « Lecture arrêtée » |
| F15 long au repos | « Enregistrement prêt » |
| première note après armement | aucune annonce ; l'enregistrement commence |
| F15 court avant première note | « Enregistrement annulé » |
| F15 court pendant enregistrement | « Stop » immédiatement, puis annonce de sauvegarde |
| fin naturelle de lecture | « Lecture terminée » |

Les bips F14/F16 sont des WAV générés par SoX et joués directement. Ils
n'utilisent pas Piper.

L'annonce standard d'une sélection datée assemble des fragments WAV
pré-générés (jour, mois, « numéro », index). Piper n'est utilisé qu'en secours
pour un nom de fichier non standard ou une valeur hors banque pré-générée.

## Guide vocal

La touche **M** coupe ou réactive uniquement le guide vocal CVP Access.

- passage vers OFF : **pas d'annonce** ; le silence immédiat est la confirmation ;
- retour vers ON : annonce « Guide vocal activé ».

Les bips de navigation du Recorder suivent le mute du guide vocal. Les retours directs « Stop », l'annonce de sélection et l'annonce de relance ESC respectent également ce mute ; aucune voie de lecture directe ne doit le contourner.

## Aide CTRL

`CTRL + touche` annonce la fonction sans l'exécuter.

Les touches réservées au Recorder suivent la même règle :

- CTRL+F14 : aide « morceau précédent » ;
- CTRL+F15 : aide dictaphone ;
- CTRL+F16 : aide « morceau suivant ».

## Règle de performance

Ne pas ajouter de Piper dynamique avant une action temporelle.

Ordre de préférence :

```text
WAV direct / cue
-> fragments WAV pré-générés
-> cache Piper existant
-> Piper dynamique
```

Une annonce longue peut être générée après un retour court immédiat, comme pour
l'arrêt/sauvegarde du Recorder.

## Point volontairement conservé

Le transport Song Yamaha (Play/Pause/Stop) et le transport Style continuent à
annoncer leur état, car ce comportement est déjà validé et fait partie du guide
d'accessibilité historique. Une suppression future de ces annonces devra être
testée en usage réel avant modification.


## Touches réservées

F14, F15 et F16 sont réservées au Recorder en 1.6.x et sont interceptées avant
le routeur TOML. Une ancienne personnalisation TOML sur ces touches est donc
conservée dans le fichier mais ignorée à l'exécution. La carte clavier affiche
toujours la fonction Recorder et signale le conflit ; le Doctor émet un WARN.


## Terminologie

Terminologie utilisateur retenue :

```text
Dictaphone MIDI       = fonction globale d'enregistrement/lecture
Enregistrements MIDI = fichiers visibles dans le portail / Samba
Recorder              = nom technique interne du contrôleur Python
Guide Yamaha          = fonction Guide du CVP
Guide vocal           = voix et signaux CVP Access
Morceau               = enregistrement MIDI sélectionné avec F14/F16
```

Les libellés utilisateur ne doivent pas exposer les noms techniques
`STATE_ARMED`, `RecorderController`, `aplaymidi`, etc.

## Matrice des commandes du layout par défaut

### Retour vocal après action

Ces commandes annoncent leur résultat ou l'information demandée :

```text
1..8                  parties Style ON/OFF
9 / 0                 Layer / Left
) / °                 toutes les parties Style ON
A..K                  pistes Song ON/OFF
Maj+A..K              Solo piste 1..16
L                     toutes les pistes Song ON
W / X / C             nom Style / nom Song / longueur Song
V                     Syncro Start
B                     Guide Yamaha
N / , / ;             noms Voice Main / Layer / Left
F1 / F2               tempo / transpose
F3                    aller à une mesure
F4 / F5 / F6          points A / B / boucle
F7                    métronome
F13                   Style Start / Stop
Espace / Entrée       Song Play-Pause / Stop
P                     position Song
← / →                 mesure précédente / suivante
Maj+← / Maj+→         déplacement de cinq mesures
↑ / ↓                 volume du guide vocal
Page↑ / Page↓         volume Style ±1
Maj+Page↑ / Page↓     volume Style ±5
Origine / Fin         volume Song ±1
Maj+Origine / Fin     volume Song ±5
Inser / Suppr         volume Main ±1
Maj+Inser / Suppr     volume Main ±5
```

### Retour conditionnel

```text
M
  vers OFF -> silence immédiat, aucune phrase
  vers ON  -> « Guide vocal activé »

ESC
  guide vocal actif -> annonce de relance puis restart
  guide vocal muet  -> restart silencieux

CTRL + commande
  -> annonce de l'aide uniquement, commande non exécutée
```

### Retour non vocal / silence volontaire

```text
F14 court -> cue descendant
F16 court -> cue montant
F14/F16 long -> annonce du morceau, sans cue
F15 lecture -> départ MIDI silencieux
première note après armement -> début d'enregistrement silencieux
F15 arrêt enregistrement -> « Stop » court puis confirmation détaillée
```

Cette matrice constitue la référence d'ergonomie pour 1.6.1. Toute nouvelle
commande doit choisir explicitement l'une de ces catégories au lieu d'hériter
accidentellement d'un comportement vocal.
