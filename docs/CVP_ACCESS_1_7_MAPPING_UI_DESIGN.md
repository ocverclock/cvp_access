# CVP Access 1.7 — éditeur Web de mapping clavier

Date de conception : 25 septembre 2026.

Statut : **spécification ergonomique et architecture proposée — avant développement**.

Base technique auditée : **CVP Access 1.6.1-RC2**.

## 1. Objectif

CVP Access 1.7 doit permettre de configurer les raccourcis clavier depuis le portail Web sans éditer manuellement `keyboard.toml`.

Flux utilisateur recherché :

```text
ouvrir le portail CVP Access
-> Configuration clavier
-> cliquer une touche du clavier affiché
-> voir son affectation actuelle
-> choisir une autre fonction, ou désaffecter la touche
-> accumuler éventuellement plusieurs changements
-> vérifier le résumé
-> Appliquer
-> validation + sauvegarde + régénération + redémarrage CVP Access
```

Le fichier `/etc/cvp-access/keyboard.toml` reste la source de vérité persistante. L'interface Web est un éditeur sûr de ce fichier, pas un second système de configuration.

## 2. Principes ergonomiques

### 2.1 Le clavier doit être l'interface principale

La page doit afficher une représentation du clavier AZERTY cohérente avec la carte clavier actuelle.

Chaque touche est un vrai bouton HTML. Une touche affiche :

- son libellé physique ;
- sa fonction principale actuelle ;
- un indicateur si des variantes avec Maj / Alt / AltGr / Cmd ou des combinaisons avancées existent ;
- un état visuel « non affectée », « affectée », « réservée » ou « modifiée mais non appliquée ».

Il ne faut pas demander à l'utilisateur de connaître des identifiants techniques comme :

```text
song_track_toggle:7
style_main:3
registration_recall:5
```

L'utilisateur doit voir :

```text
Piste Song 7 — Mute / Unmute
Main C
Registration 5
```

### 2.2 Pas de drag-and-drop

Le drag-and-drop est séduisant visuellement mais mauvais pour :

- VoiceOver ;
- navigation clavier ;
- écrans tactiles ;
- précision ;
- compréhension des conflits.

Le modèle retenu est : **sélectionner la touche, puis sélectionner la fonction**.

### 2.3 Pas de sauvegarde à chaque clic

Les changements restent en attente dans le navigateur.

Barre fixe lorsque des modifications existent :

```text
3 modifications en attente     [Annuler] [Vérifier] [Appliquer]
```

Cela évite de redémarrer CVP Access après chaque affectation et permet de corriger une erreur avant de toucher à la configuration active.

### 2.4 Aucun paramètre numérique libre

Les actions paramétrées sont développées en choix explicites.

Exemples :

```text
Pistes Song
  Piste 1 — Mute / Unmute
  ...
  Piste 16 — Mute / Unmute

Solo Song
  Solo piste 1
  ...
  Solo piste 16

Style
  Intro 1
  Intro 2
  Intro 3
  Main A
  Main B
  Main C
  Main D
  ...

Registration
  Registration 1
  ...
  Registration 8
```

Pour les volumes, proposer directement les pas valides, par exemple `+1`, `-1`, `+5`, `-5`, plutôt qu'un champ numérique.

## 3. Écran proposé

### 3.1 Entrée depuis le dashboard

Ajouter une action claire :

```text
[ Configuration clavier ]
```

La carte actuelle reste séparée :

```text
[ Voir / imprimer la carte clavier ]
```

La carte est une vue de consultation/impression.
L'éditeur 1.7 est la vue de modification.

### 3.2 Disposition desktop

