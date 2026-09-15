# wiki/

Notes distillées, une idée par fichier (`<id>.md`). Format :

```
---
title: Titre lisible de la note
group: maths | expert | ses | orient | methode
links: [autre-note, encore-une-autre]
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

Après toute modification de `wiki/`, relancer :

```
python3 scripts/generate_graph.py
```

pour régénérer `docs/graph.json`, puis committer les deux.
