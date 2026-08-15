# CVP Access v1.5 RC2

RC2 conserve le moteur MIDI/SysEx v1.4.1 et fait évoluer la couche de configuration/accessibilité.

## Nouveautés

- `keyboard.toml` devient le mode d'emploi intégré ;
- commandes de sauvegarde, validation, activation et restauration directement dans le TOML ;
- section `[speech]` réellement utilisée ;
- modes vocaux `pregenerated`, `hybrid`, `runtime` ;
- Piper runtime chargé une seule fois par un worker persistant ;
- cache des phrases dynamiques ;
- `generation = configured` génère seulement les WAV requis par les actions du TOML ;
- `generation = core/all` permet une banque complète ;
- choix de la voix Piper dans le TOML pris en compte par l'installateur ;
- CVP Doctor adapte le contrôle de la banque vocale au mode choisi ;
- catalogue maître `docs/FUNCTION_CATALOG.md` pour les fonctions ConPianist connues et leur statut.

## Fichiers nouveaux

```text
cvp_speech.py
cvp_piper_worker.py
cvp_access_installer/tools/generate_configured_voices.py
docs/FUNCTION_CATALOG.md
RC2_NOTES.md
```

## Important

Cette version reste une RC : tester le routage clavier, Caps Lock et le fallback Piper réel sur le Raspberry avant de la déclarer stable.