```text
+---------------------------------------------------------------+
| Configuration clavier                         1.7              |
| Configuration active : keyboard.toml                           |
|                                                               |
| Couche : [Simple] [Maj] [Alt] [AltGr] [Cmd] [Avancé]        |
+--------------------------------------+------------------------+
|                                      |                        |
|       CLAVIER AZERTY INTERACTIF      |  Touche sélectionnée   |
|                                      |  A                     |
|   [Esc] [F1] ...                     |                        |
|   [&] [é] ...                        |  Affectation actuelle  |
|   [A] [Z] [E] ...                    |  Piste Song 1          |
|   [Q] [S] [D] ...                    |                        |
|                                      |  Rechercher une fonction
|                                      |  [______________]      |
|                                      |                        |
|                                      |  Song                  |
|                                      |  Style                 |
|                                      |  Voices / clavier      |
|                                      |  Guide vocal           |
|                                      |  Registration          |
|                                      |  Système               |
|                                      |                        |
|                                      | [Désaffecter]          |
+--------------------------------------+------------------------+
| 2 modifications en attente  [Annuler] [Vérifier] [Appliquer] |
+---------------------------------------------------------------+
```

### 3.3 Mobile / tablette

Le clavier passe au-dessus et le panneau d'affectation en dessous.

Le clavier peut défiler horizontalement si nécessaire. Aucune fonction essentielle ne doit dépendre d'un survol de souris.

## 3.4 Mapping graphique concret — le TOML devient invisible

L'éditeur 1.7 doit fonctionner comme un configurateur de clavier. Le fichier `keyboard.toml` reste une couche de stockage interne et n'est jamais montré dans le parcours normal.

### Parcours principal : touche -> fonction

```text
1. choisir la couche : Simple / Maj / Alt / AltGr / Cmd
2. cliquer la touche sur le clavier dessiné
3. voir sa fonction actuelle
4. cliquer « Changer la fonction »
5. choisir une famille
6. choisir la fonction
7. choisir son paramètre si nécessaire
8. voir immédiatement le nouveau libellé sur la touche
9. continuer avec d'autres touches
10. Appliquer une seule fois
```

Exemple :

```text
clic sur F8

F8
Actuellement : Non affectée

[ Changer la fonction ]

-> Song
-> Piste — Mute / Unmute
-> Piste 7

Résultat en attente :
F8 = Piste Song 7 — Mute / Unmute
```

Le navigateur conserve ce changement localement. Le Raspberry n'est modifié qu'au clic sur **Appliquer**.

### Une touche doit être lisible directement sur le clavier

Exemples :

```text
┌──────────────┐
│      A       │
│ Piste Song 1 │
└──────────────┘

┌──────────────┐
│   Maj + A    │
│ Solo piste 1 │
└──────────────┘

┌──────────────┐
│      O       │
│      —       │
└──────────────┘

┌──────────────┐
│     F15      │
│ Recorder     │
│ Réservée     │
└──────────────┘
```

L'état réservé/modifié doit toujours être exprimé par du texte, pas seulement par une couleur ou une icône.

### Panneau contextuel de la touche sélectionnée

```text
Touche sélectionnée : A
Couche : Simple

Fonction actuelle
Piste Song 1 — Mute / Unmute

[ Changer la fonction ]
[ Désaffecter ]
```

Après « Changer la fonction » :

```text
Rechercher : [________________]

[ Song ]
[ Style ]
[ Parties clavier ]
[ Informations ]
[ Guide / accessibilité ]
[ Registration ]
[ Système ]
```

### Ne pas afficher une liste plate de dizaines d'actions

Les actions paramétrées sont choisies en deux temps. Exemple Song :

```text
Song
[ Lecture / Pause ]
[ Stop ]
[ Position ]
[ Aller à la mesure ]
[ Boucle A/B ]
[ Piste — Mute / Unmute ]
[ Solo piste ]
[ Volume Song ]
```

Si l'utilisateur choisit « Piste — Mute / Unmute » :

```text
Choisir la piste

[1] [2] [3] [4]
[5] [6] [7] [8]
[9] [10] [11] [12]
[13] [14] [15] [16]
```

Même principe pour :

```text
Main Style -> [A] [B] [C] [D]
Intro -> [1] [2] [3]
Registration -> [1] ... [8]
Volume -> [-5] [-1] [+1] [+5]
```

