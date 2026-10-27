import gzip
import os
import re
import time
import xml.etree.ElementTree as ET
import pandas as pd

BASELINE_XML = os.path.expanduser("~/Genealogy/GEDCOM_Files/revised_22sep_fixed.gramps")
ANCHORED_CSV = os.path.expanduser("~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv")
OUTPUT_XML = os.path.expanduser("~/Genealogy/Cousin_Review/combined_tree.gramps")

print(f"[*] Loading baseline XML: {BASELINE_XML}...")
with gzip.open(BASELINE_XML, "rb") as gz:
    tree = ET.parse(gz)
root = tree.getroot()

ns = ""
if root.tag.startswith("{"):
    ns = root.tag.split("}")[0] + "}"

def get_tag(tag):
    return f"{ns}{tag}"

def clean_person_name(name_raw):
    n = re.sub(r'^[0-9]+\.\s*', '', (name_raw or '').strip())
    n = re.sub(r'^(sp[\.\s]|ex[\.\s]|ex\.sp[\.\s]?|partner[\.\s]?)\s*', '', n, flags=re.IGNORECASE)
    parts = n.strip().split()
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    else:
        if len(parts) >= 3 and parts[-2].lower() in ['mc', 'mac', "o'", 'de', 'da']:
            surname = " ".join(parts[-2:])
            firstname = " ".join(parts[:-2])
        else:
            surname = parts[-1]
            firstname = " ".join(parts[:-1])
        return firstname, surname

people_el = root.find(get_tag("people"))
families_el = root.find(get_tag("families"))

id_to_handle = {}
people_by_handle = {}
for p in people_el.findall(get_tag("person")):
    gid = p.get("id")
    h = p.get("handle")
    if gid and h:
        id_to_handle[gid] = h
        people_by_handle[h] = p

df = pd.read_csv(ANCHORED_CSV, dtype=str, keep_default_na=False)

ts = str(int(time.time()))
temp_id_to_handle = {}
new_persons_count = 0

# 1. Inject Person nodes
for _, row in df.iterrows():
    branch = row['Sibling_Branch']
    row_num = row['Sheet_Row']
    branch_name = branch.split('-')[0]
    
    raw_name = row['Identified_Name']
    if branch_name == "brigid" and "catherine" in raw_name.lower() and row_num == "33":
        continue

    temp_id = f"_NEW_{branch_name}_{row_num}"
    p_handle = f"_new_h_{branch_name}_{row_num}"
    temp_id_to_handle[temp_id] = p_handle
    id_to_handle[temp_id] = p_handle

    fn, sn = clean_person_name(raw_name)
    bdate = row.get('Birth Date', '').strip()
    bplace = row.get('Birth Place', '').strip()
    ddate = row.get('Death Date', '').strip()
    dplace = row.get('Death Place', '').strip()

    p_node = ET.SubElement(people_el, get_tag("person"), {
        "handle": p_handle,
        "change": ts,
        "id": temp_id
    })
    people_by_handle[p_handle] = p_node
    
    name_node = ET.SubElement(p_node, get_tag("name"), {"type": "Birth Name"})
    first_node = ET.SubElement(name_node, get_tag("first"))
    first_node.text = fn
    sur_node = ET.SubElement(name_node, get_tag("surname"))
    sur_node.text = sn

    if bdate or bplace:
        ev_h = f"_ev_b_{branch_name}_{row_num}"
        events_el = root.find(get_tag("events"))
        if events_el is not None:
            ev_node = ET.SubElement(events_el, get_tag("event"), {"handle": ev_h, "change": ts, "id": f"E_{ev_h}"})
            ET.SubElement(ev_node, get_tag("type")).text = "Birth"
            if bdate:
                d_node = ET.SubElement(ev_node, get_tag("dateval"))
                d_node.set("val", bdate)
            ET.SubElement(p_node, get_tag("eventref"), {"hlink": ev_h, "role": "Primary"})

    new_persons_count += 1

print(f"[+] Injected {new_persons_count} new individuals into XML.")

def resolve_handle(anchor_str, branch_name):
    if not anchor_str:
        return None
    if anchor_str.startswith("New:Row_"):
        r = anchor_str.split("_")[1]
        t_id = f"_NEW_{branch_name}_{r}"
        return id_to_handle.get(t_id)
    return id_to_handle.get(anchor_str)

fam_index = 9000
pair_to_fam_handle = {}
parent_to_fam_handle = {}

# 2. Existing families index
for f in families_el.findall(get_tag("family")):
    fh = f.get("handle")
    fat = f.find(get_tag("father"))
    mot = f.find(get_tag("mother"))
    f_h = fat.get("hlink") if fat is not None else None
    m_h = mot.get("hlink") if mot is not None else None
    if f_h and m_h:
        pair_to_fam_handle[tuple(sorted([f_h, m_h]))] = fh
    elif f_h and not m_h:
        parent_to_fam_handle[f_h] = (fh, "mother")
    elif m_h and not f_h:
        parent_to_fam_handle[m_h] = (fh, "father")

