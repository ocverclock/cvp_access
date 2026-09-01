# AI_HANDOFF — CVP Access

## À lire en premier

Pour reprendre ce projet :

1. lire `PROJECT_STATE.md` ;
2. lire `docs/CVP_ACCESS_1_5_1.md` ;
3. lire `docs/KEY_ACTIONS_1_5_1.md` ;
4. consulter `CVP905_PROTOCOL_CHECKPOINT_RC4.md` seulement pour le protocole ;
5. ne pas relancer les recherches massives déjà clôturées.

---

## Version de départ

```text
CVP Access 1.5.1-RC2
Date de référence : 1 septembre 2026
Instrument validé : Yamaha CVP-905 firmware 1.03
```

La RC2 est le nouveau point de référence.

Elle a été :

- testée physiquement ;
- consolidée sur GitHub ;
- vérifiée avec `VERIFY_PACKAGE_151.py` ;
- redéployée avec succès depuis un clone GitHub neuf ;
- validée par `cvp_doctor_151.py`.

---

## Runtime

```text
Repo            : ~/CVP_access
Runtime         : /opt/cvp-access
Entrée runtime  : /opt/cvp-access/cvp_access.py
Source 1.5.1    : cvp_access_1_5_1.py
Config active   : /etc/cvp-access/keyboard.toml
Map             : /etc/cvp-access/keyboard-map.html
Service         : cvp-access.service
Voix            : fr_FR-siwis-medium
Mode            : hybrid
```

---

## Layout RC2

```text
1..8 = mutes parties Style
9    = Layer / Dual
0    = Left

W = nom Style
X = nom Song
C = longueur Song
V = Syncro Start
B = Guide
F7 = Métronome

PageUp               = volume Style +1
PageDown             = volume Style -1
Shift + PageUp       = volume Style +5
Shift + PageDown     = volume Style -5

Up / Down            = Vol. guide vocal
```

CTRL + touche annonce la fonction sans l'exécuter.

Caps Lock n'est plus utilisé.

Actions volontairement non attribuées :

```text
Intro
Main A..D
Fill A..D
Break
Ending
Registration 1..8
Stream Lights
```

---

## Terminologie utilisateur

Toujours utiliser :

```text
Syncro Start
Vol. guide vocal
Pas de Song chargé.
```

Ne pas renommer l'identifiant interne :

```text
sync_start_toggle
```

Les documents protocole Yamaha peuvent conserver `Sync Start`.

---

## Speech

Piper est préchargé au démarrage.

Le worker reste résident.

Le cache dynamique est persistant :

```text
~/.cache/cvp-access/tts/
```

Ordre :

```text
WAV pré-généré
→ cache dynamique
→ synthèse Piper
→ stockage cache
```

Ne pas ajouter « Je cherche » sauf si de futurs tests montrent que le délai de synthèse avec Piper déjà chargé reste réellement gênant.

---

## Installation / upgrade

Validation courante :

```bash
cd ~/CVP_access
python3 VERIFY_PACKAGE_151.py
sudo bash cvp_access_installer/upgrade_1_5_1.sh
```

Attendu :

```text
CVP Access 1.5.1 RC2 package: OK
```

Puis Doctor :

```text
OK Runtime 1.5.1
OK Version runtime 1.5.1-RC2
OK Layout accessibilité
OK WAV états 1.5.1
```

---

## Points à ne pas rouvrir sans nouvelle preuve

Recherche directe clôturée :

```text
ACMP
Fingering
Auto Fill In
Synchro Stop
```

OTS Link reste non résolu.

Pour ACMP et Fingering, utiliser les mécanismes Registration déjà validés.

Ne pas refaire les scans massifs précédents.

---

## Genos 1

Le Genos est un banc secondaire.

Aucune commande Genos ne doit être présentée comme validée CVP sans test physique sur CVP-905.

---

## Prochaines pistes raisonnables

1. installation sur une carte Raspberry Pi OS réellement vierge ;
2. observer si le worker Piper reçoit systématiquement un SIGKILL à l'arrêt ;
3. nouvelles fonctions sur `N`, `,`, `;` seulement si utiles à l'accessibilité ;
4. continuer progressivement la séparation du moteur historique ;
5. tests ciblés, jamais de brute-force SET.

---

## Rollback

```bash
sudo cp /opt/cvp-access/cvp_access_v1.5.py /opt/cvp-access/cvp_access.py
sudo systemctl restart cvp-access
```

---

## Règle de reprise

Ne pas repartir d'une ancienne RC1, d'une couche CAPS, ni d'un ancien document indiquant `1.5-RC4-dev`.

**La base correcte est `1.5.1-RC2`.**
