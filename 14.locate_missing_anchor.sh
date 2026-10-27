# Lets locate that single missing anchor (I500757) to see which sibling branch and sheet row it came from, and determine why it was formatted with I500... instead of a typical I0... ID:
echo Lets locate that single missing anchor I500757

python3 - << 'EOF'
import pandas as pd
import os

path = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")
df = pd.read_csv(path)

target_rows = df[df['Anchor_Gramps_ID'] == 'I500757']
print("=== ADDITIONS ATTACHED TO I500757 ===")
print(target_rows[['Sheet_Row', 'Sibling_Branch', 'Identified_Name', 'Relation', 'Anchor_Gramps_ID', 'Anchor_Name']])
EOF