# Verify revised_22sep_fixed.gramps Matches Your Sibling Spreadsheets
echo Verify revised_22sep_fixed.gramps Matches Your Sibling Spreadsheets

python3 - << 'EOF'
import os
import gzip
import xml.etree.ElementTree as ET
import pandas as pd

GRAMPS_FILE = os.path.expanduser("~/Genealogy/GEDCOM_Files/revised_22sep_fixed.gramps")
ADDITIONS_FILE = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")

# 1. Extract Gramps IDs from the fixed database
print(f"Reading {os.path.basename(GRAMPS_FILE)}...")
with gzip.open(GRAMPS_FILE, 'rb') as gz:
    tree = ET.parse(gz)
    root = tree.getroot()

db_ids = set()
for elem in root.iter():
    if elem.tag.split('}')[-1] == 'person':
        # Gramps stores ID in the 'id' attribute or child <grampsid>
        gid = elem.get('id')
        if not gid:
            gid_elem = elem.find('{*}grampsid') or elem.find('grampsid')
            if gid_elem is not None:
                gid = gid_elem.text
        if gid:
            db_ids.add(gid.strip())

print(f"Total IDs found in database: {len(db_ids)}")

# 2. Compare against anchor IDs from the additions file
df_add = pd.read_csv(ADDITIONS_FILE)
# Filter for direct anchors (ignore nested 'New:Row_' links)
anchors_to_check = df_add[~df_add['Anchor_Gramps_ID'].str.startswith('New:Row_', na=False)]['Anchor_Gramps_ID'].unique()

missing = [a for a in anchors_to_check if a not in db_ids]

print(f"\nTarget Anchor IDs to attach to: {len(anchors_to_check)}")
if not missing:
    print("SUCCESS: 100% of baseline anchor IDs match revised_22sep_fixed.gramps perfectly!")
else:
    print(f"WARNING: {len(missing)} IDs were not found in the baseline file:")
    print(missing)
EOF