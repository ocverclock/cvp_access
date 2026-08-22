# CVP Access — catalogue des actions clavier v1.5-RC4-dev

Ce fichier reflète `ACTION_SPECS` de `cvp_keyboard.py`.

`keyboard.toml` peut uniquement appeler les actions listées ici ; il n'exécute pas de Python arbitraire.

## Actions disponibles

| Action | Paramètre | Fonction |
|---|---:|---|
| `song_track_toggle:N` | 1..16 | Bascule une piste Song après lecture de l'état réel |
| `style_part_toggle:N` | 1..8 | Bascule une partie Style |
| `layer_toggle` | — | Layer / Dual ON/OFF |
| `left_toggle` | — | Left ON/OFF |
| `announce_tempo` | — | Annonce le tempo réel |
| `announce_transpose` | — | Annonce le transpose réel |
| `song_play_pause` | — | Play / Pause Song |
| `song_stop` | — | Stop Song |
| `song_position` | — | Annonce mesure / temps |
| `song_measure_previous` | — | Mesure -1 |
| `song_measure_next` | — | Mesure +1 |
| `song_measure_previous_5` | — | Mesure -5 |
| `song_measure_next_5` | — | Mesure +5 |
| `song_goto_measure` | — | Saisie directe d'une mesure |
| `song_loop_point_a` | — | Mémorise le point A |
| `song_loop_point_b` | — | Mémorise le point B |
| `song_loop_toggle` | — | Active/désactive la boucle A/B mémorisée |
| `style_start_stop` | — | Start / Stop Style |
| `style_intro:N` | 1..3 | Intro 1..3 |
| `style_main:N` | 1..4 | Main A..D |
| `style_fill:N` | 1..4 | Fill A..D |
| `style_break` | — | Break |
| `style_ending:N` | 1..3 | Ending 1..3 |
| `registration_recall:N` | 1..8 | Rappelle Registration Memory 1..8 |
| `song_volume_change:N` | -5..5 | Modifie le volume Song/MidiMaster ; défauts utilisés : ±1, ±5 |
| `main_volume_change:N` | -5..5 | Modifie le volume Main ; défauts utilisés : ±1, ±5 |
| `voice_volume_up` | — | Volume vocal + |
| `voice_volume_down` | — | Volume vocal - |
| `style_volume_up` | — | Volume Style +5 |
| `style_volume_down` | — | Volume Style -5 |
| `restart` | — | Quitte l'application ; systemd peut la relancer |

## Parties Style

```text
1 Rhythm 1
2 Rhythm 2
3 Bass
4 Chord 1
5 Chord 2
6 Pad
7 Phrase 1
8 Phrase 2
```

## Actions RC4 sans binding par défaut

Les actions suivantes existent dans le runtime mais ne sont volontairement affectées à aucune touche par défaut :

```text
style_intro:1..3
style_main:1..4
style_fill:1..4
style_break
style_ending:1..3
registration_recall:1..8
```

Le client peut les affecter librement dans `/etc/cvp-access/keyboard.toml`.

## Aide CTRL

`CTRL + touche assignée` annonce la fonction sans l'exécuter. `CTRL` est donc réservé à l'aide vocale dans le routeur CVP Access.

## Bindings intégrés de référence

Les principaux bindings par défaut restent :

```text
A Z E R T Y U I     Song 1..8
Q S D F G H J K     Song 9..16
TOP1..TOP8           parties Style 1..8
TOP9                 Layer
TOP0                 Left
F1                   tempo
F2                   transpose
F3                   goto mesure
F4                   point A
F5                   point B
F6                   loop A/B
F13                  Style Start/Stop
SPACE                Play/Pause
ENTER                Stop
P                    position
LEFT/RIGHT           mesure -/+1
SHIFT+LEFT/RIGHT     mesure -/+5
PAGEUP/PAGEDOWN      volume Style ±5
HOME/END             volume Song ±1
SHIFT+HOME/END       volume Song ±5
INSERT/DELETE        volume Main ±1
SHIFT+INSERT/DELETE  volume Main ±5
UP/DOWN              volume vocal
```

Pour la syntaxe détaillée des touches AZERTY et modificateurs, `cvp_keyboard.py --check` reste la référence exécutable.