Le client ne voit donc jamais `song_track_toggle:7`, `style_main:3` ou un autre identifiant technique.

### Aperçu immédiat avant sauvegarde

Dès qu'une fonction est choisie, le clavier virtuel est mis à jour, mais uniquement en état « modification en attente ».

```text
A
Avant : Piste Song 1 — Mute / Unmute
Après : Nom du Song

MODIFIÉ — non appliqué

[ Annuler cette modification ]
```

### Sélection par clavier physique — option de confort

En complément du clic sur le clavier dessiné, proposer éventuellement :

```text
[ Appuyer sur une touche du clavier pour la sélectionner ]
```

Le navigateur peut écouter un événement clavier et sélectionner la touche correspondante. Cette méthode reste secondaire car certains navigateurs ou systèmes interceptent certaines touches de fonction. Le clavier visuel reste toujours la référence fiable ; F14/F15/F16 sont de toute façon réservées.

### Le modificateur se choisit avant la touche

Le mode normal ne demande pas de cliquer graphiquement sur Maj puis A. On choisit simplement une couche en haut de page :

```text
[ Simple ] [ Maj ] [ Alt ] [ AltGr ] [ Cmd ]
```

Puis le clavier entier affiche cette couche :

```text
Simple : A -> Piste Song 1
Maj    : A -> Solo piste 1
```

Cette approche est beaucoup plus lisible que de simuler plusieurs touches simultanément à la souris.

### Recherche directe

Un utilisateur qui connaît déjà la fonction peut la rechercher :

```text
main c       -> Main Style C
solo 8       -> Solo piste 8
volume song  -> Volume Song
```

La fonction trouvée est affectée à la touche actuellement sélectionnée.

### Détails techniques uniquement pour le dépannage

Une zone repliable peut éventuellement afficher :

```text
Détails techniques
Action interne : song_track_toggle:7
```

mais cette information ne doit jamais être nécessaire pour configurer le produit.

### Résumé graphique des changements

```text
3 modifications en attente

A
Piste Song 1 -> Nom du Song

Maj + F4
Non affectée -> Main C

F2
Annonce transpose -> Non affectée

[ Tout annuler ] [ Vérifier ] [ Appliquer ]
```

Chaque modification peut être annulée individuellement avant application.

### Interaction de référence retenue

```text
COUCHE
  ↓
CLAVIER VISUEL
  ↓ clic sur une touche
PANNEAU DE LA TOUCHE
  ↓
FAMILLE DE FONCTIONS
  ↓
FONCTION
  ↓
PARAMÈTRE VISUEL SI NÉCESSAIRE
  ↓
APERÇU SUR LA TOUCHE
  ↓
MODIFICATIONS EN ATTENTE
  ↓
APPLIQUER
```

Ce parcours fait du TOML un détail d'implémentation et non plus l'interface de configuration.

## 4. Sélection des couches et modificateurs

Le moteur actuel sait gérer :

```text
SHIFT
ALT
ALTGR
META
CAPS
```

L'interface principale 1.7-RC1 expose une couche à la fois :

- Simple ;
- Maj ;
- Alt ;
- AltGr ;
- Cmd.

### Caps Lock : compatibilité uniquement

Le moteur sait encore interpréter `CAPS`, mais le profil RC2 officiel a `caps_lock_layer = false` et la couche Caps expérimentale a été abandonnée dans l'usage courant.

Décision après audit : **ne pas réintroduire Caps dans l'interface principale 1.7-RC1**. Les éventuelles affectations `CAPS+...` déjà présentes dans un ancien TOML doivent être conservées sans destruction, mais l'éditeur simple ne doit pas en créer. Une réintroduction ultérieure demanderait un choix ergonomique explicite et la gestion de `caps_fallback_to_base`.

Exemple :

```text
couche Simple
A -> Piste Song 1

couche Maj
A -> Solo piste 1
```

### CTRL reste réservé à l'aide

CTRL est une fonction d'accessibilité structurelle :

```text
CTRL + touche
-> annonce la fonction de la combinaison
-> ne l'exécute pas
```

