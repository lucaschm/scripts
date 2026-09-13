#!/usr/bin/env python3
"""
Obsidian Note Sorter
=====================

Sorts notes from a flat Obsidian folder (no subfolders) into subfolders
based on tags in the YAML frontmatter.

Requirement:
    pip install pyyaml

Usage:

  1) Analyze mode
     python obsidian_sort.py analyze --folder /path/to/notes \
         --include tag1,tag2 --exclude tag3

  2) Move mode
     python obsidian_sort.py move --folder /path/to/notes \
         --include tag1,tag2 --exclude tag3 --target "Project A"

Notes:
  - --include and --exclude are both optional. Without --include, all
    notes are considered first (only --exclude then filters them out).
  - --include works as an OR condition: a note is included if it has
    AT LEAST ONE of the given tags.
  - --exclude removes a note as soon as it has ANY of the given tags.
  - Hierarchical tags: tags may be structured with '/', e.g. "abc/1"
    and "abc/2" both belong to the parent tag "abc". By default,
    including/excluding "abc" also matches "abc/1", "abc/2", etc.
    Use --no-hierarchy to disable this and match tags exactly instead.
  - In move mode, the list of affected files is shown and confirmation
    is requested before anything is moved (unless --yes is given).
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
    print("The 'pyyaml' package is required. Install it with: pip install pyyaml")
    sys.exit(1)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?", re.DOTALL)


def read_frontmatter(path: Path) -> dict:
    """Reads the YAML frontmatter block of a markdown file."""
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
    """Turns the tags field (string, list, comma-separated, #tag) into a clean list."""
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
    """Reads all .md files in the folder (no subfolders) and returns (path, tags) pairs."""
    notes = []
    for path in sorted(folder.glob("*.md")):
        if path.is_file():
            fm = read_frontmatter(path)
            tags = normalize_tags(fm.get("tags"))
            notes.append((path, tags))
    return notes


def tag_matches(note_tag: str, filter_tag: str, hierarchical: bool) -> bool:
    """Checks whether a note's tag matches a filter tag.

    With hierarchical matching enabled, a filter tag also matches any of
    its children, e.g. filter tag "abc" matches note tags "abc", "abc/1",
    "abc/2/x", etc. Without it, only an exact match counts.
    """
    if note_tag == filter_tag:
        return True
    if hierarchical and note_tag.startswith(filter_tag + "/"):
        return True
    return False


def any_tag_matches(note_tags: list, filter_tags: set, hierarchical: bool) -> bool:
    return any(
        tag_matches(note_tag, filter_tag, hierarchical)
        for note_tag in note_tags
        for filter_tag in filter_tags
    )


def filter_notes(notes: list, include: list, exclude: list, hierarchical: bool) -> list:
    include_set = set(include)
    exclude_set = set(exclude)
    result = []
    for path, tags in notes:
        if include_set and not any_tag_matches(tags, include_set, hierarchical):
            continue
        if exclude_set and any_tag_matches(tags, exclude_set, hierarchical):
            continue
        result.append((path, tags))
    return result


def parse_tag_list(arg: str) -> list:
    if not arg:
        return []
    return [t.strip().lstrip("#") for t in arg.split(",") if t.strip()]


def cmd_analyze(args):
    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    include = parse_tag_list(args.include)
    exclude = parse_tag_list(args.exclude)
    hierarchical = not args.no_hierarchy

    notes = load_notes(folder)
    print(f"Total notes found: {len(notes)}")

    filtered = filter_notes(notes, include, exclude, hierarchical)
    print(
        f"Notes after filter (include={include or '-'}, exclude={exclude or '-'}, "
        f"hierarchical={hierarchical}): {len(filtered)}"
    )
    print()

    if not filtered:
        print("No notes match the filter criteria.")
        return

    tag_counter = Counter()
    untagged = 0
    for _, tags in filtered:
        if not tags:
            untagged += 1
        for t in tags:
            tag_counter[t] += 1

    print("Tag overview in the filtered notes:")
    print("-" * 40)
    for tag, count in sorted(tag_counter.items(), key=lambda x: (-x[1], x[0].lower())):
        print(f"  {tag:<30} {count}")
    if untagged:
        print(f"  {'(no tags)':<30} {untagged}")
    print("-" * 40)

    if args.list_files:
        print()
        print("Affected files:")
        for path, tags in filtered:
            tag_str = ", ".join(tags) if tags else "-"
            print(f"  {path.name}  [{tag_str}]")


def cmd_move(args):
    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    include = parse_tag_list(args.include)
    exclude = parse_tag_list(args.exclude)
    hierarchical = not args.no_hierarchy

    notes = load_notes(folder)
    filtered = filter_notes(notes, include, exclude, hierarchical)

    if not filtered:
        print("No notes match the filter criteria. Nothing will be moved.")
        return

    target = folder / args.target
    target.mkdir(parents=True, exist_ok=True)

    print(f"{len(filtered)} note(s) will be moved to '{target}':")
    for path, tags in filtered:
        tag_str = ", ".join(tags) if tags else "-"
        print(f"  {path.name}  [{tag_str}]")

    if not args.yes:
        answer = input("\nProceed? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Cancelled.")
            return

    moved = 0
    skipped = 0
    for path, _ in filtered:
        target_path = target / path.name
        if target_path.exists():
            print(f"  Skipped (already exists in target): {path.name}")
            skipped += 1
            continue
        try:
            shutil.move(str(path), str(target_path))
            moved += 1
        except Exception as e:
            print(f"  Error moving {path.name}: {e}")
            skipped += 1

    print(f"\nDone. {moved} file(s) moved, {skipped} skipped/failed.")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Sorts Obsidian notes into subfolders based on YAML tags."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_analyze = sub.add_parser("analyze", help="Analyze tags in the filtered notes")
    p_analyze.add_argument("--folder", required=True, help="Path to the notes folder")
    p_analyze.add_argument("--include", default="", help="Comma-separated tags a note must have at least one of (OR)")
    p_analyze.add_argument("--exclude", default="", help="Comma-separated tags a note must NOT have")
    p_analyze.add_argument("--no-hierarchy", action="store_true", help="Disable hierarchical tag matching ('abc' no longer matches 'abc/1')")
    p_analyze.add_argument("--list-files", action="store_true", help="Also list all affected files")
    p_analyze.set_defaults(func=cmd_analyze)

    p_move = sub.add_parser("move", help="Move the filtered notes into a subfolder")
    p_move.add_argument("--folder", required=True, help="Path to the notes folder")
    p_move.add_argument("--include", default="", help="Comma-separated tags a note must have at least one of (OR)")
    p_move.add_argument("--exclude", default="", help="Comma-separated tags a note must NOT have")
    p_move.add_argument("--no-hierarchy", action="store_true", help="Disable hierarchical tag matching ('abc' no longer matches 'abc/1')")
    p_move.add_argument("--target", required=True, help="Name of the target subfolder (created inside the notes folder)")
    p_move.add_argument("--yes", action="store_true", help="Move without confirmation prompt")
    p_move.set_defaults(func=cmd_move)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()