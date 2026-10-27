#!/usr/bin/env python3
import csv
import gzip
import html
import sys
import xml.etree.ElementTree as ET
from collections import Counter


def apply_surname_corrections(
    gramps_in, csv_corrections, gramps_out="revised.gramps"
):
    # 1. Load mappings from CSV
    rename_map = {}
    with open(csv_corrections, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            flag = row.get("Action_Flag", "").strip().upper()
            if flag == "RENAME":
                orig = html.unescape(row["Original_Surname"].strip())
                target = html.unescape(row["Target_Surname"].strip())
                if orig != target:
                    rename_map[orig] = target

    print(
        f"Loaded {len(rename_map)} distinct rename rules from {csv_corrections}.\n"
    )

    # 2. Decompress and parse the Gramps XML
    print(f"Reading and decompressing {gramps_in}...")
    with gzip.open(gramps_in, "rb") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    # Detect XML namespace
    ns = {"g": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    prefix = f"{{{ns['g']}}}" if ns else ""

    # 3. Apply substitutions
    replaced_counts = Counter()
    total_modifications = 0

    for el in root.findall(f".//{prefix}surname"):
        if el.text:
            cleaned_text = el.text.strip()
            if cleaned_text in rename_map:
                target_text = rename_map[cleaned_text]
                replaced_counts[(cleaned_text, target_text)] += 1
                el.text = target_text
                total_modifications += 1

    # 4. Report results
    print("\n--- Summary of Replacements Applied ---")
    if not replaced_counts:
        print("No matching surnames found to replace.")
    else:
        for (orig, targ), count in sorted(
            replaced_counts.items(), key=lambda x: -x[1]
        ):
            print(f"  '{orig}' -> '{targ}': {count} instance(s)")

    print(f"\nTotal surname records updated: {total_modifications}")

    # 5. Write gzipped output
    print(f"\nWriting cleaned package to {gramps_out}...")
    with gzip.open(gramps_out, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

    print(f"Success. Output saved to {gramps_out}")


if __name__ == "__main__":
    src_gramps = sys.argv[1] if len(sys.argv) > 1 else "export.gramps"
    src_csv = (
        sys.argv[2] if len(sys.argv) > 2 else "surnames_Corrections.csv"
    )
    dest_gramps = sys.argv[3] if len(sys.argv) > 3 else "revised.gramps"

    apply_surname_corrections(src_gramps, src_csv, dest_gramps)