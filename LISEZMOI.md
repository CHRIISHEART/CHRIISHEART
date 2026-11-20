# Profil GitHub animé (style terminal) : mode d'emploi

Le profil (`README.md`) affiche 3 images SVG animées :

| Fichier | Contenu | Script |
|---|---|---|
| `contrib-heatmap.svg` | calendrier de contributions vert | `scripts/generate_streak_svg.py` |
| `chris-ascii.svg` | portrait ASCII dans un terminal | `scripts/make_ascii_svg.py` |
| `stats.svg` | séries, totaux et barres par mois | `scripts/render_stats_svg.py` |

Le workflow `.github/workflows/update-profile-art.yml` récupère tes contributions et
redessine le calendrier et les stats chaque jour.

## Tout régénérer à la main

```
.venv\Scripts\python.exe scripts\fetch_contributions.py
.venv\Scripts\python.exe scripts\generate_streak_svg.py
.venv\Scripts\python.exe scripts\render_stats_svg.py
```

## Changer de photo

Mets ta photo dans `photo/photo.jpg` (ce dossier n'est pas envoyé sur GitHub), puis :

```
.venv\Scripts\python.exe scripts\prep_photo.py
.venv\Scripts\python.exe scripts\make_ascii_svg.py
```

## Publier

```
git add -A
git commit -m "Mise à jour"
git pull
git push
```
