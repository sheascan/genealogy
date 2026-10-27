import os
import re
import csv
import pandas as pd

ANCHORED_CSV = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")
OUTPUT_DIR = os.path.expanduser("~/Genealogy/Cousin_Review/gramps_import_ready")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "cousin_additions_for_gramps.csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(ANCHORED_CSV, dtype=str, keep_default_na=False)

def clean_person_name(name_raw):
    n = re.sub(r'^[0-9]+\.\s*', '', name_raw.strip())
    n = re.sub(r'^(sp\.?|ex\.?sp\.?|ex\.?|partner)\s*', '', n, flags=re.IGNORECASE)
    parts = n.strip().split()
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    else:
        # Check for prefixes like "Mc", "Mac", "O'", "de", "da"
        if len(parts) >= 3 and parts[-2].lower() in ['mc', 'mac', "o'", 'de', 'da']:
            surname = " ".join(parts[-2:])
            firstname = " ".join(parts[:-2])
        else:
            surname = parts[-1]
            firstname = " ".join(parts[:-1])
        return firstname, surname

persons = []
person_id_map = {}  # (branch, row) -> temp_id
families = []       # list of (fam_id, husband_id, wife_id)
children_links = [] # list of (fam_id, child_temp_id)

# 1. Build Persons table
for _, row in df.iterrows():
    branch = row['Sibling_Branch']
    row_num = row['Sheet_Row']
    temp_id = f"_NEW_{branch.split('-')[0]}_{row_num}"
    person_id_map[(branch, row_num)] = temp_id

    raw_name = row['Identified_Name']
    fn, sn = clean_person_name(raw_name)
    
    bdate = row.get('Birth Date', '').strip()
    bplace = row.get('Birth Place', '').strip()
    ddate = row.get('Death Date', '').strip()
    dplace = row.get('Death Place', '').strip()
    
    persons.append([
        temp_id,
        fn,
        sn,
        "",  # gender (Gramps auto-infers or defaults)
        bdate,
        bplace,
        ddate,
        dplace
    ])

# 2. Build Marriages and Children links
fam_counter = 1
# Map parental pair (p1, p2) to fam_ref
parent_pair_to_fam = {}

for _, row in df.iterrows():
    branch = row['Sibling_Branch']
    row_num = row['Sheet_Row']
    temp_id = person_id_map[(branch, row_num)]
    relation = row.get('Relation', '')
    anchor_id = row.get('Anchor_Gramps_ID', '').strip()
    spouse_anchor_id = row.get('Spouse_Anchor_ID', '').strip()

    # Resolve "New:Row_X" placeholders to temp_ids
    if anchor_id.startswith("New:Row_"):
        r_target = anchor_id.split("_")[1]
        anchor_id = person_id_map.get((branch, r_target), anchor_id)
    if spouse_anchor_id.startswith("New:Row_"):
        r_target = spouse_anchor_id.split("_")[1]
        spouse_anchor_id = person_id_map.get((branch, r_target), spouse_anchor_id)

    if relation == "Spouse":
        # Anchor is their partner!
        p1 = anchor_id
        p2 = temp_id
        pair_key = tuple(sorted([p1, p2]))
        if pair_key not in parent_pair_to_fam:
            fam_ref = f"FAM_{fam_counter}"
            fam_counter += 1
            parent_pair_to_fam[pair_key] = fam_ref
            families.append([fam_ref, p1, p2])
    elif "Child" in relation:
        # Anchor is the parent (and optional spouse_anchor_id)
        p1 = anchor_id
        p2 = spouse_anchor_id
        pair_key = tuple(sorted([p1, p2])) if p2 else (p1, "")
        if pair_key not in parent_pair_to_fam:
            fam_ref = f"FAM_{fam_counter}"
            fam_counter += 1
            parent_pair_to_fam[pair_key] = fam_ref
            families.append([fam_ref, p1, p2])
        fam_ref = parent_pair_to_fam[pair_key]
        children_links.append([fam_ref, temp_id])

# 3. Write Gramps CSV format
with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)

    # TABLE 1: PERSONS
    writer.writerow([
        "person", "firstname", "surname", "gender",
        "birthdate", "birthplace", "deathdate", "deathplace"
    ])
    for p in persons:
        writer.writerow(p)

    writer.writerow([])

    # TABLE 2: MARRIAGES
    writer.writerow(["marriage", "husband", "wife"])
    for fam in families:
        writer.writerow(fam)

    writer.writerow([])

    # TABLE 3: CHILDREN
    writer.writerow(["family", "child"])
    for link in children_links:
        writer.writerow(link)

print("Generated Gramps CSV import successfully!")
print(f"  Total Persons:   {len(persons)}")
print(f"  Total Marriages: {len(families)}")
print(f"  Total Children:  {len(children_links)}")
print(f"  Target File:     {OUTPUT_CSV}")
