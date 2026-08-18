# CVP functional validation - wave 1

Generated: `2026-08-18T12:11:37.899836`

## Résumé

- PASS: 6
- RESTORE_VERIFY_FAILED: 1

## Tests

| Test | Signature | Index | Initial | Test | Observé | Restauré | Statut |
|---|---|---:|---|---|---|---|---|
| guide | `04 03 00 01` | `0x00` | `00` | `01` | `01` | `00` | PASS |
| stream_lights | `04 02 00 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| part_auto | `04 00 10 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| vrm | `02 02 00 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| active_main | `0C 00 01 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| active_mic | `0C 00 01 01` | `0x40` | `01` | `00` | `00` | `01` | PASS |
| active_wave | `0C 00 01 01` | `0x44` | `01` | `00` | `31` | `31` | RESTORE_VERIFY_FAILED |
