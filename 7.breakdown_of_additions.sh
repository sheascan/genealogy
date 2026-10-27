python3 - << 'EOF'
import pandas as pd
import os

path = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")
df = pd.read_csv(path)

# 1. Truly Unresolved (No anchor found at all)
true_orphans = df[df['Anchor_Gramps_ID'].isin(['UNRESOLVED', '', None])]

# 2. Chained Additions (Child of another newly added person)
chained = df[df['Anchor_Gramps_ID'].str.startswith('New:Row_', na=False)]

# 3. Direct Descendants (Directly attached to an existing Gramps ID)
direct = df[~df['Anchor_Gramps_ID'].isin(['UNRESOLVED', '', None]) & ~df['Anchor_Gramps_ID'].str.startswith('New:Row_', na=False)]

print("=== BREAKDOWN OF THE ~139 ADDITIONS ===")
print(f"1. Direct Children of Existing Ancestors: {len(direct)}")
print(f"2. Nested Descendants (Child of a new addition): {len(chained)}")
print(f"3. TRUE UNRESOLVED ORPHANS:               {len(true_orphans)}")

if not true_orphans.empty:
    print("\n--- These are the only rows that need manual checking ---")
    print(true_orphans[['Sheet_Row', 'Sibling_Branch', 'Identified_Name', 'Generation_Col']])
else:
    print("\nResult: There are 0 orphan records. 100% of rows are connected in parent-child chains!")
EOF