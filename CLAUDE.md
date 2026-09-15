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
  `graph.json` au runtime. `docs/files/` contient les images/fichiers
  joints aux notes (généré par `scripts/import_drafts.py`, jamais à la
  main). C'est tout ce qu'il faut publier.

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

## Soumission par un tiers

Deux canaux, aucun ne demande de toucher au code :

1. **Bouton "✏️ Ajouter une bulle" sur la page** (le principal, pas de compte
   requis). En mode ajout, cliquer sur une bulle existante ouvre un
   formulaire pour créer une sous-bulle reliée ; cliquer dans le vide crée
   une bulle libre. Ces ajouts sont stockés uniquement dans le
   `localStorage` du navigateur de la personne (clé `secondCerveau.drafts`)
   — ils ne sont jamais envoyés nulle part automatiquement, et ne
   sont visibles que sur son propre appareil. Un bouton "⬇️ Exporter"
   télécharge ces brouillons en JSON (`mes-notes.json`) pour qu'elle te les
   transmette par le moyen de son choix (message, email...).

   Quand on te donne un fichier `mes-notes.json` exporté ainsi :

   ```
   python3 scripts/import_drafts.py chemin/vers/mes-notes.json
   ```

   crée les fichiers `wiki/*.md` correspondants (ignore ceux dont l'id
   existe déjà). Une note peut aussi porter un lien externe et une image
   ou un fichier joint (upload direct sur la page, max ~4 Mo côté
   navigateur) : le script les décode et les écrit dans `docs/files/`
   automatiquement. Relis les notes créées, ajuste `group`/`links`/le
   corps si besoin (le script se contente de convertir tel quel), puis
   régénère le graphe comme d'habitude.

2. **Issue GitHub** (`.github/ISSUE_TEMPLATE/nouvelle-note.yml`, formulaire
   sujet/matière/lien/description) — plus adapté à toi qu'à quelqu'un qui ne
   veut pas de compte GitHub. Traite chaque issue comme une entrée de
   `raw/` (voir workflow ci-dessus), crée la ou les notes correspondantes,
   régénère le graphe, ferme l'issue avec un commentaire pointant vers la
   note créée.

Il n'y a pas de chat intégré à la page : c'est un site statique GitHub Pages,
donc aucune conversation avec Claude n'y est possible sans exposer une clé
API côté client ou héberger un backend — hors de portée de ce projet en
l'état.

## Publication

`docs/` est le dossier servi par GitHub Pages (Settings → Pages → Deploy
from a branch → `main` / `/docs`). Après avoir régénéré `graph.json`, un
`git push` sur `main` suffit à mettre la page à jour — pas de build step.
