# Profil GitHub animé : mode d'emploi

Toutes les cartes de `README.md` sont des SVG animés dans `cards/`, dessinés par
`scripts/render_readme_cards.py`. Le workflow `.github/workflows/update-profile-art.yml`
récupère tes contributions et redessine les cartes chaque jour.

## Modifier les textes

Tout est dans `scripts/render_readme_cards.py` : les 3 tuiles
(en bas du fichier, `tile(...)`), les projets (`REPOS`). Puis relance :

```
.venv\Scripts\python.exe scripts\fetch_contributions.py
$env:PYTHONUTF8=1; .venv\Scripts\python.exe scripts\render_readme_cards.py
```

## Changer de photo

Mets ta photo dans `photo/photo.jpg` (ce dossier n'est pas envoyé sur GitHub), puis :

```
.venv\Scripts\python.exe scripts\prep_photo.py
.venv\Scripts\python.exe scripts\make_ascii_svg.py
$env:PYTHONUTF8=1; .venv\Scripts\python.exe scripts\render_readme_cards.py
```

## Publier

1. Sur github.com, crée un repo **public** nommé exactement `CHRIISHEART` (vide, sans README).
2. `git push -u origin main`
3. Sur GitHub > Actions, lance « Mise à jour du profil » une fois pour vérifier.

## Serpent

Le workflow `.github/workflows/snake.yml` dessine un serpent rouge qui mange ta grille
(toutes les 12 h). Les images vont sur la branche `output` ; couleurs modifiables dans ce fichier.
