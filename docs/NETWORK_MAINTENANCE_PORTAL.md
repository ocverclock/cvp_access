# CVP Access — réseau autonome et interface Web de maintenance

Date : 24 septembre 2026

## But

CVP Access doit rester administrable chez un client qui ne possède ni box ni Wi-Fi.

Le Raspberry privilégie toute connexion réseau normale déjà disponible. Ethernet a également priorité sur le hotspot : si une liaison Ethernet ou un Wi-Fi normal est connecté, `CVP-ACCESS` reste arrêté. Si aucun réseau normal n'est disponible après environ 30 secondes, il active son propre point d'accès `CVP-ACCESS`.

## Wi-Fi fallback validé

Configuration de référence :

```text
SSID         CVP-ACCESS
sécurité     WPA-PSK
mode         AP
bande        2,4 GHz
IPv4         shared
IP Raspberry 10.42.0.1/24
```

Le mot de passe n'est pas documenté dans le dépôt.

Composants actuellement installés sur le Raspberry de référence :

```text
/usr/local/sbin/cvp-wifi-fallback
/etc/systemd/system/cvp-wifi-fallback.service
NetworkManager profile: CVP-ACCESS
```

Principe :

```text
Ethernet ou Wi-Fi normal disponible
  -> la connexion normale est prioritaire
  -> le hotspot reste arrêté

aucun réseau normal disponible
  -> délai ~30 s
  -> CVP-ACCESS est activé si une interface Wi-Fi existe
  -> maintenance locale sur 10.42.0.1
```

## Intégration installateur

Le fallback doit devenir une fonction officielle de l'installation CVP Access et non un réglage manuel.

L'installateur devra :

1. créer ou mettre à jour le profil NetworkManager `CVP-ACCESS` ;
2. fixer l'adresse locale `10.42.0.1/24` ;
3. installer le script de fallback ;
4. installer et activer le service systemd ;
5. ne pas écraser un mot de passe hotspot personnalisé lors d'un upgrade ;
6. vérifier le service dans le Doctor.

## Interface Web locale

Une interface Web locale doit devenir le point de maintenance principal. Elle doit fonctionner sans accès Internet.

URLs cibles :

```text
http://10.42.0.1
http://cvp-access.local
```

### Tableau de bord

Afficher au minimum :

- version CVP Access ;
- état de `cvp-access.service` ;
- état de `cvp-wifi-fallback.service` ;
- SSID/réseau courant ;
- interface MIDI sélectionnée ;
- liste des interfaces MIDI disponibles ;
- périphérique audio CVP ;
- clavier USB ;
- modèle Yamaha identifié si une identification fiable devient disponible ;
- résultat synthétique du Doctor ;
- derniers événements utiles.

Les logs doivent être filtrés pour présenter les événements utiles à un technicien et non un dump brut permanent.

### Affectation dynamique des périphériques

Règle de sélection :

```text
interface explicitement configurée disponible
    -> utiliser celle-ci

sinon interface connue unique
    -> sélection automatique

sinon un seul périphérique MIDI bidirectionnel
    -> sélection automatique

sinon plusieurs candidats possibles
    -> ne rien choisir au hasard
    -> demander le choix dans l'interface Web
```

Le choix manuel doit pouvoir être mémorisé dans une configuration persistante indépendante du numéro ALSA `hw:X,Y,Z`, car ce numéro peut changer après redémarrage ou rebranchement.

### Actions de maintenance

Actions envisagées :

- relancer CVP Access ;
- lancer le Doctor ;
- tester MIDI ;
- tester audio ;
- afficher la carte clavier ;
- sélectionner une interface MIDI ;
- afficher les périphériques USB ;
- voir les événements récents ;
- redémarrer le Raspberry avec confirmation.

Éviter d'exposer un shell Web général.

## Portail captif

Lorsque le technicien se connecte à `CVP-ACCESS`, le Raspberry peut se comporter comme un portail captif afin que téléphone/tablette/ordinateur propose automatiquement la page de maintenance.

