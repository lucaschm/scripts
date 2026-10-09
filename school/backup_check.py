"""
Prüft, ob im letzten Backup-Ordner eines Backup-Tages alle Dateien vorhanden sind,
die in früheren Backup-Ordnern desselben Tages existierten.
"""

import os
import sys
from collections import defaultdict


def list_files(root):
    """Gibt alle Dateien unterhalb von root als Menge relativer Pfade zurück."""
    files = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            files.add(os.path.relpath(full, root))
    return files


def main():
    day_path = input("Pfad zum Backup-Tag: ").strip().strip('"').strip("'")
    day_path = os.path.abspath(os.path.expanduser(day_path))

    if not os.path.isdir(day_path):
        print(f"Fehler: '{day_path}' ist kein gültiges Verzeichnis.")
        sys.exit(1)

    # Uhrzeitordner (nur Verzeichnisse), alphabetisch = chronologisch sortiert
    backups = sorted(
        d for d in os.listdir(day_path)
        if os.path.isdir(os.path.join(day_path, d))
    )

    if len(backups) < 2:
        print("Es sind weniger als zwei Backup-Ordner vorhanden. Es gibt nichts zu vergleichen.")
        sys.exit(0)

    last = backups[-1]
    earlier = backups[:-1]
    print(f"\nBackup-Tag:      {day_path}")
    print(f"Backup-Ordner:   {len(backups)} ({backups[0]} ... {last})")
    print(f"Letzter Ordner:  {last}\n")

    # Dateien des letzten Ordners
    last_files = list_files(os.path.join(day_path, last))

    # Für jede Datei merken, in welchen früheren Ordnern sie vorhanden war
    seen_in = defaultdict(list)
    for folder in earlier:
        for rel in list_files(os.path.join(day_path, folder)):
            seen_in[rel].append(folder)

    # Dateien, die früher existierten, aber im letzten Ordner fehlen
    missing = sorted(rel for rel in seen_in if rel not in last_files)

    if not missing:
        print("Alles in Ordnung: Alle Dateien aus früheren Backups sind auch in "
              f"'{last}' vorhanden.")
        return

    print(f"ACHTUNG: {len(missing)} Datei(en) fehlen in '{last}':\n")
    for rel in missing:
        folders = seen_in[rel]
        print(f"  - {rel}")
        print(f"      vorhanden in: {folders[0]} ... {folders[-1]} "
              f"({len(folders)} Backup(s))")

    sys.exit(2)


if __name__ == "__main__":
    main()