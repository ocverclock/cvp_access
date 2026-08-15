v1.0
- mute/unmute 16 pistes
- lecture état réel
- tempo
- transpose
- voix

v1.1
- ajout volume accompagnement Page Up / Page Down

v1.1.3
- contrôle du volume Style avec Page Up / Page Down
- GET réel avant modification
- vérification GET après SET
- correction du décalage de lecture
- protection mono-instance
- fermeture propre de amidi
- annonces vocales du volume Style

V1.2.1
* `& é " ' ( - è _` → Rhythm 1, Rhythm 2, Bass, Chord 1, Chord 2, Pad, Phrase 1, Phrase 2
* mute/unmute individuel avec retour vocal
* détection automatique du changement de Style
* resynchronisation automatique des 8 parties après changement de Style
* contrôle du volume Style avec Page Up / Page Down
* lecture réelle avant modification et vérification après SET
* protection contre le lancement de plusieurs instances
* fermeture propre de la liaison MIDI
* correction du fichier de verrouillage déplacé vers `~/.cache`

v1.4.1
Ajout du contrôle du lecteur Song et de l’annonce de position.
* `Espace` → Play / Pause
* `Entrée` → Stop
* `P` → annonce de la position actuelle
* lecture de la mesure et du temps directement depuis le CVP
* validation des commandes Song par `GET → SET → GET`
* nouvelle synthèse vocale modulaire :
  * `mesure.wav`
  * nombres de `0 à 100`
  * `temps.wav`
* évite de générer toutes les combinaisons mesure/temps
* correction du décodage Yamaha des valeurs multi-octets en 7 bits

v1.5 - clavier configurable (à valider sur matériel)
* ajout d’un fichier TOML de configuration clavier
* catalogue fermé d’actions : aucune exécution Python depuis le TOML
* suppression du principe « une fonction = une touche codée en dur »
* noms de touches orientés clavier AZERTY
* combinaisons `SHIFT`, `CTRL`, `ALT`, `ALTGR`, `META`
* `Caps Lock` devient une deuxième couche complète de commandes
* support de tout le clavier principal, F1–F12, navigation et pavé numérique
* pressions longues / doubles volontairement laissées de côté
* erreur de configuration isolée : les autres touches continuent de fonctionner
* fallback intégré reproduisant exactement la configuration v1.4.1
* configuration client conservée lors des mises à jour
* validation de la configuration par CVP Doctor


v1.5 RC2 - configuration et voix pilotées par TOML
* `keyboard.toml` devient le mode d'emploi intégré
* section `[speech]` active : pregenerated / hybrid / runtime
* `generation = configured` génère uniquement les WAV utilisés par le profil client
* déduplication des actions avant génération
* Piper runtime chargé une seule fois par worker persistant
* cache des phrases générées à la demande
* choix `voice` et `length_scale` pris en compte
* régénération automatique des WAV nécessaires si le profil Piper change
* catalogue maître ConPianist dans `docs/FUNCTION_CATALOG.md`
* CVP Doctor adapté aux banques vocales partielles/configurées
