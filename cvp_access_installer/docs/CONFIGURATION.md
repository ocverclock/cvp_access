# Configuration clavier — CVP Access 1.6.1-RC2

Le fichier principal est volontairement auto-documenté :

```text
/etc/cvp-access/keyboard.toml
```

Il contient à la fois la configuration du clavier et la stratégie vocale Piper.

## Accès Samba

```text
\\cvp-access.local\CVP_config\keyboard.toml
```

Le dépôt Git reste disponible séparément :

```text
\\cvp-access.local\CVP_access
```

## Sauvegarde

```bash
sudo cp /etc/cvp-access/keyboard.toml \
  /etc/cvp-access/keyboard.toml.backup
```

## Régénération après modification manuelle

Valider d'abord la configuration :

```bash
python3 /opt/cvp-access/cvp_keyboard.py \
  --check /etc/cvp-access/keyboard.toml
```

Régénérer ensuite la carte clavier :

```bash
python3 /opt/cvp-access/cvp_keyboard_map.py \
  --config /etc/cvp-access/keyboard.toml \
  --output /etc/cvp-access/keyboard-map.html
```

Puis les annonces vocales nécessaires :

```bash
~/.local/share/cvp-access/piper-env/bin/python \
  /opt/cvp-access/generate_configured_voices.py \
  --config /etc/cvp-access/keyboard.toml

~/.local/share/cvp-access/piper-env/bin/python \
  /opt/cvp-access/generate_151_voices.py \
  --config /etc/cvp-access/keyboard.toml
```

Avec :

```toml
[speech]
mode = "hybrid"
generation = "configured"
```

seuls les WAV utiles aux actions présentes dans `[keys]` sont pré-générés.

Le générateur déduplique les actions : plusieurs touches associées à la même
fonction n'entraînent pas plusieurs générations du même WAV.

Si `voice` ou `length_scale` change, les WAV requis sont automatiquement
régénérés avec le nouveau profil Piper.

## Modes vocaux

```text
pregenerated  WAV uniquement
hybrid        WAV si présent, sinon Piper à la demande + cache
runtime       Piper à la demande pour toutes les annonces
```

Le mode hybride charge Piper dans un worker persistant uniquement lorsqu'une
phrase dynamique est réellement nécessaire. Le modèle n'est donc pas rechargé
à chaque touche.

## Appliquer les modifications

```bash
sudo systemctl restart cvp-access
```

## Restauration

```bash
sudo cp /etc/cvp-access/keyboard.toml.backup \
  /etc/cvp-access/keyboard.toml
sudo systemctl restart cvp-access
```

## Conservation lors des mises à jour

`install.sh` et `update.sh` ne remplacent pas un `keyboard.toml` client déjà présent.

Pour la chaîne consolidée 1.6.1-RC2, le profil usine courant installé par l'upgrade est :

```text
/opt/cvp-access/default-keyboard-1.5.1.toml
```

Un fichier historique `/opt/cvp-access/default-keyboard.toml` peut aussi être présent car `install.sh` / `update.sh` passent encore par l'ancien bootstrap v1.5 avant de déployer la release courante. **Ne pas utiliser ce fichier historique comme référence de restauration RC2.**

Le chantier 1.7 doit supprimer cette ambiguïté et définir un seul mapping usine canonique.

## Sécurité

Le TOML ne peut sélectionner que les actions déclarées dans CVP Access. Il ne
peut pas exécuter arbitrairement du Python ou une commande shell.
