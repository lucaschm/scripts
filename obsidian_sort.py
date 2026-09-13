#!/usr/bin/env python3
"""
Obsidian Notizen Sortier-Tool
==============================

Sortiert Notizen aus einem flachen Obsidian-Ordner (keine Unterordner)
anhand von Tags im YAML-Frontmatter in Unterordner.

Voraussetzung:
    pip install pyyaml

Verwendung:

  1) Analyse-Modus
     python obsidian_sort.py analyse --ordner /pfad/zu/notizen \
         --include tag1,tag2 --exclude tag3

  2) Verschieben-Modus
     python obsidian_sort.py verschieben --ordner /pfad/zu/notizen \
         --include tag1,tag2 --exclude tag3 --ziel "Projekt A"

Hinweise:
  - --include und --exclude sind optional. Ohne --include werden
    zunächst alle Notizen berücksichtigt (nur --exclude filtert dann).
  - --include wirkt als ODER-Verknüpfung: eine Notiz wird berücksichtigt,
    wenn sie MINDESTENS EINEN der angegebenen Tags besitzt.
  - --exclude schließt eine Notiz aus, sobald sie EINEN der angegebenen
    Tags besitzt.
  - Im Verschieben-Modus wird vor dem eigentlichen Verschieben eine
    Liste der betroffenen Dateien angezeigt und um Bestätigung gebeten
    (außer bei --yes).
"""

import argparse
import re
import sys
import shutil
from pathlib import Path
from collections import Counter

try:
    import yaml
except ImportError:
    print("Das Paket 'pyyaml' wird benötigt. Installieren mit: pip install pyyaml")
    sys.exit(1)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?", re.DOTALL)


