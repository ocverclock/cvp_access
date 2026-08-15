# Configuration CVP Access v1.5 RC2

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

## Validation

```bash
python3 /opt/cvp-access/cvp_keyboard.py \
  --check /etc/cvp-access/keyboard.toml
```

## Pré-génération vocale selon le TOML

```bash
~/.local/share/cvp-access/piper-env/bin/python \
  /opt/cvp-access/generate_configured_voices.py \
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

`install.sh` et `update.sh` ne remplacent pas un `keyboard.toml` client déjà
présent. Le modèle de la version courante reste disponible ici :

```text
/opt/cvp-access/default-keyboard.toml
```

## Sécurité

Le TOML ne peut sélectionner que les actions déclarées dans CVP Access. Il ne
peut pas exécuter arbitrairement du Python ou une commande shell.
