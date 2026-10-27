#!/usr/bin/env python3
import sys
import csv
from gedcom_utils import load_gedcom_raw_records, resolve_path

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gedcom_prune_branches.py <canonical.ged> <branches_to_cull.csv>")
        sys.exit(1)

    ged_file = resolve_path(sys.argv[1])
    csv_file = resolve_path(sys.argv[2])
    out_dir = ged_file.parent

    header, records, trailer = load_gedcom_raw_records(ged_file)

    prune_ids = set()
    with open(csv_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('Cull_Decision', '').strip().upper() == 'PRUNE':
                prune_ids.add(row['ID'].strip())

    print(f"[*] Pruning {len(prune_ids)} profiles...")
    prune_fams = set()
    canonical_records = {}

    for rid, lines in records.items():
        tag = lines[0].split()[2] if len(lines[0].split()) > 2 else ''
        if rid in prune_ids:
            continue
            
        if tag == 'FAM':
            husb, wife, children = None, None, []
            for l in lines:
                if l.startswith('1 HUSB '): husb = l[7:].strip()
                elif l.startswith('1 WIFE '): wife = l[7:].strip()
                elif l.startswith('1 CHIL '): children.append(l[7:].strip())
            
            spouses = [s for s in [husb, wife] if s]
            if spouses and all(s in prune_ids for s in spouses):
                prune_fams.add(rid)
                continue
                
            cleaned = [l for l in lines if not (
                (l.startswith('1 HUSB ') and husb in prune_ids) or
                (l.startswith('1 WIFE ') and wife in prune_ids) or
                (l.startswith('1 CHIL ') and l[7:].strip() in prune_ids)
            )]
            canonical_records[rid] = cleaned
        else:
            canonical_records[rid] = lines

    out_canonical = out_dir / "mcconigley_final_clean.ged"
    with open(out_canonical, 'w', encoding='utf-8') as f:
        f.writelines(header)
        for lines in canonical_records.values():
            f.writelines(lines)
        f.writelines(trailer)

    out_quarantine = out_dir / "mcconigley_quarantine.ged"
    with open(out_quarantine, 'a', encoding='utf-8') as f:
        f.write("\n0 @I_EXTRANEOUS_HUB@ INDI\n")
        f.write("1 NAME === Quarantined In-Law & Remote Branches ===\n")
        f.write("1 NOTE Collateral branches pruned from master tree\n")
        for rid in (prune_ids | prune_fams):
            if rid in records:
                f.writelines(records[rid])

    print(f"[+] Clean Master: {out_canonical}")
    print(f"[+] Updated Quarantine: {out_quarantine}")

if __name__ == '__main__':
    main()