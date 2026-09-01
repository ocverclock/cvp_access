# CVP Access 1.5.1 — actions clavier RC1

La couche principale v1.5 est conservée.

## Aide vocale

`CTRL + touche` annonce toujours la fonction sans l'exécuter.

Sur la couche CAPS :

1. appuyer une fois sur `Caps Lock` pour activer la couche ;
2. `CTRL + touche` décrit l'action CAPS ;
3. `Caps Lock` désactive ensuite la couche.

Les phrases d'aide finies sont pré-générées en WAV quand Piper est disponible.
Les noms de Song/Style restent synthétisés dynamiquement et mis en cache.

## Nouvelles fonctions CAPS

| Touche CAPS | Action |
|---|---|
| F1 | annonce le Style courant |
| F2 | annonce le Song courant |
| F3 | annonce la longueur du Song |
| F4 | Sync Start ON/OFF |
| F5 | Guide ON/OFF |
| F6 | Stream Lights ON/OFF |
| F7 | Métronome ON/OFF |
| 1/2/3 | Intro 1/2/3 |
| 4/5/6/7 | Main A/B/C/D |
| 8 | Break |
| A/Z/E/R | Fill A/B/C/D |
| T/Y/U | Ending 1/2/3 |
| Q/S/D/F/G/H/J/K | Registration 1..8 |

## Pourquoi certaines découvertes ne sont toujours pas des actions

Les propriétés suivantes restent volontairement hors SET utilisateur :

- Guide Type ;
- Piano Lid / Environment / VRM / Resonance quand la sémantique/range utilisateur n'est pas suffisamment consolidée ;
- Stream Lights Speed (`0x31` sur SET naïf) ;
- global Reverb : GET seulement ;
- Voice Name CVP : identité lisible non résolue ;
- sélection directe Style : Genos seulement, non testée CVP ;
- ACMP et Fingering direct : recherches clôturées, workaround Registration.

Règle : une signature connue n'est pas automatiquement une commande utilisateur sûre.
