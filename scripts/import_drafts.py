#!/usr/bin/env python3
"""Importe un export de brouillons (le fichier mes-notes.json téléchargé via
le bouton "Exporter" du site) dans wiki/*.md.

Les images et fichiers joints (envoyés en base64 dans l'export) sont
décodés et écrits dans docs/files/, puisque seul le dossier docs/ est
publié par GitHub Pages.

Les notes officielles supprimées depuis le site (bouton "Supprimer" sur une
bulle qui n'est pas un brouillon) apparaissent dans data["deleted"] : leur
fichier wiki/<id>.md est alors supprimé pour de bon.

Usage : python3 scripts/import_drafts.py chemin/vers/mes-notes.json
"""
import base64
import json
import mimetypes
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"
FILES_DIR = ROOT / "docs" / "files"


def decode_data_uri(data_uri: str) -> bytes:
    _, b64data = data_uri.split(",", 1)
    return base64.b64decode(b64data)


def guess_ext(data_uri: str, fallback_name: str = "") -> str:
    mime = data_uri.split(";")[0].removeprefix("data:")
    ext = mimetypes.guess_extension(mime) or Path(fallback_name).suffix or ""
    return ".jpg" if ext == ".jpe" else ext


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
        extra_lines = []

        if note.get("link"):
            extra_lines.append(f"link: {note['link']}")

        if note.get("image"):
            ext = guess_ext(note["image"]) or ".jpg"
            FILES_DIR.mkdir(parents=True, exist_ok=True)
            rel_path = f"files/{note_id}{ext}"
            (ROOT / "docs" / rel_path).write_bytes(decode_data_uri(note["image"]))
            extra_lines.append(f"image: {rel_path}")

        if note.get("file"):
            file_name = note["file"].get("name", "fichier")
            ext = Path(file_name).suffix or guess_ext(note["file"]["url"])
            FILES_DIR.mkdir(parents=True, exist_ok=True)
            rel_path = f"files/{note_id}{ext}"
            (ROOT / "docs" / rel_path).write_bytes(decode_data_uri(note["file"]["url"]))
            extra_lines.append(f"file: {rel_path}")
            extra_lines.append(f"fileName: {file_name}")

        extra = ("\n".join(extra_lines) + "\n") if extra_lines else ""
        content = (
            "---\n"
            f"title: {note['title']}\n"
            f"group: {note['group']}\n"
            f"links: [{', '.join(links)}]\n"
            f"{extra}"
            "---\n\n"
            f"{note['body']}\n"
        )
        path.write_text(content, encoding="utf-8")
        created.append(note_id)
        print(f"Créé : wiki/{note_id}.md")

    removed = []
    for note_id in data.get("deleted", []):
        path = WIKI_DIR / f"{note_id}.md"
        if not path.exists():
            print(f"Ignoré (wiki/{note_id}.md n'existe déjà plus) : {note_id}")
            continue
        path.unlink()
        removed.append(note_id)
        print(f"Supprimé : wiki/{note_id}.md")

    if created or removed:
        print(f"\n{len(created)} note(s) importée(s), {len(removed)} supprimée(s).")
        print("Relis les notes créées, vérifie qu'aucune autre note ne référence encore")
        print("les id supprimés dans son champ links, puis :")
        print("  python3 scripts/generate_graph.py")
    else:
        print("Rien à importer.")


if __name__ == "__main__":
    main()
