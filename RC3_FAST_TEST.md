# RC3 FAST

Cette passe ne change aucune propriété SysEx validée.

Optimisations :
- volume Song/Main : premier GET seulement, puis cache de la dernière valeur confirmée ;
- contrôle GET après SET conservé ;
- vérification rapide : 12 ms, avec second essai ;
- fallback plus lent uniquement si le contrôle rapide échoue ;
- annonces de volume : les anciennes valeurs en attente deviennent obsolètes ;
- version runtime : `1.5-RC3-dev-fast`.

Application :

```bash
python3 apply_rc3_fast.py ~/CVP_access
```

Puis :

```bash
cd ~/CVP_access
sudo systemctl stop cvp-access
pkill -f 'amidi.*-d'
python3 cvp_access_v1.5.py
```

Test recommandé : appuyer rapidement 5 à 10 fois sur HOME, END, INSERT et DELETE,
puis refaire avec SHIFT.
