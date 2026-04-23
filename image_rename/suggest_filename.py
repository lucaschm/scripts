import os
import re
import csv
from datetime import datetime
from collections import defaultdict
from PIL import Image, ExifTags
import pytz

CET = pytz.timezone("Europe/Berlin")

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".tiff", ".webp"}

# filename patterns
patterns = [
    ("datetime", re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)[-_ ]?([0-2]\d)([0-5]\d)([0-5]\d)")),
    ("date", re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)")),
]

# whatsapp pattern
wa_pattern = re.compile(r"IMG-(\d{8})-WA\d+", re.IGNORECASE)


def to_cet(dt):
    if dt.tzinfo is None:
        return CET.localize(dt)
    return dt.astimezone(CET)


def get_exif_datetime(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return None

        exif_data = {
            ExifTags.TAGS.get(k): v for k, v in exif.items() if k in ExifTags.TAGS
        }

        if "DateTimeOriginal" in exif_data:
            dt = datetime.strptime(exif_data["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")
            return to_cet(dt), "exif_datetimeoriginal"

    except Exception:
        pass

    return None, None


def parse_filename_datetime(name):
    # WhatsApp special case
    wa_match = wa_pattern.search(name)
    if wa_match:
        d = wa_match.group(1)
        dt = datetime.strptime(d, "%Y%m%d")
        return to_cet(dt), "filename_whatsapp", True

    # datetime patterns
    for label, pattern in patterns:
        m = pattern.search(name)
        if m:
            parts = list(map(int, m.groups()))

            if label == "datetime":
                y, mo, d, h, mi, s = parts
                dt = datetime(y, mo, d, h, mi, s)
                return to_cet(dt), "filename_datetime", False

            if label == "date":
                y, mo, d = parts
                dt = datetime(y, mo, d)
                return to_cet(dt), "filename_date", False

    return None, None, False


def filesystem_datetime(path):
    ts = os.path.getmtime(path)
    dt = datetime.fromtimestamp(ts, CET)
    return dt, "filesystem_mtime"


def determine_datetime(path):
    name = os.path.basename(path)

    # priority 1 filename
    dt, src, wa = parse_filename_datetime(name)
    if dt:
        return dt, src, wa

    # priority 2 exif
    dt, src = get_exif_datetime(path)
    if dt:
        return dt, src, False

    # priority 3 filesystem
    dt, src = filesystem_datetime(path)
    return dt, src, False


def find_images(root):
    for dirpath, _, filenames in os.walk(root):
        for f in sorted(filenames):
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXT:
                yield os.path.join(dirpath, f)


def main(root):
    records = []

    for order, path in enumerate(find_images(root)):
        dt, source, is_wa = determine_datetime(path)
        records.append(
            {
                "path": path,
                "datetime": dt,
                "date": dt.date(),
                "time": dt.time(),
                "source": source,
                "is_wa": is_wa,
                "order": order,
            }
        )

    grouped = defaultdict(list)
    for r in records:
        grouped[r["date"]].append(r)

    suggestions = []

    for date in sorted(grouped):
        items = sorted(grouped[date], key=lambda x: (x["datetime"], x["order"]))

        for idx, r in enumerate(items, 1):
            ext = os.path.splitext(r["path"])[1].lower()

            suffix = "_wa" if r["is_wa"] else ""
            newname = f"{date.strftime('%Y-%m-%d')}_{idx:02d}{suffix}{ext}"

            suggestions.append(
                [
                    r["path"],
                    newname,
                    r["source"],
                    r["time"].isoformat(),
                    r["is_wa"],
                ]
            )

    with open(f"{root}/rename_suggestions.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "original_path",
                "suggested_name",
                "date_source",
                "time_used",
                "is_whatsapp",
            ]
        )

        writer.writerows(suggestions)


if __name__ == "__main__":
    root = input("Folder with images: ")
    main(root)