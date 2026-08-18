# CVP-909 read-only protocol probe

Generated: `2026-08-18T11:57:40.842195`

**Mode:** GET uniquement — aucun SET / RESET.

## Résumé

- DATA: 141
- EMPTY: 4
- TIMEOUT: 1

## Réponses avec données

| Propriété | Signature | Index | Canal/usage | Projet | HEX | Décodé |
|---|---|---:|---|---|---|---|
| piano_model | `0F 01 18 01` | `0x00` | Main | unexplored | `00 43 56 50 2D 39 30 35` | None |
| firmware_version | `0F 01 0B 01` | `0x00` | Main | unexplored | `00 31 2E 30 33` | None |
| guide | `04 03 00 01` | `0x00` | Main | unexplored | `00` | False |
| guide_type | `04 03 01 01` | `0x00` | Main | unexplored | `00` | 0 |
| song_length | `04 00 1B 01` | `0x00` | Main | unexplored | `00 01 00 01` | {"measure": 1, "beat": 1} |
| play | `04 00 05 01` | `0x00` | Main | partial | `00` | 0 |
| loop | `04 00 0D 01` | `0x00` | Main | unexplored | `00 00 01 00 01 00 02 00 01` | 00 00 01 00 01 00 02 00 01 |
| part | `04 00 0E 01` | `0x00` | Main | unexplored | `00` | False |
| part | `04 00 0E 01` | `0x01` | Layer | unexplored | `01` | True |
| part | `04 00 0E 01` | `0x02` | Left | unexplored | `01` | True |
| part | `04 00 0E 01` | `0x03` | index 0x03 | unexplored | `01` | True |
| part_channel | `04 00 0F 01` | `0x00` | Main | unexplored | `01` | 1 |
| part_channel | `04 00 0F 01` | `0x01` | Layer | unexplored | `02` | 2 |
| part_channel | `04 00 0F 01` | `0x02` | Left | unexplored | `02` | 2 |
| part_channel | `04 00 0F 01` | `0x03` | index 0x03 | unexplored | `02` | 2 |
| part_auto | `04 00 10 01` | `0x00` | Main | unexplored | `01` | True |
| present | `04 01 00 01` | `0x10` | Song 1 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x11` | Song 2 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x12` | Song 3 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x13` | Song 4 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x14` | Song 5 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x15` | Song 6 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x16` | Song 7 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x17` | Song 8 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x18` | Song 9 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x19` | Song 10 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x1A` | Song 11 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x1B` | Song 12 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x1C` | Song 13 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x1D` | Song 14 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x1E` | Song 15 | unexplored | `00` | False |
| present | `04 01 00 01` | `0x1F` | Song 16 | unexplored | `00` | False |
| stream_lights | `04 02 00 01` | `0x00` | Main | unexplored | `01` | True |
| stream_speed | `04 02 02 01` | `0x00` | Main | unexplored | `01` | 1 |
| volume | `0C 00 00 01` | `0x00` | Main | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x01` | Layer | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x02` | Left | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x10` | Song 1 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x11` | Song 2 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x12` | Song 3 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x13` | Song 4 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x14` | Song 5 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x15` | Song 6 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x16` | Song 7 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x17` | Song 8 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x18` | Song 9 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x19` | Song 10 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x1A` | Song 11 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x1B` | Song 12 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x1C` | Song 13 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x1D` | Song 14 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x1E` | Song 15 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x1F` | Song 16 | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x40` | Mic | partial | `64` | 100 |
| volume | `0C 00 00 01` | `0x41` | AuxIn | partial | `7F` | 127 |
| volume | `0C 00 00 01` | `0x44` | Wave | partial | `7F` | 127 |
| volume | `0C 00 00 01` | `0x50` | MidiMaster | partial | `64` | 100 |
| pan | `0C 00 03 01` | `0x00` | Main | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x01` | Layer | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x02` | Left | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x10` | Song 1 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x11` | Song 2 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x12` | Song 3 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x13` | Song 4 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x14` | Song 5 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x15` | Song 6 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x16` | Song 7 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x17` | Song 8 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x18` | Song 9 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x19` | Song 10 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x1A` | Song 11 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x1B` | Song 12 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x1C` | Song 13 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x1D` | Song 14 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x1E` | Song 15 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x1F` | Song 16 | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x40` | Mic | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x44` | Wave | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x50` | MidiMaster | unexplored | `40` | 64 |
| pan | `0C 00 03 01` | `0x51` | Style | unexplored | `40` | 64 |
| reverb | `0C 00 04 01` | `0x00` | Main | unexplored | `0D` | 13 |
| reverb | `0C 00 04 01` | `0x01` | Layer | unexplored | `23` | 35 |
| reverb | `0C 00 04 01` | `0x02` | Left | unexplored | `0A` | 10 |
| reverb | `0C 00 04 01` | `0x10` | Song 1 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x11` | Song 2 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x12` | Song 3 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x13` | Song 4 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x14` | Song 5 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x15` | Song 6 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x16` | Song 7 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x17` | Song 8 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x18` | Song 9 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x19` | Song 10 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x1A` | Song 11 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x1B` | Song 12 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x1C` | Song 13 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x1D` | Song 14 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x1E` | Song 15 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x1F` | Song 16 | unexplored | `28` | 40 |
| reverb | `0C 00 04 01` | `0x40` | Mic | unexplored | `14` | 20 |
| reverb | `0C 00 04 01` | `0x44` | Wave | unexplored | `14` | 20 |
| reverb | `0C 00 04 01` | `0x50` | MidiMaster | unexplored | `40` | 64 |
| reverb | `0C 00 04 01` | `0x51` | Style | unexplored | `40` | 64 |
| active | `0C 00 01 01` | `0x00` | Main | partial | `01` | True |
| active | `0C 00 01 01` | `0x40` | Mic | partial | `01` | True |
| active | `0C 00 01 01` | `0x44` | Wave | partial | `01` | True |
| active | `0C 00 01 01` | `0x50` | MidiMaster | partial | `01` | True |
| active | `0C 00 01 01` | `0x51` | Style | partial | `01` | True |
| reverb_effect | `0C 01 00 01` | `0x00` | Main | unexplored | `00 02 24` | 00 02 24 |
| voice_midi | `02 00 01 01` | `0x10` | Song 1 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x11` | Song 2 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x12` | Song 3 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x13` | Song 4 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x14` | Song 5 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x15` | Song 6 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x16` | Song 7 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x17` | Song 8 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x18` | Song 9 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x19` | Song 10 | unexplored | `03 7C 00 00` | 03 7C 00 00 |
| voice_midi | `02 00 01 01` | `0x1A` | Song 11 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x1B` | Song 12 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x1C` | Song 13 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x1D` | Song 14 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x1E` | Song 15 | unexplored | `00 00 00 00` | 00 00 00 00 |
| voice_midi | `02 00 01 01` | `0x1F` | Song 16 | unexplored | `00 00 00 00` | 00 00 00 00 |
| octave | `0C 00 12 01` | `0x00` | Main | unexplored | `00` | 0 |
| octave | `0C 00 12 01` | `0x01` | Layer | unexplored | `00` | 0 |
| octave | `0C 00 12 01` | `0x02` | Left | unexplored | `00` | 0 |
| split_point | `09 00 00 01` | `0x00` | Main | unexplored | `00` | 0 |
| lid_position | `02 02 07 01` | `0x00` | Main | unexplored | `00` | 0 |
| environment | `02 02 03 01` | `0x00` | Main | unexplored | `06` | 6 |
| brightness | `0C 00 0B 01` | `0x00` | Main | unexplored | `06` | 6 |
| touch_curve | `00 00 00 01` | `0x00` | Main | unexplored | `06` | 6 |
| fixed_curve | `00 00 01 01` | `0x00` | Main | unexplored | `06` | True |
| fixed_curve | `00 00 01 01` | `0x01` | Layer | unexplored | `06` | True |
| fixed_curve | `00 00 01 01` | `0x02` | Left | unexplored | `06` | True |
| fixed_velocity | `00 00 02 01` | `0x00` | Main | unexplored | `06` | 6 |
| master_tune | `03 00 00 01` | `0x00` | Main | unexplored | `00 06` | 6 |
| vrm | `02 02 00 01` | `0x00` | Main | unexplored | `01` | True |
| damper_resonance | `02 02 01 01` | `0x00` | Main | unexplored | `05` | 5 |
| string_resonance | `02 02 02 01` | `0x00` | Main | unexplored | `05` | 5 |

## Réponses vides

Une réponse `EMPTY` n'est **pas** considérée comme validation de propriété.

- `song_name` `04 00 01 01` index `0x00` (Main)
- `voice_preset` `02 00 00 01` index `0x00` (Main)
- `voice_preset` `02 00 00 01` index `0x01` (Layer)
- `voice_preset` `02 00 00 01` index `0x02` (Left)