Ce mécanisme dépend du système client et ne doit jamais être le seul moyen d'accès. La page doit toujours rester disponible directement sur `10.42.0.1` et via mDNS.

Architecture envisagée :

```text
CVP-ACCESS
   |
NetworkManager hotspot
   |
DNS/DHCP local
   |
détection portail captif
   |
serveur Web CVP Access
   |
dashboard / diagnostic / configuration
```

## Sécurité

L'interface Web reste limitée aux réseaux locaux directement connectés au Raspberry.

Pour la phase actuelle de mise au point, la demande de mot de passe sur les boutons de maintenance est **suspendue par défaut** :

```text
CVP_WEB_REQUIRE_AUTH=0
```

Les boutons Doctor, relance, sélection MIDI/clavier, connexion Wi-Fi et redémarrage sont donc utilisables directement depuis le portail local.

Le mécanisme d'authentification n'est pas supprimé. Pour le réactiver :

```text
CVP_WEB_REQUIRE_AUTH=1
```

puis redémarrer `cvp-web.service`. Le mot de passe utilisé redevient celui stocké dans `/etc/cvp-access/hotspot-password`.

Ce mode sans mot de passe ne doit pas conduire à exposer le portail sur Internet ou sur une interface non maîtrisée.

## État

Le fallback Wi-Fi est validé en fonctionnement réel.

Le fallback Wi-Fi est validé en fonctionnement réel. Le portail Web, l'affectation MIDI/clavier persistante et le portail captif sont implémentés dans le dépôt ; leur validation matérielle complète reste à effectuer.


## Implémentation actuelle

Fichiers :

```text
cvp_access_installer/install_maintenance.sh
cvp_access_installer/network/cvp-wifi-fallback
cvp_access_installer/systemd/cvp-wifi-fallback.service.in
cvp_access_installer/systemd/cvp-web.service.in
cvp_access_installer/tools/cvp_web.py
```

Le portail HTTP écoute sur le port 80. Il accepte localhost, le sous-réseau du hotspot `10.42.0.0/24` et les sous-réseaux IPv4 privés directement connectés au Raspberry, y compris Ethernet et Wi-Fi.

Il expose :

- état des services ;
- réseau courant ;
- interfaces MIDI ;
- sélection persistante MIDI ;
- claviers USB et sélection persistante ;
- audio Yamaha détecté ;
- périphériques USB ;
- événements CVP Access filtrés ;
- lancement du Doctor ;
- relance de CVP Access ;
- redémarrage du Raspberry ;
- carte clavier.

Les sélections sont enregistrées dans `/etc/cvp-access/hardware.toml`.

Le portail captif combine DNS wildcard sur le dnsmasq de la connexion partagée, redirections des URLs de détection usuelles et une API captive sur `/captive-portal` annoncée par DHCP option 114.

La génération du mot de passe d'un hotspot neuf est aléatoire. Un profil `CVP-ACCESS` déjà présent conserve son mot de passe.


## Connexion à un Wi-Fi depuis le portail

Le portail est accessible dans deux situations :

```text
CVP-ACCESS
-> http://10.42.0.1

Raspberry connecté à un Wi-Fi normal
-> http://<hostname>.local
-> ou l'adresse IPv4 du Raspberry
```

L'accès HTTP est limité à localhost, au sous-réseau du hotspot et aux sous-réseaux IPv4 privés directement connectés au Raspberry.

Le dashboard permet :

1. de lancer un scan des réseaux Wi-Fi ;
2. de sélectionner un SSID ou d'en saisir un manuellement ;
3. de saisir le mot de passe du réseau ;
4. de lancer la tentative de connexion.

En mode courant `CVP_WEB_REQUIRE_AUTH=0`, la connexion Wi-Fi depuis le portail ne demande pas de mot de passe de maintenance. Si l'authentification est réactivée, elle utilise le mot de passe du hotspot `CVP-ACCESS`.

Séquence :

