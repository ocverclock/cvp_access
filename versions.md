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
Ajout du contrôle du lecteur Song et de l’annonce de position sur Yamaha CVP-905.
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
* identification du clavier de développement corrigée en Yamaha CVP-905

