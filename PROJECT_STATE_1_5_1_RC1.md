# CVP Access — état candidat 1.5.1-RC1-dev

Ce fichier complète `PROJECT_STATE.md` tant que la RC1 n'a pas été validée
physiquement sur CVP-905.

## Runtime candidat

```text
cvp_access_1_5_1.py
VERSION = 1.5.1-RC1-dev
```

Base conservée :

```text
cvp_access_v1.5.py
cvp_access_v1.4.1.py
```

Nouveaux overlays :

```text
cvp_song_151.py
cvp_speech_151.py
cvp_midi.py
cvp_yamaha.py
cvp_registration.py
cvp_style.py
cvp_voice.py
```

## Décisions

- Song name : ancien décodeur 14-bit abandonné dans la 1.5.1.
- Style name/path : exposé vocalement.
- Song name/path : exposé vocalement.
- Song length : exposé vocalement.
- Sync Start : exposé GET/SET.
- Guide ON/OFF : exposé GET/SET.
- Stream Lights ON/OFF : exposé GET/SET.
- Métronome : exposé GET/SET.
- Section Control et Registration : affectés à la couche CAPS.
- CTRL reste le mécanisme d'aide contextuelle.
- résultats Genos restent NON TESTÉS CVP et ne sont pas activés dans le runtime.

## Non exposé volontairement

- Guide Type : mapping utilisateur à consolider.
- Piano Room paramètres : ne pas généraliser les ranges sans validation.
- Stream Speed : NON APPLICABLE, SET naïf -> 0x31.
- Reverb globale : GET seulement.
- Voice human-readable CVP : non résolue.
- Style direct select Genos : verrouillé.
- ACMP/Fingering directs : clôturés, workaround Registration.
