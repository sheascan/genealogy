import os
import glob
import pandas as pd

ORIGINAL_DIR = os.path.expanduser("~/Genealogy/Cousin_Review/shadow-original_csv")
REVISED_DIR = os.path.expanduser("~/Genealogy/Cousin_Review/revised-by-cousin_csv")
OUTPUT_DIR = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SIBLINGS = [
    "brigid-29d76039",
    "charlie-9359da3b",
    "danny-4099237d",
    "mary-d9019cd4",
    "mick-de3d04b5",
    "norah-70f1d3b4",
    "paddy-2cb79295",
    "sean-d85eb77e",
    "tommy-1e091c4b"
]

def find_id_column(columns):
    for c in columns:
        if c.strip().lower() in ["gramps_id", "gramps id", "id", "person_id", "handle"]:
            return c
    return columns[0]

all_additions = []
all_modifications = []
all_revised_headers = ["Sibling_Branch"]

print("=== STEP 1: SCANNING ALL REVISED HEADERS TO BUILD MASTER SCHEMA ===")

# Build a comprehensive ordered list of all columns across all revised files
for s in SIBLINGS:
    rev_path = os.path.join(REVISED_DIR, f"{s}.csv")
    if os.path.exists(rev_path):
        cols = [c.strip() for c in pd.read_csv(rev_path, nrows=0).columns]
        for c in cols:
            if c not in all_revised_headers:
                all_revised_headers.append(c)

print(f"Total unified columns across all revised files: {len(all_revised_headers)}")
print(f"Master Columns: {all_revised_headers}\n")

print("=== STEP 2: EXTRACTING ADDITIONS AND MODIFICATIONS ===")

for s in SIBLINGS:
    orig_path = os.path.join(ORIGINAL_DIR, f"{s}.csv")
    rev_path = os.path.join(REVISED_DIR, f"{s}.csv")

    if not (os.path.exists(orig_path) and os.path.exists(rev_path)):
        continue

    # Read files ensuring every column is stripped of whitespace
    df_o = pd.read_csv(orig_path, dtype=str, keep_default_na=False)
    df_r = pd.read_csv(rev_path, dtype=str, keep_default_na=False)

    df_o.columns = [c.strip() for c in df_o.columns]
    df_r.columns = [c.strip() for c in df_r.columns]

    df_o = df_o.map(lambda x: x.strip() if isinstance(x, str) else x)
    df_r = df_r.map(lambda x: x.strip() if isinstance(x, str) else x)

    id_col = find_id_column(df_o.columns)
    base_ids = set(df_o[id_col].unique()) - {""}

    # 1. EXTRACT NEW PEOPLE (Includes all new generation columns present in df_r)
    has_text = df_r.apply(lambda r: "".join(r.values) != "", axis=1)
    is_new = (~df_r[id_col].isin(base_ids)) & has_text

    df_new = df_r[is_new].copy()
    if not df_new.empty:
        df_new.insert(0, "Sibling_Branch", s)
        # Reindex to master schema so no new column is dropped or misaligned
        df_new = df_new.reindex(columns=all_revised_headers, fill_value="")
        all_additions.append(df_new)
        print(f"[{s}] Captured {len(df_new)} new people/rows with {len(df_r.columns)} columns")

    # 2. EXTRACT FIELD MODIFICATIONS ON EXISTING PEOPLE
    df_existing_rev = df_r[df_r[id_col].isin(base_ids)].copy()
    df_existing_orig = df_o[df_o[id_col].isin(base_ids)].copy()

    # Compare columns present in baseline against revised
    merged = pd.merge(df_existing_orig, df_existing_rev, on=id_col, suffixes=("_orig", "_rev"))
    shared_cols = [c for c in df_o.columns if c != id_col and c in df_r.columns]

    for _, row in merged.iterrows():
        pid = row[id_col]
        for col in shared_cols:
            val_o = row[f"{col}_orig"]
            val_r = row[f"{col}_rev"]

            if val_o != val_r and val_r != "":
                all_modifications.append({
                    "Sibling_Branch": s,
                    "Person_ID": pid,
                    "Field": col,
                    "Original_Value": val_o,
                    "Revised_Value": val_r,
                    "Change_Type": "Added Detail" if val_o == "" else "Correction"
                })

    # Also capture if existing people had entries filled in newly added columns
    new_cols_in_branch = [c for c in df_r.columns if c not in df_o.columns]
    for col in new_cols_in_branch:
        for _, row in df_existing_rev.iterrows():
            val = row[col]
            if val != "":
                all_modifications.append({
                    "Sibling_Branch": s,
                    "Person_ID": row[id_col],
                    "Field": col,
                    "Original_Value": "",
                    "Revised_Value": val,
                    "Change_Type": "Added Column Detail"
                })

# --- WRITE COMPREHENSIVE OUTPUT FILES ---
if all_additions:
    final_additions = pd.concat(all_additions, ignore_index=True)
    out_add = os.path.join(OUTPUT_DIR, "all_cousin_additions.csv")
    final_additions.to_csv(out_add, index=False)
    print(f"\n[+] Saved {len(final_additions)} new people to:\n    {out_add}")
    print(f"    Columns in output: {list(final_additions.columns)}")
else:
    print("\n[-] No row additions detected.")

if all_modifications:
    final_mods = pd.DataFrame(all_modifications)
    out_mods = os.path.join(OUTPUT_DIR, "all_field_modifications.csv")
    final_mods.to_csv(out_mods, index=False)
    print(f"[+] Saved {len(final_mods)} modifications to:\n    {out_mods}")