# CVP Access v1.5 RC2 — fichiers à déposer sur GitHub

Cette RC2 conserve `cvp_access_v1.4.1.py` comme moteur MIDI/SysEx validé.

## Ajouter / remplacer à la racine

```text
cvp_access_v1.5.py
cvp_keyboard.py
cvp_speech.py
cvp_piper_worker.py
config/default.toml
docs/KEY_ACTIONS.md
docs/FUNCTION_CATALOG.md
versions.md
RC2_NOTES.md
```

## Ajouter / remplacer dans l'installateur

```text
cvp_access_installer/install.sh
cvp_access_installer/update.sh
cvp_access_installer/tools/cvp_doctor.py
cvp_access_installer/tools/generate_configured_voices.py
cvp_access_installer/samba/cvp-access.conf.in
cvp_access_installer/docs/CONFIGURATION.md
```

L'installateur devient `0.3.1`.

## Important

Ne pas supprimer :

```text
cvp_access_v1.4.1.py
cvp_access_installer/tools/generate_track_voices.py
cvp_access_installer/tools/generate_value_voices.py
```

Les deux anciens générateurs restent utilisés en compatibilité avec les
versions antérieures à v1.5.

Tester RC2 sur le Raspberry avant de la déclarer stable.
