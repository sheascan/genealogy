#!/usr/bin/env python3
import csv
import gzip
import sys
import xml.etree.ElementTree as ET
from collections import Counter


def dump_surnames(gramps_file, output_csv="surnames_audit.csv"):
    print(f"Reading {gramps_file}...")
    with gzip.open(gramps_file, "rb") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    # Handle Gramps XML namespace
    ns = {"g": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    prefix = f"{{{ns['g']}}}" if ns else ""

    surname_elements = root.findall(f".//{prefix}surname")
    counts = Counter(
        el.text.strip() for el in surname_elements if el.text and el.text.strip()
    )

    # 1. Print sorted list to terminal
    print(f"\nFound {len(counts)} unique surnames across {sum(counts.values())} instances.\n")
    print(f"{'Count':<8} | {'Surname'}")
    print("-" * 35)
    for name, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"{count:<8} | {name}")

    # 2. Write CSV pre-formatted for your cleanup mapping
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Original_Surname", "Count", "Target_Surname", "Action_Flag"])
        for name, count in sorted(counts.items(), key=lambda x: x[0].lower()):
            # By default Target = Original; you change Target and set Action_Flag to 'RENAME'
            writer.writerow([name, count, name, "KEEP"])

    print(f"\nSaved editable mapping template to: {output_csv}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dump_surnames.py my_export.gramps [output.csv]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else "surnames_audit.csv"
    dump_surnames(sys.argv[1], out)