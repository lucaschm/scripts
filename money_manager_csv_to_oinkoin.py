#!/usr/bin/env python3
"""
Fuegt Zeilen aus einer CSV-Datei als Records in ein Oinkoin-Backup (JSON) ein.

Aufruf:
    python csv_to_oinkoin.py alt.csv backup.json backup_neu.json

Die Original-JSON wird nicht veraendert, das Ergebnis geht in die Ausgabedatei.
"""
import argparse
import csv
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_NAME = "Europe/Berlin"
TZ = ZoneInfo(TZ_NAME)
# Unterstuetzte Datumsformate; ohne Uhrzeit wird 00:00:00 verwendet
DATE_FORMATS = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y")


def parse_date(text: str) -> datetime:
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    raise ValueError(f"Datum '{text}' passt zu keinem der Formate {DATE_FORMATS}")


def parse_amount(text: str) -> float:
    text = text.strip().replace(" ", "")
    if "," in text and "." in text:  # 1.234,56 -> 1234.56
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    return float(text)


def detect_unit_factor(records: list) -> int:
    """Oinkoin speichert 'datetime' normalerweise in Millisekunden.
    Das wird anhand der vorhandenen Records erkannt (Fallback: Millisekunden)."""
    for rec in records:
        dt = rec.get("datetime")
        if isinstance(dt, (int, float)):
            return 1000 if dt > 1e11 else 1
    return 1000


def read_csv(path: str) -> list:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for line_no, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue  # Leerzeile
            try:
                dt = parse_date(row["Datum"])
                amount = parse_amount(row["EUR"])
                kind = row["Einnahmen/Ausgaben"].strip()
                if kind == "Ausgabe":
                    category_type, value = 0, -amount
                elif kind == "Einkommen":
                    category_type, value = 1, amount
                else:
                    raise ValueError(f"Unbekannter Typ '{kind}'")
                rows.append({
                    "dt": dt,
                    "title": row["title"],
                    "value": round(value, 2),
                    "category_name": row["category_name"],
                    "category_type": category_type,
                    "description": row["description"],
                    "wallet_id": int(row["wallet_id"]),
                })
            except (KeyError, ValueError) as e:
                sys.exit(f"Fehler in CSV-Zeile {line_no}: {e}")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    parser.add_argument("json_in")
    parser.add_argument("json_out")
    args = parser.parse_args()

    with open(args.json_in, encoding="utf-8") as f:
        data = json.load(f)

    old_records = data["records"]
    rows = read_csv(args.csv_file)
    n = len(rows)

    # CSV ist absteigend sortiert -> umdrehen, dann (stabil) nach Datum sortieren.
    # Aeltester Eintrag bekommt ID 1.
    rows.reverse()
    rows.sort(key=lambda r: r["dt"])

    factor = detect_unit_factor(old_records)

    new_records = []
    for i, r in enumerate(rows, start=1):
        new_records.append({
            "id": i,
            "title": r["title"],
            "value": r["value"],
            "datetime": int(r["dt"].timestamp() * factor),
            "timezone": TZ_NAME,
            "category_name": r["category_name"],
            "category_type": r["category_type"],
            "description": r["description"],
            "recurrence_id": None,
            "wallet_id": r["wallet_id"],
            "transfer_wallet_id": None,
            "transfer_value": None,
            "profile_id": 1,
        })

    # Alte IDs nach Reihenfolge auf n+1, n+2, ... abbilden (relative Reihenfolge bleibt)
    old_ids_sorted = sorted(rec["id"] for rec in old_records)
    id_map = {old: n + idx for idx, old in enumerate(old_ids_sorted, start=1)}

    for rec in old_records:
        rec["id"] = id_map[rec["id"]]

    for assoc in data.get("record_tag_associations", []):
        old = assoc["record_id"]
        if old in id_map:
            assoc["record_id"] = id_map[old]
        else:
            print(f"Warnung: Tag-Zuordnung verweist auf unbekannte record_id {old}")

    data["records"] = old_records + new_records

    # Plausibilitaetspruefungen
    known_cats = {(c.get("name"), c.get("category_type")) for c in data.get("categories", [])}
    known_wallets = {w["id"] for w in data.get("wallets", [])}
    missing_cats = {(r["category_name"], r["category_type"]) for r in new_records} - known_cats
    for name, ctype in sorted(missing_cats):
        print(f"Warnung: Kategorie '{name}' (category_type {ctype}) existiert nicht in der JSON")
    for wid in sorted({r["wallet_id"] for r in new_records} - known_wallets):
        print(f"Warnung: wallet_id {wid} existiert nicht in der JSON")

    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"{n} CSV-Zeilen importiert (IDs 1-{n}), "
          f"{len(old_records)} bestehende Records verschoben (IDs {n + 1}-{n + len(old_records)}).")
    print(f"Zeitstempel in {'Millisekunden' if factor == 1000 else 'Sekunden'}. Ausgabe: {args.json_out}")


if __name__ == "__main__":
    main()