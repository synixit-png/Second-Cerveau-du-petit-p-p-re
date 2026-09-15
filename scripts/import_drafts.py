#!/usr/bin/env python3
"""Importe un export de brouillons (le fichier mes-notes.json téléchargé via
le bouton "Exporter" du site) dans wiki/*.md.

Usage : python3 scripts/import_drafts.py chemin/vers/mes-notes.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage : python3 scripts/import_drafts.py <export.json>")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    links_by_id: dict[str, set[str]] = {}
    for link in data.get("links", []):
        links_by_id.setdefault(link["source"], set()).add(link["target"])
        links_by_id.setdefault(link["target"], set()).add(link["source"])

    created = []
    for note in data.get("nodes", []):
        note_id = note["id"]
        path = WIKI_DIR / f"{note_id}.md"
        if path.exists():
            print(f"Ignoré (wiki/{note_id}.md existe déjà) : fusionne les liens à la main si besoin")
            continue

        links = sorted(links_by_id.get(note_id, []))
        content = (
            "---\n"
            f"title: {note['title']}\n"
            f"group: {note['group']}\n"
            f"links: [{', '.join(links)}]\n"
            "---\n\n"
            f"{note['body']}\n"
        )
        path.write_text(content, encoding="utf-8")
        created.append(note_id)
        print(f"Créé : wiki/{note_id}.md")

    if created:
        print(f"\n{len(created)} note(s) importée(s). Relis-les, ajuste group/links/body si besoin, puis :")
        print("  python3 scripts/generate_graph.py")
    else:
        print("Rien à importer.")


if __name__ == "__main__":
    main()
