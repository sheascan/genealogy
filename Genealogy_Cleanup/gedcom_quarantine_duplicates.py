#!/usr/bin/env python3
import sys
import re
import csv
from collections import deque
from gedcom_utils import load_gedcom_raw_records, resolve_path

def parse_relationships(records):
    indis = {}
    fams = {}
    for rid, lines in records.items():
        tag = lines[0].split()[2] if len(lines[0].split()) > 2 else ''
        if tag == 'INDI':
            name = "Unknown"
            famc = None
            fams_list = []
            for l in lines:
                if l.startswith('1 NAME '):
                    name = l[7:].replace('/', '').strip()
                elif l.startswith('1 FAMC '):
                    famc = l[7:].strip()
                elif l.startswith('1 FAMS '):
                    fams_list.append(l[7:].strip())
            indis[rid] = {'name': name, 'famc': famc, 'fams': fams_list}
        elif tag == 'FAM':
            husb, wife, chil = None, None, []
            for l in lines:
                if l.startswith('1 HUSB '): husb = l[7:].strip()
                elif l.startswith('1 WIFE '): wife = l[7:].strip()
                elif l.startswith('1 CHIL '): chil.append(l[7:].strip())
            fams[rid] = {'husb': husb, 'wife': wife, 'children': chil}
    return indis, fams

def get_descendants(root_ids, fams):
    visited = set(root_ids)
    q = deque(root_ids)
    all_desc = set(root_ids)
    while q:
        curr = q.popleft()
        for fid, f in fams.items():
            if f['husb'] == curr or f['wife'] == curr:
                for c in f['children']:
                    if c not in visited:
                        visited.add(c)
                        all_desc.add(c)
                        q.append(c)
    return all_desc

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gedcom_quarantine_duplicates.py <master.ged> <duplicates_manifest.csv>")
        sys.exit(1)

    ged_file = resolve_path(sys.argv[1])
    csv_file = resolve_path(sys.argv[2])
    out_dir = ged_file.parent

    header, records, trailer = load_gedcom_raw_records(ged_file)
    indis, fams = parse_relationships(records)

    quarantine_indis = set()
    quarantine_fams = set()
    catalog = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if row.get('Recommendation', '').upper() == 'IGNORE':
                continue
            
            branch_id = f"BRANCH_{idx+1:03d}"
            dup_id_str = row['Duplicate_ID']
            dup_ids = re.findall(r'@[^@]+@', dup_id_str)
            
            subtree = get_descendants(dup_ids, fams)
            quarantine_indis.update(subtree)

            for fid, f in fams.items():
                if f['husb'] in subtree or f['wife'] in subtree:
                    quarantine_fams.add(fid)

            catalog.append({
                "Branch_ID": branch_id,
                "Type": row['Type'],
                "Primary_Anchor": row['Primary_ID'],
                "Quarantined_Root": dup_id_str,
                "Root_Name": row['Duplicate_Name'],
                "Subtree_Size": len(subtree),
                "Subtree_Members": " ".join(subtree)
            })

    print("\n" + "="*50)
    print(" QUARANTINE ENGINE EXECUTION")
    print("="*50)
    print(f"Total Individuals targeted: {len(quarantine_indis)}")
    print(f"Total Families targeted:    {len(quarantine_fams)}")

    canonical_records = {}
    for rid, lines in records.items():
        if rid in quarantine_indis or rid in quarantine_fams:
            continue
        
        cleaned_lines = []
        for l in lines:
            if l.startswith('1 CHIL ') and l[7:].strip() in quarantine_indis:
                continue
            if l.startswith('1 HUSB ') and l[7:].strip() in quarantine_indis:
                continue
            if l.startswith('1 WIFE ') and l[7:].strip() in quarantine_indis:
                continue
            cleaned_lines.append(l)
        canonical_records[rid] = cleaned_lines

    out_canonical = out_dir / "mcconigley_canonical.ged"
    with open(out_canonical, 'w', encoding='utf-8') as f:
        f.writelines(header)
        for lines in canonical_records.values():
            f.writelines(lines)
        f.writelines(trailer)

    out_quarantine = out_dir / "mcconigley_quarantine.ged"
    with open(out_quarantine, 'w', encoding='utf-8') as f:
        f.writelines(header)
        f.write("0 @I_INDEX@ INDI\n")
        f.write("1 NAME === Quarantined Duplicate Branches ===\n")
        f.write("1 NOTE Hub record linking to all severed duplicate clusters\n")
        for rid in (quarantine_indis | quarantine_fams):
            if rid in records:
                f.writelines(records[rid])
        f.writelines(trailer)

    out_catalog = out_dir / "quarantine_catalog.csv"
    cat_fields = ["Branch_ID", "Type", "Primary_Anchor", "Quarantined_Root", "Root_Name", "Subtree_Size", "Subtree_Members"]
    with open(out_catalog, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cat_fields)
        writer.writeheader()
        writer.writerows(catalog)

    print(f"[+] Canonical GEDCOM:  {out_canonical}")
    print(f"[+] Quarantine GEDCOM: {out_quarantine}")
    print(f"[+] Catalog CSV:       {out_catalog}")
    print("="*50)

if __name__ == '__main__':
    main()