def read_frontmatter(path: Path) -> dict:
    """Liest den YAML-Frontmatter-Block einer Markdown-Datei aus."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    return data or {}


def normalize_tags(raw_tags) -> list:
    """Wandelt das tags-Feld (String, Liste, kommagetrennt, #tag) in eine saubere Liste um."""
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        parts = [t.strip() for t in raw_tags.split(",")]
    elif isinstance(raw_tags, list):
        parts = [str(t).strip() for t in raw_tags]
    else:
        parts = [str(raw_tags).strip()]

    cleaned = []
    for t in parts:
        t = t.lstrip("#").strip()
        if t:
            cleaned.append(t)
    return cleaned


def load_notes(folder: Path) -> list:
    """Liest alle .md-Dateien im Ordner (keine Unterordner) und gibt (Pfad, Tags) zurück."""
    notes = []
    for path in sorted(folder.glob("*.md")):
        if path.is_file():
            fm = read_frontmatter(path)
            tags = normalize_tags(fm.get("tags"))
            notes.append((path, tags))
    return notes


def filter_notes(notes: list, include: list, exclude: list) -> list:
    include_set = set(include)
    exclude_set = set(exclude)
    result = []
    for path, tags in notes:
        tag_set = set(tags)
        if include_set and not (tag_set & include_set):
            continue
        if exclude_set and (tag_set & exclude_set):
            continue
        result.append((path, tags))
    return result


def parse_tag_list(arg: str) -> list:
    if not arg:
        return []
    return [t.strip().lstrip("#") for t in arg.split(",") if t.strip()]


def cmd_analyse(args):
    folder = Path(args.ordner).expanduser().resolve()
    if not folder.is_dir():
        print(f"Ordner nicht gefunden: {folder}")
        sys.exit(1)

    include = parse_tag_list(args.include)
    exclude = parse_tag_list(args.exclude)

    notes = load_notes(folder)
    print(f"Gefundene Notizen insgesamt: {len(notes)}")

    filtered = filter_notes(notes, include, exclude)
    print(f"Notizen nach Filter (include={include or '-'}, exclude={exclude or '-'}): {len(filtered)}")
    print()

    if not filtered:
        print("Keine Notizen entsprechen den Filterkriterien.")
        return

    tag_counter = Counter()
    untagged = 0
    for _, tags in filtered:
        if not tags:
            untagged += 1
        for t in tags:
            tag_counter[t] += 1

    print("Tag-Übersicht in den gefilterten Notizen:")
    print("-" * 40)
    for tag, count in sorted(tag_counter.items(), key=lambda x: (-x[1], x[0].lower())):
        print(f"  {tag:<30} {count}")
    if untagged:
        print(f"  {'(ohne Tags)':<30} {untagged}")
    print("-" * 40)

    if args.list_files:
        print()
        print("Betroffene Dateien:")
        for path, tags in filtered:
            tag_str = ", ".join(tags) if tags else "-"
            print(f"  {path.name}  [{tag_str}]")


def cmd_verschieben(args):
    folder = Path(args.ordner).expanduser().resolve()
    if not folder.is_dir():
        print(f"Ordner nicht gefunden: {folder}")
        sys.exit(1)

    include = parse_tag_list(args.include)
    exclude = parse_tag_list(args.exclude)

    notes = load_notes(folder)
    filtered = filter_notes(notes, include, exclude)

    if not filtered:
        print("Keine Notizen entsprechen den Filterkriterien. Es wird nichts verschoben.")
        return

    ziel = folder / args.ziel
    ziel.mkdir(parents=True, exist_ok=True)

    print(f"{len(filtered)} Notiz(en) werden nach '{ziel}' verschoben:")
    for path, tags in filtered:
        tag_str = ", ".join(tags) if tags else "-"
        print(f"  {path.name}  [{tag_str}]")

    if not args.yes:
        antwort = input("\nFortfahren? [j/N] ").strip().lower()
        if antwort not in ("j", "ja", "y", "yes"):
            print("Abgebrochen.")
            return

    verschoben = 0
    fehler = 0
    for path, _ in filtered:
        ziel_pfad = ziel / path.name
        if ziel_pfad.exists():
            print(f"  Übersprungen (existiert bereits im Ziel): {path.name}")
            fehler += 1
            continue
        try:
            shutil.move(str(path), str(ziel_pfad))
            verschoben += 1
        except Exception as e:
            print(f"  Fehler bei {path.name}: {e}")
            fehler += 1

    print(f"\nFertig. {verschoben} Datei(en) verschoben, {fehler} übersprungen/fehlgeschlagen.")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Sortiert Obsidian-Notizen anhand von YAML-Tags in Unterordner."
    )
    sub = parser.add_subparsers(dest="modus", required=True)

    p_analyse = sub.add_parser("analyse", help="Tags in gefilterten Notizen analysieren")
    p_analyse.add_argument("--ordner", required=True, help="Pfad zum Notizen-Ordner")
    p_analyse.add_argument("--include", default="", help="Kommagetrennte Tags, die enthalten sein müssen (ODER-Verknüpfung)")
    p_analyse.add_argument("--exclude", default="", help="Kommagetrennte Tags, die NICHT enthalten sein dürfen")
    p_analyse.add_argument("--list-files", action="store_true", help="Zusätzlich alle betroffenen Dateien auflisten")
    p_analyse.set_defaults(func=cmd_analyse)

    p_move = sub.add_parser("verschieben", help="Gefilterte Notizen in einen Unterordner verschieben")
    p_move.add_argument("--ordner", required=True, help="Pfad zum Notizen-Ordner")
    p_move.add_argument("--include", default="", help="Kommagetrennte Tags, die enthalten sein müssen (ODER-Verknüpfung)")
    p_move.add_argument("--exclude", default="", help="Kommagetrennte Tags, die NICHT enthalten sein dürfen")
    p_move.add_argument("--ziel", required=True, help="Name des Zielunterordners (wird im Notizen-Ordner angelegt)")
    p_move.add_argument("--yes", action="store_true", help="Ohne Rückfrage verschieben")
    p_move.set_defaults(func=cmd_verschieben)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()