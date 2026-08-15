# Catalogue des actions clavier — CVP Access v1.5

Ce fichier décrit les **actions autorisées** dans `keyboard.toml`.

Le fichier TOML ne contient jamais de Python et ne peut pas exécuter de
commande système. Il ne fait qu'associer une touche ou une combinaison à une
action présente dans ce catalogue.

## Syntaxe

```toml
[keys]
A = "song_track_toggle:1"
F1 = "announce_tempo"
"CAPS+A" = "song_position"
"CTRL+SPACE" = "song_stop"
```

Les actions avec `:nombre` utilisent un paramètre contrôlé par CVP Access.

## Actions disponibles

| Action | Paramètre | Fonction |
|---|---:|---|
| `song_track_toggle:N` | 1–16 | Bascule la piste Song N après lecture de son état réel |
| `style_part_toggle:N` | 1–8 | Bascule la partie Style N |
| `layer_toggle` | — | Bascule Layer / Dual |
| `left_toggle` | — | Bascule Left |
| `announce_tempo` | — | Lit et annonce le tempo réel |
| `announce_transpose` | — | Lit et annonce le transpose réel |
| `song_play_pause` | — | Lecture ↔ Pause |
| `song_stop` | — | Stop Song |
| `song_position` | — | Lit et annonce mesure / temps |
| `voice_volume_up` | — | Volume vocal +10 |
| `voice_volume_down` | — | Volume vocal −10 |
| `style_volume_up` | — | Volume Style +5, avec GET / SET / vérification |
| `style_volume_down` | — | Volume Style −5, avec GET / SET / vérification |
| `restart` | — | Quitte l'application ; systemd la redémarre |

### Parties Style

```text
1  Rhythm 1
2  Rhythm 2
3  Bass
4  Chord 1
5  Chord 2
6  Pad
7  Phrase 1
8  Phrase 2
```

## Touches

Les lettres sont nommées comme elles sont **imprimées sur un clavier AZERTY** :

```text
A Z E R T Y U I O P
Q S D F G H J K L M
W X C V B N
```

La rangée des chiffres utilise des noms physiques stables :

```text
TOP1 = & / 1
TOP2 = é / 2
TOP3 = " / 3
TOP4 = ' / 4
TOP5 = ( / 5
TOP6 = - / 6
TOP7 = è / 7
TOP8 = _ / 8
TOP9 = ç / 9
TOP0 = à / 0
```

Les autres touches imprimables françaises disposent également d'un nom stable :

```text
RPAREN       ) / °
EQUAL        = / +
CARET        ^ / ¨
DOLLAR       $ / £
U_GRAVE      ù / %
ASTERISK     * / µ
COMMA        , / ?
SEMICOLON    ; / .
COLON        : / /
EXCLAMATION  ! / §
LESS         < / >
```

Touches supplémentaires reconnues :

```text
F1 ... F12
ESC
TAB
SPACE
ENTER
BACKSPACE
PRINT SCROLLLOCK PAUSE NUMLOCK
UP DOWN LEFT RIGHT
PAGEUP PAGEDOWN
HOME END INSERT DELETE
KP0 ... KP9
KPENTER KPPLUS KPMINUS KPDOT KPSLASH KPASTERISK
```

## Combinaisons

Modificateurs reconnus :

```text
SHIFT
CTRL
ALT
ALTGR
META
CAPS
```

Exemples :

```toml
"SHIFT+A" = "announce_tempo"
"CTRL+F1" = "song_position"
"ALT+SPACE" = "song_stop"
"CAPS+A" = "song_track_toggle:16"
"CAPS+SHIFT+A" = "announce_transpose"
```

L'ordre écrit dans le TOML n'est pas important : CVP Access normalise les
modificateurs.

## Caps Lock

En v1.5, `CAPSLOCK` n'est plus une touche texte : elle commute une **deuxième
couche de commandes CVP Access**.

```text
Caps Lock OFF : A      -> action de A
Caps Lock ON  : CAPS+A -> action de CAPS+A
```

Par défaut :

```toml
caps_fallback_to_base = true
```

Ainsi, si `CAPS+A` n'existe pas, la touche A conserve son action normale. Pour
un second clavier totalement indépendant :

```toml
caps_fallback_to_base = false
```

## Ce qui n'est volontairement pas implémenté

La v1.5 ne donne aucun sens spécial à :

- pression longue ;
- double pression ;
- triple pression ;
- répétition automatique d'une touche.

Ces fonctions pourront être étudiées plus tard, mais ne sont pas nécessaires
pour obtenir un clavier largement configurable avec les modificateurs et la
couche Caps Lock.

## Validation

La configuration peut être contrôlée sans lancer le piano :

```bash
python3 cvp_keyboard.py --check /etc/cvp-access/keyboard.toml
```

Une action inconnue, une piste 17, une partie Style 9 ou une touche inconnue est
signalée comme erreur.

## Génération vocale liée aux actions

Avec :

```toml
[speech]
generation = "configured"
```

CVP Access inspecte les actions réellement présentes dans `[keys]` et ne
pré-génère que les WAV nécessaires. Les affectations dupliquées sont
automatiquement dédupliquées.

Les fonctions Yamaha/ConPianist connues mais pas encore exposées au clavier
sont suivies dans :

```text
docs/FUNCTION_CATALOG.md
```
