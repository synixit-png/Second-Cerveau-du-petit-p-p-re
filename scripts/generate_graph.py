#!/usr/bin/env python3
"""Génère docs/graph.json à partir des notes markdown du dossier wiki/.

Chaque note wiki/<id>.md a un frontmatter minimal :

    ---
    title: Titre de la note
    group: maths
    links: [autre-note, encore-une-autre]
    link: https://exemple.com (optionnel)
    image: files/mon-id.jpg (optionnel, chemin relatif à docs/)
    file: files/mon-id.pdf (optionnel, chemin relatif à docs/)
    fileName: mon-cours.pdf (optionnel, nom affiché pour "file")
    ---

    Corps de la note.

Usage : python3 scripts/generate_graph.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"
OUTPUT = ROOT / "docs" / "graph.json"

HUB_ID = "accueil"
GROUPS = {
    "maths":   {"label": "Maths",        "color": "#7AA2FF"},
    "expert":  {"label": "Maths expert", "color": "#B98CFF"},
    "ses":     {"label": "SES",          "color": "#FFB35C"},
    "orient":  {"label": "Orientation",  "color": "#5CE1B8"},
    "methode": {"label": "Memecoin",     "color": "#FF6F91"},
}


def parse_note(path: Path) -> tuple[dict, list[str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: frontmatter manquant (doit commencer par '---')")
    end = text.index("\n---", 4)
    frontmatter_raw = text[4:end]
    body = text[end + 4:].strip()

    fields: dict[str, str] = {}
    links: list[str] = []
    for line in frontmatter_raw.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key == "links":
            inner = value.strip("[]").strip()
            links = [item.strip() for item in inner.split(",") if item.strip()]
        else:
            fields[key] = value

    note = {
        "id": path.stem,
        "title": fields.get("title", path.stem),
        "group": fields.get("group", "methode"),
        "body": body,
    }
    if fields.get("link"):
        note["link"] = fields["link"]
    if fields.get("image"):
        note["image"] = fields["image"]
    if fields.get("file"):
        note["file"] = {"name": fields.get("fileName", fields["file"]), "url": fields["file"]}
    return note, links


def main() -> None:
    if not WIKI_DIR.is_dir():
        sys.exit(f"Dossier introuvable : {WIKI_DIR}")

    notes_by_id: dict[str, dict] = {}
    links_by_id: dict[str, list[str]] = {}
    for path in sorted(WIKI_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        note, links = parse_note(path)
        notes_by_id[note["id"]] = note
        links_by_id[note["id"]] = links

    nodes = list(notes_by_id.values())

    seen_pairs: set[str] = set()
    links = []
    for source_id, targets in links_by_id.items():
        for target_id in targets:
            if target_id not in notes_by_id:
                print(f"Avertissement : '{source_id}' pointe vers une note inconnue '{target_id}'", file=sys.stderr)
                continue
            pair_key = "|".join(sorted([source_id, target_id]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            links.append({"source": source_id, "target": target_id})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {"nodes": nodes, "links": links, "groups": GROUPS, "hub": HUB_ID},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"{len(nodes)} notes, {len(links)} liens -> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