CTRL ne doit donc **pas** être proposé comme couche assignable dans l'interface.

Exemple :

```text
Maj + A = Solo piste 1

CTRL + Maj + A
-> « Solo piste 1 »
-> aucune exécution
```

### Mode avancé

Le moteur accepte plusieurs modificateurs simultanés. La première version de l'éditeur ne doit pas encombrer l'usage normal avec cela.

Un panneau « Avancé » peut permettre plus tard des combinaisons comme :

```text
SHIFT+ALT+F1
ALTGR+SHIFT+F2
```

Le backend doit néanmoins conserver sans les détruire les combinaisons avancées déjà présentes dans un TOML existant, y compris d'anciennes combinaisons `CAPS+...`, même si l'interface simple ne les modifie pas.

## 5. Touches réservées et protégées

### 5.1 Verrouillage dur

Les touches du Dictaphone MIDI sont gérées en dehors du mapping TOML normal :

```text
F14 = morceau précédent
F15 = lecture / stop / armement / enregistrement
F16 = morceau suivant
```

Elles doivent apparaître dans le clavier Web avec un cadenas et leur fonction, sans possibilité de réaffectation en 1.7.

Même règle pour les touches CTRL : elles restent réservées à l'aide vocale.

### 5.2 ESC

ESC est actuellement la relance de CVP Access.

Je propose de ne pas le verrouiller complètement, mais d'afficher un avertissement avant modification :

```text
ESC sert actuellement de raccourci de récupération pour relancer CVP Access.
Changer cette affectation supprimera ce raccourci physique.
[Annuler] [Modifier quand même]
```

Le bouton de relance du portail Web reste disponible comme secours.

## 6. Panneau « Touche sélectionnée »

Après clic sur une touche, le panneau doit afficher :

```text
Touche : A
Couche : Simple
Combinaison : A

Affectation actuelle :
Piste Song 1 — Mute / Unmute

[Rechercher une fonction]

Catégories :
- Song
- Style
- Parties clavier / Voices
- Informations
- Guide vocal / accessibilité
- Registration
- Système

[Désaffecter cette combinaison]
```

Après sélection d'une nouvelle fonction :

```text
A
Avant : Piste Song 1
Après : Nom du Song

Modification non appliquée
```

La touche prend immédiatement un état « modifiée » sur le clavier virtuel, mais la configuration du Raspberry ne change pas encore.

## 7. Recherche des fonctions

La recherche doit fonctionner sur les noms destinés à l'utilisateur et sur quelques synonymes.

Exemples :

```text
"piste 4"
"solo"
"volume song"
"main c"
"intro"
"guide"
"registration"
```

Les identifiants internes peuvent être affichés uniquement dans une zone technique repliable, jamais comme libellé principal.

## 8. Gestion des conflits

Une combinaison clavier ne peut avoir qu'une fonction.

Comme l'utilisateur édite directement une combinaison donnée, remplacer sa fonction n'est pas un conflit : c'est une modification normale.

En revanche :

- la même fonction peut être affectée à plusieurs touches : **autorisé** ;
- une combinaison réservée ne peut pas être modifiée ;
- une combinaison invalide doit être refusée avant écriture ;
- une modification externe de `keyboard.toml` pendant l'édition doit être détectée.

Pour ce dernier point, l'API doit fournir un hash/révision de la configuration. Lors de « Appliquer », si le fichier a changé depuis l'ouverture de la page :

```text
La configuration a été modifiée depuis l'ouverture de cette page.
Rechargez-la avant d'appliquer vos changements.
```

Aucune écriture silencieuse ne doit écraser une modification Samba ou manuelle récente.

## 9. Vérification avant application

Le bouton « Vérifier » ouvre un résumé lisible :

```text
Modifications

A
  Piste Song 1
  -> Nom du Song

Maj + F4
  Non affectée
  -> Main C

F2
  Annonce transpose
  -> Non affectée
```

Puis :

