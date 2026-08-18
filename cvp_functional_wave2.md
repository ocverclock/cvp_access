# CVP functional validation - wave 2

Generated: `2026-08-18T12:22:25.123415`

## Résumé

- PASS: 3
- RESTORE_VERIFY_FAILED: 1

## Tests

| Test | Signature | Index | Initial | Test | Observé | Restauré | Statut |
|---|---|---:|---|---|---|---|---|
| part_0 | `04 00 0E 01` | `0x00` | `01` | `00` | `00` | `01` | PASS |
| part_1 | `04 00 0E 01` | `0x01` | `01` | `00` | `00` | `01` | PASS |
| part_2 | `04 00 0E 01` | `0x02` | `01` | `00` | `00` | `01` | PASS |
| part_3 | `04 00 0E 01` | `0x03` | `01` | `00` | `31` | `31` | RESTORE_VERIFY_FAILED |
