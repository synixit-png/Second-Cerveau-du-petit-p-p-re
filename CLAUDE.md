# Second cerveau

Second cerveau personnel organisé selon le pattern « LLM Wiki » (Karpathy) :
un tas de notes brutes distillées en notes wiki atomiques et interconnectées,
visualisées comme un graphe 3D navigable.

## Structure

- `raw/` — notes brutes, désordonnées, sans structure imposée. Captures de
  cours, brouillons, liens. Rien ici n'est visible dans le graphe.
- `wiki/` — notes distillées, une par fichier (`wiki/<id>.md`), format décrit
  dans `wiki/README.md`. C'est la seule source de vérité du graphe.
- `scripts/generate_graph.py` — parse `wiki/*.md` et régénère
  `docs/graph.json` (nœuds + liens).
- `docs/` — page GitHub Pages : `index.html` (le graphe 3D) charge
  `graph.json` au runtime. C'est tout ce qu'il faut publier.

## Workflow attendu de Claude

Quand on te demande de traiter des notes de `raw/` :

1. Lis le contenu brut concerné.
2. Découpe-le en notes atomiques (une idée/notion par fichier) plutôt que de
   copier un gros pavé de cours dans une seule note.
3. Pour chaque note, choisis un `id` court et stable (kebab-case, sans
   accents), un `group` parmi `maths`, `expert`, `ses`, `orient`, `methode`
   (ou une nouvelle valeur si le sujet ne rentre nulle part — dans ce cas
   ajoute aussi l'entrée correspondante dans `GROUPS` de `docs/index.html`),
   et remplis `links` avec les notes existantes (ou à créer dans le même lot)
   qui sont vraiment reliées — pas de liens forcés pour gonfler le graphe.
4. Écris le corps en 2-4 phrases denses, pas un cours complet : la note doit
   donner envie de cliquer sur les liens plutôt que tout expliquer d'un coup.
5. Une fois les fichiers `wiki/*.md` écrits ou modifiés, lance
   `python3 scripts/generate_graph.py` et vérifie qu'il ne signale pas de
   lien vers une note inconnue.
6. Ne modifie jamais `docs/graph.json` à la main — il est entièrement généré.

Ne crée pas de note dans `wiki/` uniquement pour "compléter" le graphe :
chaque note doit correspondre à un vrai concept qu'on veut pouvoir retrouver.

## Soumission par un tiers (bouton "Proposer une note")

La page `docs/index.html` a un bouton qui ouvre une issue GitHub pré-remplie
(`.github/ISSUE_TEMPLATE/nouvelle-note.yml`) — sujet, matière, lien optionnel,
description. Pas de compte GitHub pour toi requis en dehors de ça : n'importe
qui peut proposer une note sans toucher au code.

Quand on te demande de traiter les issues en attente (label `nouvelle-note`) :
traite chaque issue comme une entrée de `raw/` (voir workflow ci-dessus),
crée la ou les notes `wiki/*.md` correspondantes, régénère le graphe, puis
ferme l'issue avec un commentaire pointant vers la note créée.

Il n'y a pas de chat intégré à la page : c'est un site statique GitHub Pages,
donc aucune conversation avec Claude n'y est possible sans exposer une clé
API côté client ou héberger un backend — hors de portée de ce projet en
l'état. Le bouton "Proposer une note" est le canal de contribution.

## Publication

`docs/` est le dossier servi par GitHub Pages (Settings → Pages → Deploy
from a branch → `main` / `/docs`). Après avoir régénéré `graph.json`, un
`git push` sur `main` suffit à mettre la page à jour — pas de build step.
