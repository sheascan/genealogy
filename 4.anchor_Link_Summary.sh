python3 - << 'EOF'
import pandas as pd
import os

path = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")
df = pd.read_csv(path)

print("=== 1. ADDITIONS BY SIBLING BRANCH ===")
print(df['Sibling_Branch'].value_counts().to_string())

print("\n=== 2. UNRESOLVED OR AMBIGUOUS ANCHORS ===")
unresolved = df[df['Anchor_Gramps_ID'].isin(['UNRESOLVED', '']) | df['Anchor_Gramps_ID'].str.startswith('New:')]
if unresolved.empty:
    print("Zero unresolved rows! Every addition successfully linked to a base Gramps ID.")
else:
    print(f"Found {len(unresolved)} rows requiring attention:")
    print(unresolved[['Sheet_Row', 'Sibling_Branch', 'Generation_Col', 'Identified_Name', 'Relation', 'Anchor_Gramps_ID']])

print("\n=== 3. ANCHOR LINK SUMMARY ===")
print(df['Relation'].value_counts().to_string())
EOF