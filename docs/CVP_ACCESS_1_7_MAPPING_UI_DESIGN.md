# CVP Access 1.7 — éditeur Web de mapping clavier

Date de conception : 25 septembre 2026.

Statut : **spécification ergonomique et architecture proposée — avant développement**.

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
- un indicateur si des variantes avec Maj / Alt / AltGr / Cmd / Caps existent ;
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
| Couche : [Simple] [Maj] [Alt] [AltGr] [Cmd] [Caps] [Avancé] |
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

## 4. Sélection des couches et modificateurs

Le moteur actuel sait gérer :

```text
SHIFT
ALT
ALTGR
META
CAPS
```

L'interface principale expose une couche à la fois :

- Simple ;
- Maj ;
- Alt ;
- AltGr ;
- Cmd ;
- Caps.

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
CAPS+SHIFT+F2
```

Le backend doit néanmoins conserver sans les détruire les combinaisons avancées déjà présentes dans un TOML existant, même si l'interface simple ne les modifie pas.

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
- couches Simple / Maj / Alt / AltGr / Cmd / Caps ;
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
7. conserver les raccourcis avancés non édités ;
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
