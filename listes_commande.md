Voici ce que j’ai trouvé dans ConPianist :

Contrôle des morceaux MIDI
Play
Pause
Stop
position dans le morceau, par mesure + temps
longueur du morceau
boucle entre deux positions
reset du morceau
récupération du nom du morceau
chargement de fichiers MIDI vers certains pianos par réseau.
Contrôle des 16 pistes MIDI
ON/OFF de chaque piste ← notre Active
détection si une piste est réellement présente dans le fichier MIDI
volume individuel 0–127
panoramique
quantité de réverb
choix de la Voice/instrument de chaque piste
récupération de la Voice actuelle.
Parties du morceau
ConPianist distingue :
Right Hand
Left Hand
Backing
ON/OFF de chacune
attribution d’un canal MIDI à Right/Left
détection/affectation automatique des parties.
Tempo / tonalité
tempo 5 à 280 BPM
reset tempo
transposition −12 à +12 demi-tons.

Guide Yamaha

Guide ON/OFF
modes :
Correct Key
Any Key
Your Tempo
sélection des parties Right / Left / Backing.

Attention : ce n’est pas le Voice Guide d’accessibilité dont tu parlais. Je n’ai trouvé aucune commande Voice Guide ou équivalent dans ConPianist. Le Guide ici est la fonction pédagogique Yamaha liée à l’apprentissage des morceaux.

Voices / clavier
choix de la Voice Main
Left
Layer
choix direct de la Voice de chaque canal MIDI
octave −2 à +2
split point
Local Control ON/OFF.
Mixer
volume
pan
reverb
choix du type de réverb
ON/OFF des canaux
sélection des parties
sélection de Voices
balance entre Main / Left / Layer / Song / Mic / Aux In.
Réglages piano
Le protocole contient aussi :
position du couvercle virtuel : Open / Half Open / Closed
Environment
Brightness/timbre
courbe de toucher :
Soft 2
Soft 1
Medium
Hard 1
Hard 2
Fixed Curve ON/OFF
Fixed Velocity
Master Tune
VRM ON/OFF
Damper Resonance
String Resonance
Key-Off Sampling.
Stream Lights
Pour les CSP équipés :
Stream Lights ON/OFF
vitesse Slow/Fast.
Lecture de l’état du piano — très intéressant pour nous
Le protocole n’est pas uniquement « envoyer une commande ». Il possède :
GET → demander une valeur au piano
SET → modifier une valeur
INFO → recevoir une valeur
RESPONSE → réponse à une modification
RESET
EVENTS → demander au piano d'envoyer les changements d’état.
