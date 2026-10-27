#!/usr/bin/env python3
import gzip
import re
import xml.etree.ElementTree as ET

tree_file = "Rebuilds/McConigley_25Oct.gramps"
print(f"Loading {tree_file}...")

with gzip.open(tree_file, "rb") as f:
    tree = ET.parse(f)
root = tree.getroot()
ns = {"g": "http://gramps-project.org/xml/1.7.1/"}

people = {p.attrib["handle"]: p for p in root.findall(".//g:person", ns)}
families = {f.attrib["handle"]: f for f in root.findall(".//g:family", ns)}

child_to_fams = {}
for fh, fam in families.items():
    for ch in fam.findall(".//g:childref", ns):
        child_to_fams.setdefault(ch.attrib.get("hlink"), []).append(fam)

def extract_year(date_val):
    if not date_val:
        return ""
    match = re.search(r"\b(\d{4})\b", date_val)
    return match.group(1) if match else date_val.strip()

def get_person_info(p):
    if p is None:
        return "Unknown"
    first = p.findtext(".//g:first", default="", namespaces=ns).strip()
    sur = p.findtext(".//g:surname", default="", namespaces=ns).strip()
    name = f"{sur}, {first}".strip(", ")
    
    dates = []
    for evt_ref in p.findall(".//g:eventref", ns):
        eh = evt_ref.attrib.get("hlink")
        evt = root.find(f'.//g:event[@handle="{eh}"]', ns)
        if evt is not None:
            etype = evt.findtext("g:type", default="", namespaces=ns)
            dval = evt.findtext("g:dateval", default="", namespaces=ns)
            if not dval:
                dt_node = evt.find("g:dateval", ns)
                if dt_node is not None:
                    dval = dt_node.attrib.get("val", "")
            
            yr = extract_year(dval)
            if etype == "Birth" and yr:
                dates.append(f"b. {yr}")
            elif etype == "Death" and yr:
                dates.append(f"d. {yr}")
                
    d_str = f" ({', '.join(dates)})" if dates else ""
    return f"{name}{d_str}"

def get_parents(p_handle):
    fams = child_to_fams.get(p_handle, [])
    if not fams:
        return None, None
    fam = fams[0]
    fat = fam.find(".//g:father", ns)
    mot = fam.find(".//g:mother", ns)
    f_h = fat.attrib.get("hlink") if fat is not None else None
    m_h = mot.attrib.get("hlink") if mot is not None else None
    return people.get(f_h), people.get(m_h)

def render_pedigree_ascii(p_handle, max_gen=5, cur_gen=1, prefix="", is_top=True, is_root=True):
    if not p_handle or cur_gen > max_gen:
        return []
    p = people.get(p_handle)
    label = get_person_info(p)
    fat, mot = get_parents(p_handle)
    
    step_empty = "       "
    step_vert  = "|      "
    
    lines = []
    if fat and cur_gen < max_gen:
        lines.extend(render_pedigree_ascii(
            fat.attrib.get("handle"), max_gen, cur_gen + 1,
            prefix + (step_empty if is_top and not is_root else step_vert),
            is_top=True, is_root=False
        ))
    
    conn = "+----- " if is_root else ("/----- " if is_top else "\\----- ")
    lines.append(f"{prefix}{conn}{label}")
    
    if mot and cur_gen < max_gen:
        lines.extend(render_pedigree_ascii(
            mot.attrib.get("handle"), max_gen, cur_gen + 1,
            prefix + (step_vert if is_top or is_root else step_empty),
            is_top=False, is_root=False
        ))
    return lines

def format_person_with_spouses(p):
    p_label = get_person_info(p)
    p_handle = p.attrib["handle"]
    
    spouses = []
    p_fams = [f.attrib.get("hlink") for f in p.findall(".//g:parentin", ns)]
    for fh in p_fams:
        fam = families.get(fh)
        if not fam:
            continue
        fat = fam.find(".//g:father", ns)
        mot = fam.find(".//g:mother", ns)
        f_h = fat.attrib.get("hlink") if fat is not None else None
        m_h = mot.attrib.get("hlink") if mot is not None else None
        
        spouse_h = m_h if f_h == p_handle else (f_h if m_h == p_handle else None)
        if spouse_h and spouse_h in people:
            spouses.append(get_person_info(people[spouse_h]))
            
    if spouses:
        unique_spouses = list(dict.fromkeys(spouses))
        return f"{p_label}  +  {' + '.join(unique_spouses)}"
    return p_label