```text
sélection SSID + mot de passe
-> arrêt de CVP-ACCESS
-> tentative de connexion au Wi-Fi demandé
-> succès : profil CVP-WIFI-xxxxxxxx mémorisé + autoconnect
-> échec : profil désactivé + réactivation immédiate de CVP-ACCESS
```

Le service `cvp-wifi-fallback.service` reste une deuxième sécurité si la réactivation immédiate du hotspot échoue.

Le mot de passe du Wi-Fi cible est écrit uniquement dans une requête temporaire sous `/run`, mode 0600, supprimée après traitement. La connexion persistante est ensuite gérée par NetworkManager.


## Keyboard map — accès maintenance

La carte clavier imprimable contient deux encarts compacts :

```text
Accès Web
- http://<hostname>.local
- http://10.42.0.1 en mode CVP-ACCESS

Partages Samba
- Mac / Linux : smb://<hostname>.local/CVP_access
- Mac / Linux : smb://<hostname>.local/CVP_config
- Mac / Linux hotspot : smb://10.42.0.1/CVP_access
- Mac / Linux hotspot : smb://10.42.0.1/CVP_config
- Windows : \\<hostname>.local\CVP_access
- Windows : \\<hostname>.local\CVP_config
```

Ces deux blocs sont aussi affichés dans le dashboard Web.

La carte reste conçue pour tenir sur **une seule page A4 paysage**. Le CSS d'impression fixe la page à A4 landscape avec marge de 6 mm, limite la hauteur utile et empêche les blocs maintenance de se couper entre deux pages.


## Samba et copie des adresses

Les partages officiels sont :

```text
CVP_access -> dépôt/projet CVP Access
CVP_config -> configuration client
```

Le dashboard affiche séparément les syntaxes adaptées aux systèmes :

```text
Mac / Linux :
smb://<hostname>.local/CVP_access
smb://<hostname>.local/CVP_config
smb://10.42.0.1/CVP_access
smb://10.42.0.1/CVP_config

Windows :
\\<hostname>.local\CVP_access
\\<hostname>.local\CVP_config
\\10.42.0.1\CVP_access
\\10.42.0.1\CVP_config
```

Chaque adresse affichée dans le dashboard est cliquable pour la copier. La carte clavier offre la même fonction à l'écran ; les marqueurs interactifs sont masqués à l'impression.

Sur macOS, utiliser Finder → **Aller → Se connecter au serveur…** (`Cmd + K`) et une URL `smb://...`. Sous Linux/GNOME/Zorin, utiliser également `smb://...`; si le gestionnaire de fichiers ne sait pas monter SMB, installer le backend `gvfs-backends`.

## Intégration version 1.5.2-RC1

La maintenance autonome fait partie du paquet officiel **CVP Access 1.5.2-RC1**.

Les trois chemins d'installation convergent vers la même configuration :

```text
cvp_access_installer/install.sh
cvp_access_installer/update.sh
cvp_access_installer/upgrade_1_5_2.sh
```

Ils installent ou rafraîchissent le runtime courant, Samba, le portail Web, la carte clavier, le fallback réseau et les services systemd associés.


## Mise à jour depuis GitHub

Le dashboard possède un bouton **Mettre à jour depuis GitHub**.

Séquence :

```text
clic + confirmation
-> lancement d'un service systemd transitoire
-> vérification que le dépôt local est propre
-> git pull --ff-only avec l'utilisateur CVP
-> exécution du VERIFY_PACKAGE_* le plus récent
-> exécution de l'upgrade_* le plus récent
-> redémarrage des services par l'installateur de version
```

La mise à jour continue même si `cvp-web.service` se redémarre pendant l'installation. Le dashboard se reconnecte ensuite et affiche l'état ainsi que les dernières lignes du journal.

Fichiers d'état temporaires :

```text
/run/cvp-access-update-state
/run/cvp-access-update.log
```

Par sécurité, si le dépôt contient des modifications locales, le bouton refuse la mise à jour afin de ne rien écraser.