# 3. Pass 1: Spouses
for _, row in df.iterrows():
    branch_name = row['Sibling_Branch'].split('-')[0]
    row_num = row['Sheet_Row']
    if branch_name == "brigid" and "catherine" in row['Identified_Name'].lower() and row_num == "33":
        continue

    temp_id = f"_NEW_{branch_name}_{row_num}"
    p_handle = temp_id_to_handle.get(temp_id)
    relation = row.get('Relation', '')
    anchor_id = row.get('Anchor_Gramps_ID', '').strip()

    if relation == "Spouse" and p_handle:
        partner_h = resolve_handle(anchor_id, branch_name)
        if partner_h:
            pair = tuple(sorted([p_handle, partner_h]))
            # If partner already has a family missing this spouse slot, adopt it!
            if partner_h in parent_to_fam_handle:
                f_handle, slot_to_fill = parent_to_fam_handle[partner_h]
                f_node = next((f for f in families_el.findall(get_tag("family")) if f.get("handle") == f_handle), None)
                if f_node is not None:
                    ET.SubElement(f_node, get_tag(slot_to_fill), {"hlink": p_handle})
                    pair_to_fam_handle[pair] = f_handle
                    p_node = people_by_handle.get(p_handle)
                    if p_node is not None:
                        ET.SubElement(p_node, get_tag("parentin"), {"hlink": f_handle})
                    del parent_to_fam_handle[partner_h]
                    continue

            if pair not in pair_to_fam_handle:
                fam_index += 1
                f_handle = f"_fam_new_{fam_index}"
                pair_to_fam_handle[pair] = f_handle
                f_node = ET.SubElement(families_el, get_tag("family"), {
                    "handle": f_handle,
                    "change": ts,
                    "id": f"F{fam_index}"
                })
                ET.SubElement(f_node, get_tag("father"), {"hlink": partner_h})
                ET.SubElement(f_node, get_tag("mother"), {"hlink": p_handle})
                
                for h_target in pair:
                    target_p = people_by_handle.get(h_target)
                    if target_p is not None:
                        ET.SubElement(target_p, get_tag("parentin"), {"hlink": f_handle})

# 4. Pass 2: Children
for _, row in df.iterrows():
    branch_name = row['Sibling_Branch'].split('-')[0]
    row_num = row['Sheet_Row']
    if branch_name == "brigid" and "catherine" in row['Identified_Name'].lower() and row_num == "33":
        continue

    temp_id = f"_NEW_{branch_name}_{row_num}"
    p_handle = temp_id_to_handle.get(temp_id)
    relation = row.get('Relation', '')
    anchor_id = row.get('Anchor_Gramps_ID', '').strip()
    spouse_anchor_id = row.get('Spouse_Anchor_ID', '').strip()

    if "Child" in relation and p_handle:
        parent_h = resolve_handle(anchor_id, branch_name)
        sp_parent_h = resolve_handle(spouse_anchor_id, branch_name) if spouse_anchor_id else None
        
        target_f_handle = None
        if parent_h and sp_parent_h:
            pair = tuple(sorted([parent_h, sp_parent_h]))
            target_f_handle = pair_to_fam_handle.get(pair)
            
        if not target_f_handle and parent_h:
            for pair, fh in pair_to_fam_handle.items():
                if parent_h in pair:
                    target_f_handle = fh
                    break
                    
        if not target_f_handle and parent_h:
            fam_index += 1
            target_f_handle = f"_fam_new_{fam_index}"
            pair_to_fam_handle[(parent_h, "")] = target_f_handle
            f_node = ET.SubElement(families_el, get_tag("family"), {
                "handle": target_f_handle,
                "change": ts,
                "id": f"F{fam_index}"
            })
            ET.SubElement(f_node, get_tag("father"), {"hlink": parent_h})
            parent_p = people_by_handle.get(parent_h)
            if parent_p is not None:
                ET.SubElement(parent_p, get_tag("parentin"), {"hlink": target_f_handle})

        if target_f_handle:
            f_node = next((f for f in families_el.findall(get_tag("family")) if f.get("handle") == target_f_handle), None)
            if f_node is not None:
                ET.SubElement(f_node, get_tag("childref"), {"hlink": p_handle})
            child_p = people_by_handle.get(p_handle)
            if child_p is not None:
                ET.SubElement(child_p, get_tag("childof"), {"hlink": target_f_handle})

print(f"[+] Total families linked: {len(pair_to_fam_handle)}")

print(f"[*] Writing combined XML to {OUTPUT_XML}...")
with gzip.open(OUTPUT_XML, "wb") as gz:
    tree.write(gz, encoding="utf-8", xml_declaration=True)

print("[+] Done! Combined XML generated.")
