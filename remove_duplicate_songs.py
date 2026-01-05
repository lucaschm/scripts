import os
import re
import shutil
from mutagen import File

# ================= CONFIG =================
MUSIC_DIR = r"/home/mint/Desktop/Monstercat/catalog"
REMOVED_DIR = r"/home/mint/Desktop/Monstercat/catalog_duplicates"
DRY_RUN = False   # <-- set False to actually move files
# ==========================================

os.makedirs(REMOVED_DIR, exist_ok=True)

DUPLICATE_PATTERN = re.compile(r"\s*\(\d+\)\s*$")
PAREN_CONTENT_PATTERN = re.compile(r"\s*\([^)]*\)")

def base_filename(filename):
    """Lowercased filename without (1), (2), extension"""
    name, _ = os.path.splitext(filename)
    name = DUPLICATE_PATTERN.sub("", name)
    return name.lower().strip()

def extract_title(filename):
    """
    Extract title from:
    Artist - Title (feat. X)
    """
    name = base_filename(filename)
    if " - " in name:
        return name.split(" - ", 1)[1].strip()
    return name

def title_variants(title):
    """
    Return:
    - title as-is
    - title without parenthesis content
    """
    no_paren = PAREN_CONTENT_PATTERN.sub("", title).strip()
    return {title, no_paren}

def get_album(filepath):
    audio = File(filepath, easy=True)
    if not audio:
        return None
    return audio.get("album", [None])[0].lower()

songs = {}
failures = []

# ---------- STEP 1: Scan files ----------
for root, _, files in os.walk(MUSIC_DIR):
    for file in files:
        if not file.lower().endswith((".mp3", ".flac", ".wav", ".m4a")):
            continue

        path = os.path.join(root, file)
        album = get_album(path)
        if not album:
            print(f"Missing metadata for {file}")
            continue

        key = base_filename(file)

        songs.setdefault(key, []).append({
            "path": path,
            "file": file,
            "album": album,
            "title_variants": title_variants(extract_title(file))
        })

# ---------- STEP 2: Resolve duplicates ----------
for key, versions in songs.items():
    if len(versions) < 2:
        continue

    singles = []
    albums = []

    for v in versions:
        if v["album"] in v["title_variants"]:
            singles.append(v)
        else:
            albums.append(v)

    # Edge case: ambiguous single vs album
    if singles and albums and any(a["album"] in s["title_variants"] for s in singles for a in albums):
        failures.append({
            "song": key,
            "files": [v["path"] for v in versions]
        })
        continue

    normal_albums = [
        a for a in albums
        if "remix" not in a["album"] and "vip" not in a["album"]
    ]

    if normal_albums:
        keep = normal_albums[0]
    elif singles:
        keep = singles[0]
    else:
        continue

    for v in versions:
        if v is keep:
            continue

        dest = os.path.join(REMOVED_DIR, os.path.basename(v["path"]))

        if DRY_RUN:
            print(f"[DRY-RUN] Would move: {v['path']} → {dest}")
        else:
            print(f"Moving: {v['path']} → {dest}")
            shutil.move(v["path"], dest)

# ---------- STEP 3: Print failures ----------
if failures:
    print("\n=== FAILURE LIST ===")
    for f in failures:
        print(f"\nSong key: {f['song']}")
        for file in f["files"]:
            print(f"  - {file}")

print("\nDone.")