```text
[Retour à l'édition] [Appliquer les 3 modifications]
```

Ce résumé est important pour l'accessibilité et réduit les erreurs de manipulation.

## 10. Pipeline d'application

L'application ne doit jamais écrire directement le fichier actif sans filet.

Pipeline cible :

```text
1. relire /etc/cvp-access/keyboard.toml
2. vérifier que sa révision correspond à celle éditée
3. appliquer les changements en mémoire
4. écrire keyboard.toml.tmp
5. valider le TOML avec le parseur officiel CVP Access
6. vérifier toutes les actions et tous les paramètres
7. créer une sauvegarde datée
8. remplacement atomique du fichier actif
9. régénérer keyboard-map.html
10. générer les WAV requis par les nouvelles actions
11. redémarrer cvp-access.service
12. vérifier que le service revient actif
13. en cas d'échec critique : rollback automatique puis nouveau redémarrage
```

Sauvegardes proposées :

```text
/etc/cvp-access/backups/keyboard-20260925-103500.toml
```

Conserver par exemple les 10 dernières sauvegardes.

## 11. Retour utilisateur après application

Succès :

```text
Configuration appliquée.
CVP Access a redémarré correctement.
Carte clavier mise à jour.
```

Échec avec rollback :

```text
La nouvelle configuration n'a pas pu être activée.
La configuration précédente a été restaurée.
CVP Access fonctionne avec l'ancienne configuration.
[Détails]
```

Ne jamais laisser l'utilisateur avec un simple « erreur 500 » après avoir modifié son clavier.

## 12. Restauration

Deux niveaux sont utiles.

### Touche / combinaison

```text
[Annuler la modification]
```

revient à la valeur active au chargement de la page.

### Configuration complète

Dans une zone « Avancé » :

```text
[Restaurer le mapping officiel CVP Access]
[Restaurer une sauvegarde]
```

La restauration complète doit demander confirmation et passer par le même pipeline de validation que toute autre modification.

## 13. Accessibilité Web obligatoire

Cette page fait partie d'un projet d'accessibilité : elle doit elle-même être réellement accessible.

Exigences :

- chaque touche = élément `button`, pas une `div` cliquable ;
- `aria-label` du type « A, Piste Song 1 » ;
- état réservé/modifié exprimé aussi par texte, jamais seulement par couleur ;
- navigation complète au clavier ;
- focus visible ;
- après sélection d'une touche, le focus logique peut aller vers le titre du panneau d'affectation ;
- aucun drag-and-drop obligatoire ;
- recherche et catégories utilisables avec VoiceOver ;
- résumé des modifications lisible dans l'ordre logique du DOM ;
- messages de succès/erreur annoncés via une zone `aria-live` ;
- contrastes suffisants ;
- interface utilisable avec zoom important.

Validation VoiceOver/macOS à prévoir avant de déclarer la 1.7 stable.

## 14. Architecture — source de vérité unique

### Problème actuel

Le catalogue exécutable n'est pas entièrement centralisé :

- `cvp_keyboard.py` contient le catalogue de base ;
- `cvp_access_1_5_1_base.py` ajoute des actions ;
- `cvp_access_1_5_2.py` ajoute encore les actions Solo / tout ON ;
- `cvp_keyboard_map.py` possède ses propres labels et groupes.

Créer l'éditeur Web en recopiant encore cette logique créerait une quatrième source de vérité.

### Décision 1.7

Avant l'interface, centraliser les métadonnées des actions dans un module importable sans initialiser le matériel.

Proposition :

```text
cvp_action_catalog.py
```

Il contient pour chaque action :

```python
id
label
description
category
parameter type / valeurs autorisées
public
deprecated
```

Exemple conceptuel :

```text
song_track_toggle
  label       = "Piste Song — Mute / Unmute"
  category    = "song"
  parameters  = 1..16

style_main
  label       = "Main Style"
  category    = "style"
  parameters  = A..D

restart
  label       = "Relancer CVP Access"
  category    = "system"
```