def render_descendants_tree(p_handle, max_gen=4, cur_gen=1, prefix=""):
    if not p_handle or cur_gen > max_gen:
        return []
    p = people.get(p_handle)
    lines = [f"{prefix}\\----- {format_person_with_spouses(p)}"]
    
    p_fams = [f.attrib.get("hlink") for f in p.findall(".//g:parentin", ns)]
    for fh in p_fams:
        fam = families.get(fh)
        if not fam:
            continue
        children = [people.get(c.attrib.get("hlink")) for c in fam.findall(".//g:childref", ns) if c.attrib.get("hlink") in people]
        for i, ch in enumerate(children):
            is_last = (i == len(children) - 1)
            sub_p = prefix + ("       " if is_last else "|      ")
            ch_lines = render_descendants_tree(ch.attrib.get("handle"), max_gen, cur_gen + 1, sub_p)
            if ch_lines:
                conn = "\\----- " if is_last else "+----- "
                ch_lines[0] = f"{prefix}{conn}{format_person_with_spouses(ch)}"
                lines.extend(ch_lines)
    return lines

# Root definitions
mick_sean = [p for p in people.values() if p.attrib.get("id") == "I500007"][0]
mick_handle = mick_sean.attrib["handle"]

fams = [families[f.attrib["hlink"]] for f in mick_sean.findall(".//g:parentin", ns) if f.attrib.get("hlink") in families]
wife = None
if fams:
    mot = fams[0].find(".//g:mother", ns)
    if mot is not None:
        wife = people.get(mot.attrib.get("hlink"))

# Build pages list
pages = []

# Page 1: Ancestry
p1_lines = []
p1_lines.append("="*80)
p1_lines.append("HOURGLASS REPORT: Mick Sean McConigley & Margaret Heraghty")
p1_lines.append("="*80)
p1_lines.append("\n[ HUSBAND'S ANCESTRY ]")
p1_lines.extend(render_pedigree_ascii(mick_handle, max_gen=5))
if wife:
    p1_lines.append("\n[ WIFE'S ANCESTRY ]")
    p1_lines.extend(render_pedigree_ascii(wife.attrib["handle"], max_gen=5))
pages.append("\n".join(p1_lines))

# Collect Mick Sean's children
all_children = []
for fh in [f.attrib.get("hlink") for f in mick_sean.findall(".//g:parentin", ns)]:
    fam = families.get(fh)
    if fam:
        all_children.extend([people.get(c.attrib.get("hlink")) for c in fam.findall(".//g:childref", ns) if c.attrib.get("hlink") in people])

# Generate a page for each child's family
for idx, ch in enumerate(all_children):
    p_branch = []
    p_branch.append("="*80)
    p_branch.append(f"DESCENDANT FAMILY BRANCH {idx+1} OF {len(all_children)}")
    p_branch.append(f"Root: Mick Sean McConigley & Margaret Heraghty")
    p_branch.append("="*80)
    p_branch.append("|")
    p_branch.append("|")
    p_branch.append(f"+----- {format_person_with_spouses(ch)}")
    
    # Downstream descendants of this child
    child_fams = [f.attrib.get("hlink") for f in ch.findall(".//g:parentin", ns)]
    for cfh in child_fams:
        cfam = families.get(cfh)
        if not cfam:
            continue
        gchildren = [people.get(gc.attrib.get("hlink")) for gc in cfam.findall(".//g:childref", ns) if gc.attrib.get("hlink") in people]
        for j, gc in enumerate(gchildren):
            is_last = (j == len(gchildren) - 1)
            sub_p = "       "
            gc_lines = render_descendants_tree(gc.attrib.get("handle"), max_gen=4, cur_gen=2, prefix=sub_p + ("       " if is_last else "|      "))
            if gc_lines:
                gc_conn = "\\----- " if is_last else "+----- "
                gc_lines[0] = f"{sub_p}{gc_conn}{format_person_with_spouses(gc)}"
                p_branch.extend(gc_lines)
    pages.append("\n".join(p_branch))

# Save as plain ASCII text with form feeds
with open("hourglass_report.txt", "w", encoding="utf-8") as f:
    f.write("\x0c\n".join(pages))

# Save as clean printable HTML
html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {
    size: A4 portrait;
    margin: 12mm 15mm;
  }
  body {
    font-family: "DejaVu Sans Mono", "Courier New", monospace;
    font-size: 11px;
    line-height: 1.4;
    color: #111;
  }
  .page {
    page-break-after: always;
    white-space: pre;
    font-family: inherit;
    margin-bottom: 30px;
  }
  .page:last-child {
    page-break-after: avoid;
  }
  h2 {
    font-size: 13px;
    margin: 0 0 8px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #666;
  }
</style>
</head>
<body>
"""

for p in pages:
    html_content += f'<div class="page">\n{p}\n</div>\n'
html_content += "</body></html>"

with open("hourglass_report.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Generated hourglass_report.txt and hourglass_report.html successfully!")