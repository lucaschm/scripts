import csv
import os
import shutil
import sys

DRY_RUN = False  # change to False when ready

CSV_FILE = "rename_suggestions.csv"
UNDO_LOG = "rename_undo.csv"


def load_csv():
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def check_collisions(rows):
    targets = set()

    for r in rows:
        src = r["original_path"]
        dst = os.path.join(os.path.dirname(src), r["suggested_name"])

        if dst in targets:
            raise RuntimeError(f"Collision detected: {dst}")

        if os.path.exists(dst) and src != dst:
            raise RuntimeError(f"Target already exists: {dst}")

        targets.add(dst)


def rename_files(rows):
    undo_rows = []

    for r in rows:
        src = r["original_path"]
        dst = os.path.join(os.path.dirname(src), r["suggested_name"])

        if src == dst:
            continue

        print(f"{src} -> {dst}")

        if not DRY_RUN:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)

        undo_rows.append([dst, src])

    return undo_rows


def write_undo_log(rows):
    if DRY_RUN:
        return

    with open(UNDO_LOG, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["current_path", "restore_path"])
        writer.writerows(rows)


def main():
    rows = load_csv()

    print(f"{len(rows)} rename operations loaded\n")

    check_collisions(rows)

    undo_rows = rename_files(rows)

    write_undo_log(undo_rows)

    if DRY_RUN:
        print("\nDRY RUN complete. No files renamed.")
        print("Set DRY_RUN = False when ready.")


if __name__ == "__main__":
    main()