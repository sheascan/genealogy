#!/usr/bin/env python3
import sys
import csv
import re
from collections import defaultdict
from gedcom_utils import parse_gedcom, resolve_path

def years_compatible(y1, y2, tolerance=3):
    if not y1 or not y2:
        return True
    try:
        return abs(int(y1) - int(y2)) <= tolerance
    except (ValueError, TypeError):
        return True

def names_compatible(n1, n2):
    if not n1 or not n2 or n1 == "Unknown" or n2 == "Unknown":
        return False
    s1 = re.sub(r'[^a-zA-Z]', '', n1).lower()
    s2 = re.sub(r'[^a-zA-Z]', '', n2).lower()
    if not s1 or not s2:
        return False
    return s1 == s2 or s1 in s2 or s2 in s1

def detect_duplicates(indis, fams):
    duplicates = []

    # 1. Sibling Duplicates: Same FAMC, compatible given names & birth years
    fam_to_children = defaultdict(list)
    for indi_id, data in indis.items():
        if data.get('famc'):
            fam_to_children[data['famc']].append(indi_id)

    for fam_id, children in fam_to_children.items():
        if len(children) < 2:
            continue
        n = len(children)
        for i in range(n):
            for j in range(i + 1, n):
                c1 = indis[children[i]]
                c2 = indis[children[j]]
                if names_compatible(c1.get('given'), c2.get('given')):
                    if years_compatible(c1.get('birth'), c2.get('birth')):
                        # Retain the more complete record as primary
                        score1 = sum([bool(c1.get('birth')), bool(c1.get('death')), len(c1.get('fams', []))])
                        score2 = sum([bool(c2.get('birth')), bool(c2.get('death')), len(c2.get('fams', []))])
                        primary, dup = (c1, c2) if score1 >= score2 else (c2, c1)

                        duplicates.append({
                            "Type": "DUPLICATE_SIBLING",
                            "Context_ID": fam_id,
                            "Primary_ID": primary['id'],
                            "Primary_Name": primary['name'],
                            "Primary_Birth": primary.get('birth', ''),
                            "Duplicate_ID": dup['id'],
                            "Duplicate_Name": dup['name'],
                            "Duplicate_Birth": dup.get('birth', ''),
                            "Recommendation": "QUARANTINE",
                            "Reason": "Same parents, compatible given name and birth year"
                        })

    # 2. Couple Duplicates: Redundant FAM records joining the same couple
    seen_couples = defaultdict(list)
    for fam_id, data in fams.items():
        h = data.get('husb')
        w = data.get('wife')
        if h and w:
            pair = tuple(sorted([h, w]))
            seen_couples[pair].append(fam_id)

    for pair, fam_list in seen_couples.items():
        if len(fam_list) > 1:
            h_data = indis.get(pair[0], {'name': pair[0], 'birth': ''})
            w_data = indis.get(pair[1], {'name': pair[1], 'birth': ''})
            label = f"{h_data['name']} & {w_data['name']}"
            canon_fam = fam_list[0]
            for dup_fam in fam_list[1:]:
                duplicates.append({
                    "Type": "DUPLICATE_COUPLE",
                    "Context_ID": f"{canon_fam} vs {dup_fam}",
                    "Primary_ID": pair[0],
                    "Primary_Name": label,
                    "Primary_Birth": h_data.get('birth', ''),
                    "Duplicate_ID": pair[1],
                    "Duplicate_Name": label,
                    "Duplicate_Birth": w_data.get('birth', ''),
                    "Recommendation": "QUARANTINE",
                    "Reason": f"Redundant FAM record between {canon_fam} and {dup_fam}"
                })

    return duplicates

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_detect_duplicates.py <file.ged>")
        sys.exit(1)

    ged_file = resolve_path(sys.argv[1])
    if not ged_file.exists():
        print(f"Error: {sys.argv[1]} not found.")
        sys.exit(1)

    print(f"[*] Parsing {ged_file} via gedcom_utils...")
    indis, fams = parse_gedcom(ged_file)
    print(f"[*] Parsed {len(indis)} individuals and {len(fams)} families.")

    print("[*] Detecting sibling and couple duplicate candidates...")
    dups = detect_duplicates(indis, fams)
    print(f"[+] Found {len(dups)} duplicate candidates.")

    out_csv = ged_file.parent / "duplicates_manifest.csv"
    fields = [
        "Type", "Context_ID", "Primary_ID", "Primary_Name", "Primary_Birth",
        "Duplicate_ID", "Duplicate_Name", "Duplicate_Birth", "Recommendation", "Reason"
    ]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(dups)

    print(f"[+] Manifest written to: {out_csv}")

if __name__ == '__main__':
    main()