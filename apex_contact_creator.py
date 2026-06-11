#!/usr/bin/env python3
"""
Apex Contact Creator
Converts a CSV file of contacts into a Carbyne-compatible JSON format.
"""

import csv
import json
import sys
import uuid
import argparse
from pathlib import Path

DEFAULT_ICON = "https://carbyne-resources.carbynenet.com/images/speed-dial-icons/default.png"

ICON_MAP = {
    "default": "https://carbyne-resources.carbynenet.com/images/speed-dial-icons/default.png",
    "police":  "https://carbyne-resources.carbynenet.com/images/speed-dial-icons/police.png",
    "911psap": "https://carbyne-resources.carbynenet.com/images/speed-dial-icons/911PSAP.png",
}


def resolve_icon(value: str) -> str:
    if not value:
        return DEFAULT_ICON
    key = value.strip().lower()
    return ICON_MAP.get(key, value.strip())


def build_phone_numbers(row: dict) -> str:
    """
    Supports up to 3 phone numbers per row via columns:
      PHONE_NUMBER_1, PHONE_LABEL_1, CONTACT_TYPE_1
      PHONE_NUMBER_2, PHONE_LABEL_2, CONTACT_TYPE_2
      PHONE_NUMBER_3, PHONE_LABEL_3, CONTACT_TYPE_3
    Falls back to single-number columns: PHONE_NUMBER, PHONE_LABEL, CONTACT_TYPE
    """
    entries = []

    def add(number, label, contact_type):
        if not number:
            return
        contact_type = (contact_type or "OTHER").strip().upper()
        entry = {"contactType": contact_type, "phoneNumber": number.strip(), "label": (label or "").strip()}
        entries.append(entry)

    # Multi-number columns
    for i in range(1, 4):
        num   = row.get(f"PHONE_NUMBER_{i}", "").strip()
        label = row.get(f"PHONE_LABEL_{i}", "").strip()
        ctype = row.get(f"CONTACT_TYPE_{i}", "").strip()
        add(num, label, ctype)

    # Single-number fallback
    if not entries:
        add(
            row.get("PHONE_NUMBER", ""),
            row.get("PHONE_LABEL", ""),
            row.get("CONTACT_TYPE", ""),
        )

    return json.dumps(entries)


def csv_to_json(csv_path: str, cnc_id: str) -> list:
    contacts = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("NAME", "").strip()
            if not name:
                continue

            notes = row.get("NOTES", "").strip()
            short_name = row.get("SPEED_DIAL_SHORT_NAME", "").strip()
            icon = resolve_icon(row.get("ICON", ""))
            disabled = int(row.get("DISABLED_TIMESTAMP", 0) or 0)

            contact = {
                "ID":                   str(uuid.uuid4()),
                "CNC_ID":               cnc_id,
                "NAME":                 name,
                "ICON":                 icon,
                "NOTES":                notes,
                "SPEED_DIAL_SHORT_NAME": short_name,
                "PHONE_NUMBERS":        build_phone_numbers(row),
                "DISABLED_TIMESTAMP":   disabled,
            }
            contacts.append(contact)

    return contacts


def main():
    parser = argparse.ArgumentParser(
        description="Convert a CSV file to Carbyne contact JSON."
    )
    parser.add_argument("csv_file", nargs="?", help="Path to input CSV file")
    parser.add_argument("--cnc-id", help="CNC ID for all contacts")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: stdout)")
    args = parser.parse_args()

    # Resolve CSV path
    csv_path = args.csv_file
    if not csv_path:
        csv_path = input("Enter path to CSV file: ").strip().strip('"')

    if not Path(csv_path).is_file():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # Resolve CNC ID
    cnc_id = args.cnc_id
    if not cnc_id:
        cnc_id = input("Enter CNC ID: ").strip()
    if not cnc_id:
        print("Error: CNC ID is required.", file=sys.stderr)
        sys.exit(1)

    contacts = csv_to_json(csv_path, cnc_id)

    output_json = json.dumps(contacts, indent="\t", ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Wrote {len(contacts)} contact(s) to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
