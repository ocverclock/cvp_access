# CVP functional validation - wave 2

Generated: `2026-08-18T12:40:47.939268`

## Résumé

- PASS: 3
- RESTORE_VERIFY_FAILED: 1

## Tests

| Test | Signature | Index | Initial | Test | Observé | Restauré | Statut |
|---|---|---:|---|---|---|---|---|
| guide_type | `04 03 01 01` | `0x00` | `00` | `01` | `01` | `00` | PASS |
| lid_position | `02 02 07 01` | `0x00` | `00` | `01` | `01` | `00` | PASS |
| environment | `02 02 03 01` | `0x00` | `06` | `07` | `07` | `06` | PASS |
| brightness | `0C 00 0B 01` | `0x00` | `06` | `07` | `31` | `31` | RESTORE_VERIFY_FAILED |
