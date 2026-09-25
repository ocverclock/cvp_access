# CVP Access 1.7.0-RC1 — état d'implémentation et validation Raspberry

Date : 25 septembre 2026.

Branche de développement :

```text
feature/cvp-access-1.7-mapping-ui
```

Pull request de validation :

```text
#1 — CVP Access 1.7-RC1 — éditeur graphique et profils clavier
```

La PR reste volontairement en **draft** tant que la validation matérielle sur le Raspberry + CVP-905 n'est pas terminée.

## 1. Ce qui est implémenté

### Éditeur graphique

Page :

```text
http://cvp-access.local/keyboard
```

Fonctions :

- clavier AZERTY graphique ;
- couches Simple / Maj / Alt / AltGr / Cmd ;
- touches de navigation et flèches incluses ;
- clic sur une touche puis choix d'une fonction en français ;
- recherche des fonctions ;
- catégories Song / Style / Parties clavier / Informations / Guide / Registration / Système ;
- actions paramétrées en deux étapes, par exemple « Piste Song » puis 1..16 ;
- aperçu immédiat des changements ;
- modifications en attente avant écriture ;
- désaffectation ;
- Échap modifiable avec avertissement de récupération ;
- F14/F15/F16 verrouillées ;
- CTRL reste réservé à l'aide et n'est pas assignable.

Le TOML n'est jamais nécessaire dans le parcours normal.

## 2. Profils clavier

Implémenté :

- profil usine protégé ;
- profil Standard créé à partir de la configuration active lors de la migration ;
- créer / Enregistrer sous ;
- renommer ;
- dupliquer ;
- supprimer un profil non actif ;
- ouvrir un profil sans l'activer ;
- activer explicitement un profil ;
- détection SHA-256 des modifications concurrentes ;
- détection d'un `keyboard.toml` modifié hors du portail ;
- possibilité de conserver ce fichier externe comme nouveau profil ;
- possibilité de recharger explicitement le profil enregistré.

Le runtime continue à charger uniquement :

```text
/etc/cvp-access/keyboard.toml
```

Les profils sont une couche de gestion autour du runtime validé.

## 3. Stockage

```text
/etc/cvp-access/
  keyboard.toml
  keyboard-profiles.json
  profiles/
    factory.toml
    standard.toml
    p-<id>.toml
  backups/
    keyboard-AAAAmmjj-HHMMSS.toml
```

Le nom humain d'un profil est séparé de son identifiant/fichier.

## 4. Accès à l'édition

Décision terrain : **l'éditeur clavier et la gestion des profils ne demandent aucun code ni mot de passe**.

Le portail reste limité au réseau local par le contrôle d'accès réseau existant. Les endpoints d'édition clavier/profils sont volontairement placés avant l'authentification maintenance globale afin de rester utilisables sans déverrouillage, même si cette authentification est réactivée plus tard pour les autres actions.

Le mot de passe maintenance reste disponible pour les opérations générales du portail qui en auraient besoin (mise à jour, reboot, etc.), mais il n'intervient plus dans le flux de mapping.

L'éditeur n'affiche plus de champ mot de passe.

## 5. Application transactionnelle

Lors de l'activation/modification du profil actif :

1. validation complète du TOML ;
2. rejet côté serveur de F14/F15/F16 et CTRL ;
3. contrôle de révision ;
4. sauvegarde de l'ancien `keyboard.toml` ;
5. écriture atomique ;
6. régénération de la carte clavier ;
7. régénération des annonces configurées avec le compte CVP ;
8. restart de `cvp-access.service` ;
9. relecture du fichier actif ;
10. contrôle de sa révision ;
11. contrôle du service ;
12. rollback automatique si une étape critique échoue.

Dix sauvegardes sont conservées.

## 6. Migration

À partir de 1.7 :

```text
touche absente != touche à restaurer automatiquement
```

Les anciennes migrations « absent => ajouter le raccourci officiel » sont désactivées par l'upgrader 1.7.

Une configuration utilisateur est donc autoritaire, y compris un `[keys]` volontairement vide.

Les installations neuves utilisent directement :

```text
config/default-current.toml
```

Le fallback intégré du runtime contient les mêmes 83 affectations.

## 7. Source unique des métadonnées

```text
cvp_action_catalog.py
cvp_keyboard_layout.py
```

sont maintenant consommés par :

- le parseur/runtime clavier ;
- l'éditeur Web ;
- la carte clavier imprimable.