Le runtime, le générateur de carte, le générateur vocal et le portail Web doivent consommer cette même source.

## 15. Architecture — métadonnées du clavier

Même principe pour la géométrie et les libellés du clavier.

Aujourd'hui `cvp_keyboard_map.py` possède ses propres `ROWS`, `KEY_LABELS` et informations de présentation.

Proposition :

```text
cvp_keyboard_layout.py
```

qui expose :

- touches physiques supportées ;
- libellés AZERTY ;
- rangées ;
- largeur visuelle ;
- touches réservées ;
- modificateurs disponibles.

Puis :

```text
cvp_keyboard.py        -> routage evdev
cvp_keyboard_map.py    -> carte imprimable
cvp_web.py             -> éditeur Web
```

utilisent la même description.

## 16. API Web proposée

Lecture :

```text
GET /api/keyboard/config
GET /api/keyboard/catalog
```

`/api/keyboard/config` retourne notamment :

```json
{
  "revision": "<sha256>",
  "bindings": {
    "A": "song_track_toggle:1",
    "SHIFT+A": "song_track_solo:1"
  },
  "reserved": ["F14", "F15", "F16"],
  "caps_lock_layer": false
}
```

Le catalogue retourne des choix déjà structurés pour l'interface, sans faire interpréter au JavaScript les règles internes des paramètres.

Application :

```text
POST /api/keyboard/apply
```

avec :

```json
{
  "revision": "<sha256>",
  "changes": [
    {"combo": "A", "action": "announce_song_name"},
    {"combo": "SHIFT+F4", "action": "style_main:3"},
    {"combo": "F2", "action": null}
  ]
}
```

Le serveur ne fait jamais confiance au navigateur : il renormalise toutes les combinaisons et reparcourt toutes les actions avec le parseur officiel.

## 17. Ne pas refactorer le moteur Yamaha dans la même version

La pile actuelle :

```text
1.6.1
 -> 1.5.2
 -> 1.5.1
 -> 1.5
 -> 1.4.1
```

est une dette technique réelle, mais elle contient beaucoup de comportement matériel validé.

La 1.7 doit être un gros changement de **configuration et d'ergonomie**, pas simultanément une réécriture du moteur Yamaha/SysEx.

Décision proposée :

- centraliser catalogues et métadonnées nécessaires à l'éditeur ;
- conserver le chemin d'exécution Yamaha validé ;
- reporter la fusion/refonte complète de la pile runtime à une version distincte.

Cela limite fortement le risque de régression sur le CVP-905.

## 18. Profils clavier

Les profils seraient intéressants à terme :

```text
Profil standard
Profil Song
Profil accompagnement
Profil client X
```

Mais les intégrer dès le premier RC 1.7 ferait exploser la portée : sélection du profil actif, migration, sauvegardes, affichage, changements à chaud.

Décision proposée pour 1.7-RC1 :

- **une seule configuration active** ;
- sauvegardes/restauration solides ;
- architecture compatible avec des profils futurs ;
- profils reportés après validation terrain de l'éditeur simple.

## 19. Découpage de développement recommandé

### Étape A — fondations

- créer la source unique du catalogue d'actions ;
- créer la source unique des métadonnées clavier ;
- adapter runtime et carte actuelle sans changement fonctionnel ;
- tests de non-régression.

### Étape B — éditeur en lecture seule

- nouvelle page `/keyboard` ;
- clavier interactif ;
- couches Simple / Maj / Alt / AltGr / Cmd ;
- affichage des affectations actuelles ;
- recherche/catalogue des fonctions, sans écriture.

### Étape C — édition locale

- sélection d'une fonction ;
- désaffectation ;
- modifications en attente ;
- résumé des différences ;
- annulation.

### Étape D — application sûre

- API d'application ;
- hash de révision ;
- validation ;
- sauvegarde ;
- écriture atomique ;
- régénération carte/WAV ;
- restart ;
- rollback automatique.

### Étape E — validation accessibilité et terrain

