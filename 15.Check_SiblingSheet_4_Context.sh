# Step 2: Check the Sibling Sheet for Context
echo Step 2: Check the Sibling Sheet for Context

python3 - << 'EOF'
import pandas as pd
import os

path = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")
df = pd.read_csv(path)
match = df[df['Anchor_Gramps_ID'] == 'I500757']

if not match.empty:
    branch = match.iloc[0]['Sibling_Branch']
    sheet_row = int(match.iloc[0]['Sheet_Row'])
    
    rev_path = os.path.expanduser(f"~/Genealogy/Cousin_Review/revised-by-cousin_csv/{branch}.csv")
    df_rev = pd.read_csv(rev_path, dtype=str).fillna('')
    
    # Show 3 rows before and 3 rows after in the revised sheet
    start = max(0, sheet_row - 4)
    end = min(len(df_rev), sheet_row + 3)
    
    print(f"=== SURROUNDING CONTEXT IN {branch}.csv (Rows {start+2} to {end+1}) ===")
    cols_to_show = [c for c in df_rev.columns[:6]]
    print(df_rev.iloc[start:end][cols_to_show].to_string())
EOF