Les anciens wrappers 1.5.1 / 1.5.2 ne réécrivent plus `ACTION_SPECS`.

Les 46 actions historiques connues sont présentes dans le catalogue 1.7.

## 8. Doctor

Le Doctor distingue désormais :

```text
VALIDITÉ
profil valide / invalide

PROFIL
usine / personnalisé
```

Une configuration personnalisée valide n'est plus signalée comme anomalie simplement parce qu'elle diffère du mapping officiel.

## 9. Vérification logicielle

Deux contrôles sont fournis :

```bash
python3 VERIFY_PACKAGE_170.py
python3 TEST_KEYBOARD_PROFILES_170.py
```

Le vérificateur contrôle entre autres :

- syntaxe Python ;
- syntaxe shell ;
- manifeste de release ;
- cohérence profil usine / fallback ;
- catalogue d'actions ;
- absence des anciennes sources d'ActionSpec dans les wrappers ;
- déploiement des nouveaux modules ;
- absence de blocage par code sur les endpoints clavier/profils ;
- conservation de `/api/keyboard/select` ;
- Doctor ;
- carte imprimable ;
- layout complet ;
- puis lance le self-test fonctionnel.

Le self-test utilise un faux `evdev` et un faux `/etc/cvp-access` temporaire. Il teste sans Yamaha :

- création du store ;
- profil usine / Standard ;
- créer / renommer / dupliquer / supprimer ;
- révision obsolète ;
- mapping ;
- refus F14/F15/CTRL ;
- activation simulée ;
- désaffectation totale ;
- détection de modification externe ;
- import de l'état manuel ;
- réactivation du profil enregistré ;
- couches UI ;
- touches de navigation ;
- choix paramétré en deux étapes.

## 10. Installation RC1 sur le Raspberry de test

Ne pas fusionner `main` avant cette validation.

Sur le Raspberry :

```bash
cd ~/CVP_access

git fetch origin
git switch feature/cvp-access-1.7-mapping-ui
git pull --ff-only origin feature/cvp-access-1.7-mapping-ui

python3 VERIFY_PACKAGE_170.py
```

Le vérificateur doit terminer par :

```text
CVP Access 1.7.0 RC1 package: OK
```

Ensuite seulement :

```bash
sudo bash cvp_access_installer/upgrade_1_7_0.sh
```

Puis :

```bash
systemctl --no-pager --full status cvp-access.service cvp-web.service
cat /opt/cvp-access/VERSION 2>/dev/null || true
sudo cat /etc/cvp-access/maintenance-password
```

Ouvrir :

```text
http://cvp-access.local/keyboard
```

## 11. Validation terrain recommandée

Ordre de test :

1. vérifier que le CVP fonctionne encore avec le profil Standard sans modification ;
2. ouvrir l'éditeur et vérifier toutes les couches ;
3. créer « Test 1.7 » avec Enregistrer sous ;
4. modifier une touche non critique, par exemple F8 ;
5. enregistrer le profil non actif ;
6. vérifier que le piano n'a pas changé ;
7. activer « Test 1.7 » ;
8. vérifier le restart et la nouvelle affectation ;
9. vérifier CTRL + touche pour l'aide ;
10. vérifier F14/F15/F16 ;
11. revenir à Standard ;
12. renommer puis dupliquer un profil ;
13. vérifier la suppression d'un profil non actif ;
14. modifier manuellement `keyboard.toml` et vérifier la détection ;
15. tester « Enregistrer comme nouveau profil » ;
16. vérifier la carte clavier imprimable ;
17. lancer le Doctor ;
18. test VoiceOver / clavier seul.

## 12. À ne pas faire avant validation

- ne pas fusionner la PR #1 ;
- ne pas publier de release stable 1.7 ;
- ne pas refactorer la pile Yamaha/SysEx en même temps ;
- ne pas utiliser le bouton de mise à jour GitHub depuis la branche de test sans vérifier d'abord son comportement vis-à-vis de `main`.

## 13. Critère de passage vers main

La PR peut quitter le mode draft seulement après :

- `VERIFY_PACKAGE_170.py` OK sur le Raspberry ;
- installation 1.7-RC1 OK ;
- portail clavier accessible ;
- profils fonctionnels ;
- remapping réel validé ;
- aucune régression F14/F15/F16 ;
- aucune régression Song / Style / Guide / voix ;
- restauration Standard OK ;
- Doctor propre ;
- validation VoiceOver minimale.
