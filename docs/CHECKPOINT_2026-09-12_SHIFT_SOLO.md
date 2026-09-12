# Checkpoint — Solo Song avec Maj

Date : **12 septembre 2026**

Version : **CVP Access 1.5.1-RC3**

Instrument de référence : **Yamaha CVP-905 firmware 1.03**

## Migration clavier confirmée

L'installation de référence a été migrée de l'ancien profil Solo `ALT+...` vers le nouveau profil `SHIFT+...`.

La migration a supprimé les 16 anciennes affectations officielles :

```text
ALT+A .. ALT+K -> song_track_solo:1 .. song_track_solo:16
```

et ajouté :

```text
SHIFT+A .. SHIFT+K -> song_track_solo:1 .. song_track_solo:16
```

Terminologie utilisateur : **Maj + touche de piste = Solo Song**.

Les touches simples A..K restent les toggles ON/OFF individuels des 16 pistes Song.

`L` remet les 16 pistes Song sur ON.

## Vérification du paquet

Après `git pull` :

```text
CVP Access 1.5.1 RC3 package: OK
```

## Génération vocale

Les banques vocales étaient déjà complètes après migration :

```text
Required WAV files: 863
Generated: 0; already present: 863

WAV supplémentaires requis : 262
Generated: 0; existing: 262
```

Conclusion : le passage de Alt vers Maj ne nécessite aucune régénération des 16 annonces `Solo piste N`.

## Doctor après migration

Résultat observé sur le Raspberry de référence :

```text
CVP Access Doctor 1.5.1
========================================================================
OK    Runtime 1.5.1             modules complets
OK    Version runtime           1.5.1-RC3
OK    Layout accessibilité      présente
OK    WAV états 1.5.1           10 présents
OK    WAV mute Style            8 présents
OK    WAV Solo Song             16 présents
========================================================================
```

## Validation fonctionnelle matérielle

Test confirmé sur le Yamaha CVP-905 de référence :

```text
Maj + touche de piste
-> la piste sélectionnée passe / reste sur ON
-> les 15 autres pistes Song passent sur OFF
-> l'annonce « Solo piste N » est produite
```

Le mode Solo Song avec **Maj** est donc **VALIDÉ MATÉRIELLEMENT** sur CVP-905 firmware 1.03.

`L` reste la commande prévue pour réactiver ensuite les 16 pistes Song.

## Statut

**Migration / installation / layout / banques WAV / Solo Song Maj : VALIDÉS.**
