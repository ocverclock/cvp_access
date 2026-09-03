# CVP-905 — recherche Song Recorder

Branche de recherche : `research/song-recorder-probe`

## Objectif

Déterminer si le Yamaha CVP-905 expose par CSP/SysEx un état exploitable pour :

- création / préparation d'un nouveau Song ;
- Record Ready ;
- enregistrement en cours ;
- arrêt de l'enregistrement.

À ce stade, **aucune commande d'enregistrement n'est revendiquée**.

## Règle de sécurité

La première phase est strictement **GET-only**.

Le script ne doit envoyer :

- aucun SET ;
- aucun RESET ;
- aucune commande Record ;
- aucune écriture sur le CVP.

Les changements d'état sont réalisés manuellement sur le piano.

## Outil

```text
docs/cvp_probe_song_recorder.py
```

Il réutilise le moteur de lecture existant :

```text
docs/cvp_probe_readonly.py
```

## Premier test recommandé

Arrêter CVP Access afin de libérer le port MIDI :

```bash
sudo systemctl stop cvp-access
```

Depuis le dépôt :

```bash
cd ~/CVP_access
python3 docs/cvp_probe_song_recorder.py
```

Le périmètre initial est volontairement ciblé :

```text
04 00 00..7F 01 | index 00
```

Le script demande trois états :

```text
A1 = NORMAL
B  = RECORD_READY
A2 = NORMAL
```

Pour B, préparer manuellement un nouvel enregistrement Song sur l'écran du CVP sans commencer à jouer.

Le script ne conserve comme candidats forts que :

```text
A1 == A2 != B
```

Les résultats sont écrits dans :

```text
docs/research/song_recorder_YYYYMMDD_HHMMSS.json
docs/research/song_recorder_YYYYMMDD_HHMMSS.md
```

## Si le premier scan ne trouve rien

Élargir progressivement, toujours en GET-only :

```bash
python3 docs/cvp_probe_song_recorder.py --families 00,01
```

Puis, uniquement si nécessaire :

```bash
python3 docs/cvp_probe_song_recorder.py --families 00,01,02,03
```

Ne pas lancer immédiatement un scan beaucoup plus large sans raison : le but est de garder une recherche interprétable et reproductible.

## Interprétation

Un changement reproductible n'est qu'un **candidat d'état**.

Même si une propriété passe par exemple de `00` à `01` en Record Ready, cela ne prouve pas qu'un SET sur cette propriété permet de déclencher l'enregistrement.

Toute tentative de SET devra faire l'objet d'une validation séparée, ciblée, réversible et documentée.

## État actuel du projet

Les fonctions Song déjà validées dans CVP Access comprennent notamment :

- Play / Pause / Stop ;
- position mesure/temps ;
- longueur ;
- nom / chemin Song ;
- boucle A/B ;
- présence des pistes ;
- parties pédagogiques.

La création directe d'un nouveau Song et le pilotage du Song Recorder restent **NON RÉSOLUS** tant qu'un test matériel n'a pas fourni de preuve.
