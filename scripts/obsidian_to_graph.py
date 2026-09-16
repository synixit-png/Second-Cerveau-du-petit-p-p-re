#!/usr/bin/env python3
"""Convertit un vault Obsidian en graphe pour la page 3D de ce projet, sans
toucher au wiki/ de ce dépôt.

Contrairement à generate_graph.py (qui lit exclusivement wiki/*.md), ce
script lit N'IMPORTE QUEL vault Obsidian : il détecte les matières/thèmes
à partir des tags ou du dossier de chaque note, suit les [[liens Obsidian]]
pour construire le graphe, et récupère les images/fichiers joints. Aucune
dépendance à installer (uniquement la bibliothèque standard de Python).

Usage :
    python3 scripts/obsidian_to_graph.py /chemin/vers/mon-vault [dossier-sortie]

Par défaut, le dossier de sortie est "./obsidian-graph". Il contient :
    - vault-graph.html   la page à ouvrir (double-clic, aucun serveur requis)
    - graph.json         les données du graphe (pour référence/débogage)
    - files/             les images et fichiers joints copiés du vault

Détection des matières : si une note a un champ "group"/"matiere"/"matière"
dans son frontmatter, ou un tag (frontmatter "tags:" ou "#tag" dans le
texte), c'est utilisé comme matière. Sinon, le dossier qui contient la note
(par rapport à la racine du vault) sert de matière ; les notes à la racine
vont dans "Notes".

Détection de la bulle centrale : une note nommée "Home", "Index", "Start"
ou "MOC" (insensible à la casse) est utilisée si elle existe, sinon la note
la plus reliée du vault.
"""
import json
import re
import shutil
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
EMBED_RE = re.compile(r"!\[\[([^\]|#]+)")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
INLINE_TAG_RE = re.compile(r"(?:^|\s)#([a-zA-Z0-9_/-]+)")
URL_RE = re.compile(r"https?://\S+")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
DOC_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}
HOME_NAMES = {"home", "index", "start", "moc"}

PALETTE = [
    "#7AA2FF", "#B98CFF", "#FFB35C", "#5CE1B8", "#FF6F91",
    "#66D9E8", "#F2C94C", "#EB5757", "#9B51E0", "#56CCF2",
]


