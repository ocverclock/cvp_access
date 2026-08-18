# CVP functional validation - wave 1

Generated: `2026-08-18T12:19:47.037815`

## Résumé

- PASS: 24

## Tests

| Test | Signature | Index | Initial | Test | Observé | Restauré | Statut |
|---|---|---:|---|---|---|---|---|
| guide | `04 03 00 01` | `0x00` | `00` | `01` | `01` | `00` | PASS |
| stream_lights | `04 02 00 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| part_auto | `04 00 10 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| vrm | `02 02 00 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| active_main | `0C 00 01 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| active_mic | `0C 00 01 01` | `0x40` | `01` | `00` | `00` | `01` | PASS |
| volume_main | `0C 00 00 01` | `0x00` | `64` | `65` | `65` | `64` | PASS |
| volume_layer | `0C 00 00 01` | `0x01` | `64` | `65` | `65` | `64` | PASS |
| volume_left | `0C 00 00 01` | `0x02` | `64` | `65` | `65` | `64` | PASS |
| volume_song_1 | `0C 00 00 01` | `0x10` | `64` | `65` | `65` | `64` | PASS |
| volume_mic | `0C 00 00 01` | `0x40` | `64` | `65` | `65` | `64` | PASS |
| volume_auxin | `0C 00 00 01` | `0x41` | `7F` | `7E` | `7E` | `7F` | PASS |
| volume_wave | `0C 00 00 01` | `0x44` | `7F` | `7E` | `7E` | `7F` | PASS |
| volume_midi_master | `0C 00 00 01` | `0x50` | `64` | `65` | `65` | `64` | PASS |
| pan_main | `0C 00 03 01` | `0x00` | `40` | `41` | `41` | `40` | PASS |
| pan_layer | `0C 00 03 01` | `0x01` | `40` | `41` | `41` | `40` | PASS |
| pan_left | `0C 00 03 01` | `0x02` | `40` | `41` | `41` | `40` | PASS |
| pan_song_1 | `0C 00 03 01` | `0x10` | `40` | `41` | `41` | `40` | PASS |
| pan_style | `0C 00 03 01` | `0x51` | `40` | `41` | `41` | `40` | PASS |
| reverb_main | `0C 00 04 01` | `0x00` | `0D` | `0E` | `0E` | `0D` | PASS |
| reverb_layer | `0C 00 04 01` | `0x01` | `23` | `24` | `24` | `23` | PASS |
| reverb_left | `0C 00 04 01` | `0x02` | `0A` | `0B` | `0B` | `0A` | PASS |
| reverb_song_1 | `0C 00 04 01` | `0x10` | `28` | `29` | `29` | `28` | PASS |
| reverb_style | `0C 00 04 01` | `0x51` | `40` | `41` | `41` | `40` | PASS |
