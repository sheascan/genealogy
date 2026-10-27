import os
import glob
import re
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

def find_generation_boundaries(columns):
    start_idx = 2
    end_idx = None
    for idx, col in enumerate(columns):
        c_clean = col.strip().lower()
        if "birth date" in c_clean or c_clean == "birth" or "dob" in c_clean:
            end_idx = idx
            break
    if end_idx is None:
        for idx, col in enumerate(columns):
            if "date" in col.strip().lower():
                end_idx = idx
                break
    if end_idx is None or end_idx <= start_idx:
        end_idx = 8
    return start_idx, end_idx

def get_person_generation(row, start_idx, end_idx):
    cols = list(row.index)
    for idx in range(start_idx, min(end_idx, len(cols))):
        val = str(row.iloc[idx]).strip()
        if val != "":
            return idx, cols[idx], val
    return -1, "", ""

def is_spouse_entry(name, role):
    n = str(name).strip().lower()
    r = str(role).strip().lower()
    if any(r.startswith(prefix) for prefix in ["sp", "ex", "partner"]):
        return True
    # Matches sp., sp, ex., ex.sp, ex.sp., partner, with or without dots and spaces
    pattern = r"^(sp[\.\s]|sp$|ex[\.\s]|ex\.sp[\.\s]?|partner[\.\s]?)"
    return bool(re.match(pattern, n))

all_resolved = []
all_revised_headers = ["Sibling_Branch"]
for s in SIBLINGS:
    rev_path = os.path.join(REVISED_DIR, f"{s}.csv")
    if os.path.exists(rev_path):
        cols = [c.strip() for c in pd.read_csv(rev_path, nrows=0).columns]
        for c in cols:
            if c not in all_revised_headers:
                all_revised_headers.append(c)

print("=== STARTING GENERATION-AWARE ANCHORING (WITH SPOUSE DETECTION) ===")

for s in SIBLINGS:
    orig_path = os.path.join(ORIGINAL_DIR, f"{s}.csv")
    rev_path = os.path.join(REVISED_DIR, f"{s}.csv")
    if not (os.path.exists(orig_path) and os.path.exists(rev_path)):
        continue

    df_o = pd.read_csv(orig_path, dtype=str, keep_default_na=False).map(lambda x: x.strip())
    df_r = pd.read_csv(rev_path, dtype=str, keep_default_na=False).map(lambda x: x.strip())

    id_col = df_o.columns[0]
    base_ids = set(df_o[id_col].unique()) - {""}

    start_idx, end_idx = find_generation_boundaries(df_r.columns)
    role_col = "Role / Line" if "Role / Line" in df_r.columns else ""

    row_catalog = []
    for r_idx, row in df_r.iterrows():
        g_idx, g_col, name = get_person_generation(row, start_idx, end_idx)
        val_id = str(row[id_col]).strip()
        role = str(row[role_col]).strip() if role_col else ""
        sp = is_spouse_entry(name, role)
        row_catalog.append({
            "r_idx": r_idx,
            "gramps_id": val_id if val_id in base_ids else "",
            "gen_idx": g_idx,
            "gen_col": g_col,
            "name": name,
            "role": role,
            "is_spouse": sp,
            "raw_row": row
        })

    # Link additions
    for entry in row_catalog:
        if entry["gramps_id"] == "" and entry["gen_idx"] != -1:
            curr_g = entry["gen_idx"]
            curr_r = entry["r_idx"]
            is_sp = entry["is_spouse"]

            target_anchor_id = "UNRESOLVED"
            target_anchor_name = ""
            spouse_anchor_id = ""
            spouse_anchor_name = ""
            relation = "Unknown"

            if is_sp:
                # 1. SPOUSE: Look UPWARD in the SAME generation column for the descendant partner
                partner_candidate = None
                for prev in reversed(row_catalog[:curr_r]):
                    if prev["gen_idx"] == curr_g and not prev["is_spouse"] and prev["name"] != "":
                        partner_candidate = prev
                        break

                if partner_candidate:
                    if partner_candidate["gramps_id"] != "":
                        target_anchor_id = partner_candidate["gramps_id"]
                    else:
                        target_anchor_id = f"New:Row_{partner_candidate['r_idx']+2}"
                    target_anchor_name = partner_candidate["name"]
                    relation = "Spouse"
                else:
                    # Fallback to closest prior descendant
                    for prev in reversed(row_catalog[:curr_r]):
                        if not prev["is_spouse"] and prev["name"] != "":
                            target_anchor_id = prev["gramps_id"] if prev["gramps_id"] != "" else f"New:Row_{prev['r_idx']+2}"
                            target_anchor_name = prev["name"]
                            relation = "Spouse"
                            break
            else:
                # 2. CHILD: Look UPWARD for the parent candidate (gen_idx == curr_g - 1)
                parent_candidate = None
                for prev in reversed(row_catalog[:curr_r]):
                    if prev["gen_idx"] == curr_g - 1 and not prev["is_spouse"] and prev["name"] != "":
                        parent_candidate = prev
                        break

                if parent_candidate:
                    if parent_candidate["gramps_id"] != "":
                        target_anchor_id = parent_candidate["gramps_id"]
                    else:
                        target_anchor_id = f"New:Row_{parent_candidate['r_idx']+2}"
                    target_anchor_name = parent_candidate["name"]
                    relation = f"Child of {parent_candidate['gen_col']}"

                    # Also check if this parent has a spouse row immediately following them
                    p_r = parent_candidate["r_idx"]
                    for fol in row_catalog[p_r + 1 : curr_r]:
                        if fol["gen_idx"] == curr_g - 1 and fol["is_spouse"]:
                            spouse_anchor_id = fol["gramps_id"] if fol["gramps_id"] != "" else f"New:Row_{fol['r_idx']+2}"
                            spouse_anchor_name = fol["name"]
                            break
                        elif fol["gen_idx"] != curr_g - 1:
                            break

            row_dict = entry["raw_row"].to_dict()
            row_dict["Sibling_Branch"] = s
            row_dict["Sheet_Row"] = curr_r + 2
            row_dict["Identified_Name"] = entry["name"]
            row_dict["Generation_Col"] = entry["gen_col"]
            row_dict["Relation"] = relation
            row_dict["Anchor_Gramps_ID"] = target_anchor_id
            row_dict["Anchor_Name"] = target_anchor_name
            row_dict["Spouse_Anchor_ID"] = spouse_anchor_id
            row_dict["Spouse_Anchor_Name"] = spouse_anchor_name

            all_resolved.append(row_dict)

if all_resolved:
    df_out = pd.DataFrame(all_resolved)
    audit_cols = [
        "Sibling_Branch", "Sheet_Row", "Generation_Col",
        "Identified_Name", "Relation", "Anchor_Gramps_ID", "Anchor_Name",
        "Spouse_Anchor_ID", "Spouse_Anchor_Name"
    ]
    data_cols = [c for c in all_revised_headers if c not in audit_cols and c in df_out.columns]
    df_out = df_out.reindex(columns=audit_cols + data_cols)

    out_file = os.path.join(OUTPUT_DIR, "all_cousin_additions_anchored.csv")
    df_out.to_csv(out_file, index=False)
    print(f"\n[+] Successfully anchored {len(df_out)} additions!")
    print(f"    Saved to: {out_file}")
else:
    print("[-] No additions found.")
