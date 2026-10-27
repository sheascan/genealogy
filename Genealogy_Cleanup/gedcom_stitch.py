#!/usr/bin/env python3
import sys
import csv
from datetime import datetime
from gedcom_utils import load_gedcom_raw_records, resolve_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_stitch.py <BRANCH_ID> [clean_file.ged] [quarantine_file.ged] [catalog.csv]")
        sys.exit(1)

    target_branch = sys.argv[1].strip().upper()
    clean_file = resolve_path(sys.argv[2] if len(sys.argv) > 2 else "mcconigley_final_clean.ged")
    quarantine_file = resolve_path(sys.argv[3] if len(sys.argv) > 3 else "mcconigley_quarantine.ged")
    catalog_file = resolve_path(sys.argv[4] if len(sys.argv) > 4 else "quarantine_catalog.csv")

    target_row = None
    with open(catalog_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['Branch_ID'].strip().upper() == target_branch:
                target_row = row
                break

    if not target_row:
        print(f"[-] Error: {target_branch} not found in {catalog_file}.")
        sys.exit(1)

    member_ids = set(target_row['Subtree_Members'].split())
    primary_anchor = target_row['Primary_Anchor'].strip()
    dup_root = target_row['Quarantined_Root'].strip()
    branch_type = target_row['Type']

    print(f"[*] Found {target_branch}: {target_row['Root_Name']}")
    clean_hdr, clean_recs, _ = load_gedcom_raw_records(clean_file)
    _, guar_recs, _ = load_gedcom_raw_records(quarantine_file)

    restored_recs = {mid: list(guar_recs[mid]) for mid in member_ids if mid in guar_recs}
    for rid, lines in guar_recs.items():
        if len(lines) > 0 and lines[0].split()[2] == 'FAM':
            husb = any(l.startswith('1 HUSB ') and l[7:].strip() in member_ids for l in lines)
            wife = any(l.startswith('1 WIFE ') and l[7:].strip() in member_ids for l in lines)
            if husb or wife:
                restored_recs[rid] = list(lines)

    if branch_type == "DUPLICATE_SIBLING":
        famc_id = None
        if primary_anchor in clean_recs:
            for l in clean_recs[primary_anchor]:
                if l.startswith('1 FAMC '):
                    famc_id = l[7:].strip()
                    break
        if famc_id and famc_id in clean_recs:
            clean_recs[famc_id].append(f"1 CHIL {dup_root}\n")
            if dup_root in restored_recs and not any(l.startswith('1 FAMC ') for l in restored_recs[dup_root]):
                restored_recs[dup_root].append(f"1 FAMC {famc_id}\n")
            print(f"[+] Re-linked sibling {dup_root} into family {famc_id}.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = clean_file.parent
    out_file = out_dir / f"mcconigley_restored_{target_branch}_{timestamp}.ged"

    with open(out_file, 'w', encoding='utf-8') as f:
        f.writelines(clean_hdr)
        for lines in clean_recs.values():
            f.writelines(lines)
        for lines in restored_recs.values():
            f.writelines(lines)
        f.write("0 TRLR\n")

    print(f"[+] Success! Restored {len(restored_recs)} records to {out_file}")

if __name__ == '__main__':
    main()