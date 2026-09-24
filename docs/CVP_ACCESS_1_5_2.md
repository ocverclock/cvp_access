# CVP Access 1.5.2-RC1 — maintenance autonome consolidée

Date : **24 septembre 2026**

## Objet de la version

La 1.5.2-RC1 conserve le protocole Yamaha et le layout clavier de la 1.5.1-RC3, mais transforme la maintenance réseau en fonction officielle du paquet.

Cette version consolide dans GitHub :

- fallback réseau autonome ;
- priorité Ethernet / Wi-Fi normal sur le hotspot ;
- hotspot `CVP-ACCESS` uniquement lorsqu'aucun réseau normal n'est disponible ;
- portail Web local ;
- sélection persistante MIDI / clavier ;
- connexion à un Wi-Fi depuis le portail avec retour automatique au hotspot en cas d'échec ;
- accès Samba au projet et à la configuration ;
- syntaxes Samba adaptées à macOS/Linux et Windows ;
- adresses cliquables pour copie dans le dashboard et la carte clavier ;
- carte clavier toujours conçue pour une seule page A4 paysage ;
- intégration de ces composants dans les chemins d'installation et de mise à jour.

## Version et runtime

```text
Version            : 1.5.2-RC1
Frontend courant   : cvp_access_1_5_2.py
Base fonctionnelle : cvp_access_1_5_1_base.py
Runtime installé   : /opt/cvp-access/cvp_access.py
```

Architecture transitoire :

```text
cvp_access_1_5_2.py
-> cvp_access_1_5_1_base.py
-> cvp_access_v1.5.py
-> cvp_access_v1.4.1.py
```

Le changement de version ne modifie pas les commandes MIDI Yamaha validées. Le wrapper 1.5.2 formalise le paquet courant et permet au portail d'afficher la bonne version.

## Réseau

Priorité :

```text
Ethernet connecté
-> pas de hotspot

Wi-Fi normal connecté
-> pas de hotspot

aucun réseau normal
-> attente ~30 s
-> activation de CVP-ACCESS si une interface Wi-Fi existe
```

Si `CVP-ACCESS` est actif et qu'une connexion Ethernet ou Wi-Fi normale apparaît, le hotspot est arrêté.

Référence hotspot :

```text
SSID       : CVP-ACCESS
Raspberry  : 10.42.0.1/24
Portail    : http://10.42.0.1
```

Le mot de passe du hotspot n'est pas stocké dans le dépôt. Il est conservé localement dans `/etc/cvp-access/hotspot-password`.

## Portail Web

Le portail est servi sur le port HTTP 80 et accepte :

- localhost ;
- le sous-réseau du hotspot ;
- les sous-réseaux IPv4 privés directement connectés au Raspberry, Ethernet compris.

Fonctions :

- état CVP Access / fallback / portail ;
- réseau et hostname ;
- interfaces MIDI et sélection persistante ;
- clavier USB et sélection persistante ;
- audio Yamaha et USB ;
- événements utiles ;
- Doctor ;
- relance de CVP Access ;
- redémarrage du Raspberry ;
- scan / sélection d'un Wi-Fi ;
- accès à la carte clavier ;
- blocs Accès Web et Samba.

Les actions de modification nécessitent le mot de passe de maintenance, identique au mot de passe local `CVP-ACCESS`.

## Samba

Partages :

```text
CVP_access -> dépôt/projet
CVP_config -> /etc/cvp-access
```

### macOS / Linux

```text
smb://<hostname>.local/CVP_access
smb://<hostname>.local/CVP_config
smb://10.42.0.1/CVP_access
smb://10.42.0.1/CVP_config
```

Sur macOS : Finder → Aller → Se connecter au serveur… (`Cmd + K`).

Sous Linux/GNOME/Zorin, utiliser également `smb://...`. Le paquet `gvfs-backends` peut être nécessaire côté ordinateur client.

### Windows

```text
\\<hostname>.local\CVP_access
\\<hostname>.local\CVP_config
\\10.42.0.1\CVP_access
\\10.42.0.1\CVP_config
```

Le dashboard présente les adresses sous forme cliquable afin de les copier. La carte clavier offre la même fonction lorsqu'elle est consultée dans un navigateur.

## Carte clavier

Deux blocs de maintenance sont intégrés :

```text
Accès Web
Partages Samba
```

Contraintes d'impression :

```text
A4 paysage
marge 6 mm
une seule page
éléments interactifs masqués à l'impression
```

Le hostname est généré dynamiquement à partir du Raspberry qui produit la carte.

## Installation et mise à jour

Vérification du paquet :

```bash
python3 VERIFY_PACKAGE_152.py
```

Upgrade direct depuis une 1.5.x :

```bash
sudo bash cvp_access_installer/upgrade_1_5_2.sh
```

Installation neuve :

```bash
sudo bash cvp_access_installer/install.sh
```

Mise à jour générale :

```bash
sudo bash cvp_access_installer/update.sh
```

Les installateurs `install.sh` et `update.sh` convergent désormais vers `upgrade_1_5_2.sh` pour déployer le frontend courant et la maintenance 1.5.2.

## Fichiers principaux

```text
cvp_access_1_5_2.py
VERIFY_PACKAGE_152.py
cvp_access_installer/upgrade_1_5_2.sh
cvp_access_installer/install_maintenance.sh
cvp_access_installer/network/cvp-wifi-fallback
cvp_access_installer/network/cvp-wifi-connect
cvp_access_installer/tools/cvp_web.py
cvp_access_installer/samba/cvp-access.conf.in
cvp_keyboard_map.py
docs/NETWORK_MAINTENANCE_PORTAL.md
```

## Validation actuelle

Confirmé en fonctionnement réel :

- portail Web démarré et accessible sur le LAN ;
- dashboard et API d'état ;
- détection de l'interface MIDI générique ;
- fallback `CVP-ACCESS` et accès SSH sur `10.42.0.1` lors du test dédié ;
- priorité réseau normal / absence de hotspot sur connexion Ethernet après correction.

À valider encore sur le matériel client :

- accès Samba en étant réellement connecté au hotspot `CVP-ACCESS` ;
- comportement Finder macOS via `smb://10.42.0.1/...` ;
- ouverture automatique du portail captif selon l'OS ;
- scan Wi-Fi pendant le mode hotspot selon le chipset Wi-Fi utilisé.

Ne pas présenter ces derniers points comme validés tant que le test réel n'a pas été effectué.