- VoiceOver ;
- clavier uniquement ;
- mobile ;
- modification via hotspot CVP-ACCESS ;
- modification via LAN ;
- configuration modifiée simultanément par Samba ;
- perte/reprise du service CVP Access ;
- tests CVP-905 des principaux raccourcis après remapping.

## 20. Critères de validation 1.7

La version n'est pas considérée prête tant que les cas suivants ne passent pas :

1. modifier une touche libre ;
2. remplacer une affectation existante ;
3. désaffecter une touche ;
4. affecter une action paramétrée ;
5. conserver une même action sur plusieurs touches ;
6. modifier un raccourci avec Maj ;
7. conserver les raccourcis avancés non édités, y compris les anciens `CAPS+...` ;
8. empêcher la modification de F14/F15/F16 ;
9. conserver CTRL comme aide ;
10. détecter un TOML modifié extérieurement ;
11. refuser une action invalide ;
12. créer une sauvegarde avant écriture ;
13. régénérer la carte clavier ;
14. redémarrer CVP Access ;
15. rollback automatique si le nouveau fichier empêche le service de repartir ;
16. utiliser toute la page avec VoiceOver et sans souris.

## 21. Résumé de la décision proposée

Le cœur ergonomique de la 1.7 est :

```text
CLAVIER VISUEL
   +
COUCHE / MODIFICATEUR
   +
PANNEAU DE FONCTIONS HUMAINES
   +
MODIFICATIONS EN ATTENTE
   +
RÉSUMÉ
   +
APPLICATION ATOMIQUE AVEC ROLLBACK
```

Le point architectural indispensable est :

```text
une seule source de vérité pour les actions
une seule source de vérité pour le layout clavier
keyboard.toml reste la configuration persistante
```

C'est la base retenue pour commencer le développement de CVP Access 1.7 sans fragiliser le moteur Yamaha déjà validé.


## 22. Audit du dépôt RC2 avant développement

Revue complémentaire effectuée le 25 septembre 2026 sur la base **1.6.1-RC2**.

### 22.1 Écriture Web : authentification obligatoire

Le portail actuel fonctionne avec :

```text
User=root
CVP_WEB_REQUIRE_AUTH=0
```

et accepte les clients des réseaux IPv4 privés directement connectés au Raspberry.

Ce mode est tolérable pour la phase de mise au point actuelle, mais **aucun endpoint 1.7 capable d'écrire le mapping ne doit être livré ainsi**.

Avant d'activer `POST /api/keyboard/apply` :

- l'écriture doit exiger une authentification ;
- l'autorisation doit être contrôlée côté serveur, jamais seulement dans l'interface ;
- les chemins de fichiers restent fixes ;
- aucune donnée utilisateur ne doit être interpolée dans une commande shell ;
- F14/F15/F16 et CTRL doivent être refusés côté backend même si le navigateur est contourné.

Option minimale pour 1.7 : réactiver l'authentification des actions d'écriture par défaut.

Le fait que `cvp-web.service` tourne en root augmente l'impact potentiel d'une erreur du portail. Réduire les privilèges ou déléguer les opérations sensibles à des helpers stricts reste souhaitable, mais ne doit pas entraîner un refactoring Yamaha dans cette version.

### 22.2 Une désaffectation doit survivre aux mises à jour

Les migrations actuelles 1.5.1 / 1.5.2 utilisent encore une logique de type :

```text
si une touche officielle est absente
-> ajouter l'affectation officielle
```

Avec l'éditeur 1.7, une touche absente pourra signifier **« l'utilisateur l'a volontairement désaffectée »**.

À partir de 1.7, une mise à jour ne doit donc plus déduire l'état de migration de la seule présence d'une touche.

Règle retenue :

