# wiki/

Notes distillées, une idée par fichier (`<id>.md`). Format :

```
---
title: Titre lisible de la note
group: maths | expert | ses | orient | methode
links: [autre-note, encore-une-autre]
link: https://exemple.com/ressource (optionnel)
image: files/mon-id.jpg (optionnel)
file: files/mon-id.pdf (optionnel)
fileName: Nom affiché du fichier.pdf (optionnel, avec "file")
---

Corps de la note : quelques phrases denses, pas un cours entier.
```

- `id` = nom du fichier sans l'extension, doit être stable (c'est la clé
  utilisée dans `links`).
- `group` détermine la couleur/la légende dans la vue 3D — utiliser une des
  cinq valeurs existantes ou en ajouter une dans `GROUPS` (`docs/index.html`).
- `links` liste les autres notes avec lesquelles celle-ci a un rapport direct.
  Les liens sont symétriques dans le graphe (A→B affiche aussi B→A), pas
  besoin de les déclarer dans les deux sens.
- `link`/`image`/`file` sont optionnels. `image` et `file` pointent vers un
  fichier physique dans `docs/files/` (chemin relatif à `docs/`, car seul ce
  dossier est publié par GitHub Pages) — ils sont générés automatiquement par
  `scripts/import_drafts.py` quand quelqu'un a joint une image/un fichier sur
  le site ; pas besoin de les remplir à la main sauf ajout manuel d'un fichier
  dans `docs/files/`.

Après toute modification de `wiki/`, relancer :

```
python3 scripts/generate_graph.py
```

pour régénérer `docs/graph.json`, puis committer les deux.
