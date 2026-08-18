# CVP functional validation - wave 2

Generated: `2026-08-18T12:37:33.381271`

## Résumé

- PASS: 1
- RESTORE_VERIFY_FAILED: 1

## Tests

| Test | Signature | Index | Initial | Test | Observé | Restauré | Statut |
|---|---|---:|---|---|---|---|---|
| guide_type | `04 03 01 01` | `0x00` | `00` | `01` | `01` | `00` | PASS |
| octave_main | `0C 00 12 01` | `0x00` | `00` | `01` | `31` | `31` | RESTORE_VERIFY_FAILED |