- une configuration personnalisée est autoritaire pour `[keys]` ;
- une nouvelle fonction de release peut rester non attribuée ;
- seules les migrations structurelles nécessaires (renommage d'identifiant, changement de format) peuvent modifier automatiquement un mapping existant ;
- ces migrations doivent être pilotées par une version de schéma/migration explicite, pas par « touche absente = touche à ajouter ».

Sinon une mise à jour pourrait ressusciter une touche que le client venait précisément de supprimer dans l'interface.

### 22.3 Un seul mapping usine canonique

Le dépôt contient actuellement deux lignées de configuration :

```text
config/default.toml
config/default-1.5.1.toml
```

et les chemins d'installation historiques peuvent produire :

```text
/opt/cvp-access/default-keyboard.toml
/opt/cvp-access/default-keyboard-1.5.1.toml
```

La chaîne RC2 finit par utiliser le profil 1.5.1 consolidé, mais cette duplication est mauvaise pour une future commande « Restaurer le mapping officiel ».

Pour 1.7 il faut une seule source canonique de mapping usine. Les anciens fichiers peuvent rester comme historique/compatibilité, mais l'éditeur, le Doctor, l'installateur et la restauration doivent pointer vers le même fichier courant.

### 22.4 Le Doctor doit accepter un mapping volontairement personnalisé

Le Doctor actuel recherche plusieurs affectations officielles précises et produit un avertissement lorsqu'elles sont absentes ou différentes.

Ce comportement était utile avant l'éditeur, mais devient ambigu en 1.7.

Le Doctor 1.7 doit distinguer :

```text
VALIDITÉ
- TOML lisible
- combinaisons valides
- actions connues
- paramètres valides
- pas de conflit avec touches réservées

PROFIL
- identique au mapping usine
- personnalisé
```

Un mapping personnalisé valide ne doit pas être présenté comme une panne.

### 22.5 La carte clavier actuelle confirme le besoin d'un catalogue unique

La revue de `cvp_keyboard_map.py` montre déjà des divergences de présentation :

- certaines actions récentes n'ont pas de libellé humain dédié et retombent sur leur identifiant technique ;
- `song_track_solo` ne bénéficie pas actuellement d'un libellé paramétré propre dans cette carte ;
- certaines fonctions Guide / Métronome / Layer / Left sont regroupées visuellement dans la catégorie Style.

Ce n'est pas un problème du moteur Yamaha, mais c'est exactement la raison pour laquelle 1.7 doit centraliser `label`, `category`, description et paramètres dans `cvp_action_catalog.py`.

Le vérificateur 1.7 devra comparer catalogue, runtime, carte et API afin qu'une action ne puisse plus exister avec quatre descriptions différentes.

### 22.6 Touches réservées : validation serveur

Le runtime Recorder intercepte F14/F15/F16 et la carte indique qu'une affectation TOML sur ces touches serait ignorée. Le parseur TOML générique peut néanmoins encore accepter ces combinaisons.

Pour conserver la compatibilité des anciens fichiers, le parseur historique peut continuer à les signaler. En revanche l'API 1.7 doit **refuser explicitement** toute tentative nouvelle d'affecter :

```text
F14
F15
F16
CTRL+...
```

CTRL est une sémantique d'aide, pas une couche utilisateur.

### 22.7 Validation après application

Le simple état `systemctl is-active cvp-access.service` ne suffit pas comme seule preuve d'activation.

Après écriture, la séquence doit au minimum confirmer :

1. le fichier actif passe `cvp_keyboard.py --check` ;
2. sa révision correspond au contenu validé ;
3. le service redémarre et reste actif ;
4. la carte est régénérée depuis ce même fichier ;
5. aucun fallback de configuration n'a été utilisé à la place du fichier demandé.

Le rollback doit restaurer exactement la sauvegarde précédente puis refaire les mêmes contrôles.

### 22.8 Ordre de priorité après audit

Avant toute page d'édition :

```text
1. catalogue d'actions unique
2. métadonnées clavier uniques
3. mapping usine canonique unique
4. stratégie de migration compatible avec les désaffectations volontaires
5. Doctor compatible avec les profils personnalisés
6. protection des écritures Web
7. éditeur lecture seule
8. édition + application atomique
```

Ces points sont désormais considérés comme faisant partie du périmètre de fondation de CVP Access 1.7.