def slugify(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "note"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw, body = m.group(1), text[m.end():]
    fields: dict = {}
    current_list_key = None
    for line in raw.splitlines():
        if re.match(r"^\s*-\s+", line) and current_list_key:
            fields.setdefault(current_list_key, [])
            fields[current_list_key].append(line.strip("- ").strip())
            continue
        current_list_key = None
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if not key:
            continue
        if not value:
            current_list_key = key
            continue
        if value.startswith("[") and value.endswith("]"):
            fields[key] = [v.strip().strip('"\'') for v in value[1:-1].split(",") if v.strip()]
        else:
            fields[key] = value.strip('"\'')
    return fields, body


def strip_markdown(text: str) -> str:
    text = FRONTMATTER_RE.sub("", text)
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`>]+", "", text)
    text = re.sub(r"\n{2,}", "\n\n", text).strip()
    return text


def excerpt(text: str, limit: int = 400) -> str:
    text = strip_markdown(text)
    if len(text) <= limit:
        return text or "(note vide)"
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def guess_group(fields: dict, rel_folder: str, body: str) -> str:
    for key in ("group", "matiere", "matière", "subject", "category", "categorie"):
        if fields.get(key):
            return str(fields[key]).strip()
    tags = fields.get("tags")
    if isinstance(tags, list) and tags:
        return str(tags[0]).lstrip("#").split("/")[0]
    if isinstance(tags, str) and tags.strip():
        return tags.split(",")[0].strip().lstrip("#").split("/")[0]
    m = INLINE_TAG_RE.search(body)
    if m:
        return m.group(1).split("/")[0]
    return rel_folder or "Notes"


def find_referenced_file(name: str, by_basename: dict[str, Path]) -> Path | None:
    name = name.split("|")[0].split("#")[0].strip()
    return by_basename.get(Path(name).name.lower())


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage : python3 scripts/obsidian_to_graph.py <vault> [dossier-sortie]")

    vault = Path(sys.argv[1]).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"Dossier introuvable : {vault}")
    outdir = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else Path.cwd() / "obsidian-graph"
    files_dir = outdir / "files"

    md_paths = [p for p in vault.rglob("*.md") if ".obsidian" not in p.parts and ".trash" not in p.parts]
    if not md_paths:
        sys.exit(f"Aucune note .md trouvée dans {vault}")

    all_files_by_basename = {
        p.name.lower(): p for p in vault.rglob("*") if p.is_file() and ".obsidian" not in p.parts
    }

    name_to_id: dict[str, str] = {}
    used_ids: set[str] = set()
    parsed: list[dict] = []

    for path in md_paths:
        raw = path.read_text(encoding="utf-8", errors="replace")
        fields, body = parse_frontmatter(raw)
        stem = path.stem
        base_id = slugify(fields.get("title", stem))
        note_id = base_id
        i = 2
        while note_id in used_ids:
            note_id = f"{base_id}-{i}"
            i += 1
        used_ids.add(note_id)
        name_to_id[stem.lower()] = note_id

        rel_folder = str(path.relative_to(vault).parent).replace("\\", "/")
        rel_folder = "" if rel_folder == "." else rel_folder.split("/")[0]

        parsed.append({
            "id": note_id, "path": path, "stem": stem, "fields": fields,
            "body": body, "rel_folder": rel_folder,
        })

    nodes: dict[str, dict] = {}
    link_pairs: set[tuple] = set()
    degree: dict[str, int] = {}

    for note in parsed:
        note_id, fields, body = note["id"], note["fields"], note["body"]
        group_raw = guess_group(fields, note["rel_folder"], body)
        group = slugify(group_raw)

        node = {
            "id": note_id,
            "title": fields.get("title", note["stem"]),
            "group": group,
            "body": excerpt(body),
        }

        url_field = fields.get("link") or fields.get("url")
        if url_field:
            node["link"] = url_field
        elif (m := URL_RE.search(body)):
            node["link"] = m.group(0)

        embed_match = EMBED_RE.search(body) or MD_IMAGE_RE.search(body)
        if embed_match:
            ref = find_referenced_file(embed_match.group(1), all_files_by_basename)
            if ref and ref.suffix.lower() in IMAGE_EXTS:
                files_dir.mkdir(parents=True, exist_ok=True)
                dest = files_dir / f"{note_id}{ref.suffix.lower()}"
                shutil.copyfile(ref, dest)
                node["image"] = f"files/{dest.name}"
            elif ref and ref.suffix.lower() in DOC_EXTS:
                files_dir.mkdir(parents=True, exist_ok=True)
                dest = files_dir / f"{note_id}{ref.suffix.lower()}"
                shutil.copyfile(ref, dest)
                node["file"] = {"name": ref.name, "url": f"files/{dest.name}"}

        nodes[note_id] = node
        degree[note_id] = 0

        for target_name in WIKILINK_RE.findall(body):
            target_id = name_to_id.get(target_name.split("|")[0].split("#")[0].strip().lower())
            if not target_id or target_id == note_id:
                continue
            link_pairs.add(tuple(sorted((note_id, target_id))))

    links = [{"source": a, "target": b} for a, b in sorted(link_pairs)]
    for a, b in link_pairs:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1

    hub = None
    for note in parsed:
        if note["stem"].strip().lower() in HOME_NAMES:
            hub = note["id"]
            break
    if hub is None and degree:
        hub = max(degree, key=lambda k: (degree[k], k))

    group_keys = sorted({n["group"] for n in nodes.values()})
    groups = {
        key: {"label": key.replace("-", " ").title(), "color": PALETTE[i % len(PALETTE)]}
        for i, key in enumerate(group_keys)
    }

    graph = {"nodes": list(nodes.values()), "links": links, "groups": groups, "hub": hub}

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    template_path = Path(__file__).resolve().parent.parent / "docs" / "index.html"
    template = template_path.read_text(encoding="utf-8")
    fetch_block_re = re.compile(
        r'fetch\("graph\.json"\)\s*\n'
        r'\s*\.then\(r => \{.*?\}\)\s*\n'
        r'\s*\.then\(init\)\s*\n'
        r'\s*\.catch\(err => \{\s*\n'
        r'.*?\n'
        r'\s*\}\);',
        re.DOTALL,
    )
    embedded_json = json.dumps(graph, ensure_ascii=False)
    replacement = f"const EMBEDDED_GRAPH_DATA = {embedded_json};\ninit(EMBEDDED_GRAPH_DATA);"
    # Une fonction en remplacement : re.sub réinterprète sinon les
    # séquences \n, \1, etc. à l'intérieur du JSON injecté comme des
    # échappements de son propre mini-langage de template, ce qui corrompt
    # le JavaScript généré (retours à la ligne bruts au lieu de \n littéral).
    standalone, count = fetch_block_re.subn(lambda _m: replacement, template)
    if count != 1:
        sys.exit(
            "Le gabarit docs/index.html a changé de forme, impossible d'y intégrer le graphe "
            "automatiquement (aucun ou plusieurs blocs fetch(\"graph.json\") trouvés). "
            "Régénère graph.json seul et ouvre-le manuellement, ou ajuste ce script."
        )
    (outdir / "vault-graph.html").write_text(standalone, encoding="utf-8")

    print(f"{len(nodes)} notes, {len(links)} liens, {len(groups)} matière(s) : {', '.join(group_keys)}")
    print(f"Bulle centrale : {hub or '(aucune, note la plus reliée introuvable)'}")
    print(f"\nOuvre directement : {outdir / 'vault-graph.html'}")


if __name__ == "__main__":
    main()
