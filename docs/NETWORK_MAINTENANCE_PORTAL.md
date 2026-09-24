# CVP Access — réseau autonome et interface Web de maintenance

Date : 24 septembre 2026

## But

CVP Access doit rester administrable chez un client qui ne possède ni box ni Wi-Fi.

Le Raspberry essaie d'abord les réseaux Wi-Fi déjà connus. Si aucun réseau normal n'est disponible après environ 30 secondes, il active son propre point d'accès `CVP-ACCESS`.

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
Wi-Fi connu disponible
  -> NetworkManager se connecte normalement
  -> le hotspot reste arrêté

aucun Wi-Fi connu
  -> délai ~30 s
  -> CVP-ACCESS est activé
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

L'interface Web de maintenance est destinée au réseau local CVP-ACCESS. Les opérations modifiant la configuration doivent être protégées au minimum par une authentification locale ou un secret de session. Le service ne doit pas être exposé automatiquement sur une interface réseau publique.

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

Le portail HTTP écoute sur le port 80 mais n'accepte que les clients du sous-réseau `10.42.0.0/24` et localhost.

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
