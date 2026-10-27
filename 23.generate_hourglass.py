import gzip
import html
import os
import xml.etree.ElementTree as ET

XML_PATH = os.path.expanduser("~/Genealogy/Cousin_Review/combined_tree.gramps")
OUTPUT_HTML = os.path.expanduser("~/Genealogy/Cousin_Review/hourglass_convergence.html")

print(f"[*] Parsing {XML_PATH} for Hourglass view...")
with gzip.open(XML_PATH, "rb") as gz:
    tree = ET.parse(gz)
root = tree.getroot()

ns = ""
if root.tag.startswith("{"):
    ns = root.tag.split("}")[0] + "}"

def get_tag(tag):
    return f"{ns}{tag}"

people = {}
people_el = root.find(get_tag("people"))
if people_el is not None:
    for p in people_el.findall(get_tag("person")):
        h = p.get("handle")
        gid = p.get("id") or ""
        name_node = p.find(get_tag("name"))
        first = ""
        surname = ""
        if name_node is not None:
            fn = name_node.find(get_tag("first"))
            sn = name_node.find(get_tag("surname"))
            first = fn.text if fn is not None and fn.text else ""
            surname = sn.text if sn is not None and sn.text else ""
        full_name = f"{first} {surname}".strip() or "Unnamed"

        is_new = gid.startswith("_NEW_")
        spouse_fams = [r.get("hlink") for r in p.findall(get_tag("parentin"))]
        parent_fams = [r.get("hlink") for r in p.findall(get_tag("childof"))]

        people[h] = {
            "handle": h,
            "gid": gid,
            "name": full_name,
            "is_new": is_new,
            "spouse_families": spouse_fams,
            "parent_families": parent_fams,
        }

families = {}
fams_el = root.find(get_tag("families"))
if fams_el is not None:
    for f in fams_el.findall(get_tag("family")):
        fh = f.get("handle")
        fat = f.find(get_tag("father"))
        mot = f.find(get_tag("mother"))
        fat_h = fat.get("hlink") if fat is not None else None
        mot_h = mot.get("hlink") if mot is not None else None
        children = [c.get("hlink") for c in f.findall(get_tag("childref"))]
        families[fh] = {
            "handle": fh,
            "father": fat_h,
            "mother": mot_h,
            "children": children
        }

# Find Mick Shan McConigley & Margaret Heraghty
mick_handle = None
margaret_handle = None
shared_fam_handle = None

for fh, fam in families.items():
    f_p = people.get(fam["father"], {})
    m_p = people.get(fam["mother"], {})
    fn = f_p.get("name", "").lower()
    mn = m_p.get("name", "").lower()
    if ("mcconigley" in fn and "heraghty" in mn) or ("heraghty" in fn and "mcconigley" in mn):
        mick_handle = fam["father"] if "mcconigley" in fn else fam["mother"]
        margaret_handle = fam["mother"] if "heraghty" in mn else fam["father"]
        shared_fam_handle = fh
        break

if not mick_handle or not margaret_handle:
    print("[-] Could not find McConigley x Heraghty family unit.")
    exit(1)

mick_name = people[mick_handle]["name"]
margaret_name = people[margaret_handle]["name"]
print(f"[+] Found Convergence Pivot: {mick_name} x {margaret_name}")

def build_ancestor_tree(ph, depth=3):
    if not ph or ph not in people or depth == 0:
        return ""
    p = people[ph]
    fat_h, mot_h = None, None
    for pf in p["parent_families"]:
        fam = families.get(pf)
        if fam:
            fat_h = fam.get("father")
            mot_h = fam.get("mother")
            break

    card = f'''
    <div class="ancestor-card">
        <div class="p-name">{html.escape(p["name"])}</div>
        <div class="p-id">{html.escape(p["gid"])}</div>
    </div>
    '''
    if fat_h or mot_h:
        parents_html = '<div class="ancestor-branch">'
        if fat_h:
            parents_html += f'<div class="branch-col"><span class="anc-tag">Father:</span>{build_ancestor_tree(fat_h, depth-1)}</div>'
        if mot_h:
            parents_html += f'<div class="branch-col"><span class="anc-tag">Mother:</span>{build_ancestor_tree(mot_h, depth-1)}</div>'
        parents_html += '</div>'
        return f'<div class="ancestor-unit">{parents_html}{card}</div>'
    return f'<div class="ancestor-unit">{card}</div>'

def render_descendant_node(ph, visited):
    if ph in visited or ph not in people:
        return ""
    visited.add(ph)
    p = people[ph]
    cls = "node-new" if p["is_new"] else "node-base"
    badge = '<span class="badge new-badge">NEW COUSIN ADDITION</span>' if p["is_new"] else '<span class="badge base-badge">BASELINE</span>'

    out = f'''
    <div class="person-node {cls}">
        <div class="node-header">
            <span class="person-name">{html.escape(p["name"])}</span>
            <span class="person-id">{html.escape(p["gid"])}</span>
            {badge}
        </div>
    '''
    if p["spouse_families"]:
        out += '<div class="marriages-container">'
        for fh in p["spouse_families"]:
            fam = families.get(fh)
            if not fam:
                continue
            other_h = fam["mother"] if fam["father"] == ph else fam["father"]
            if other_h and other_h in people:
                sp = people[other_h]
                sp_badge = '<span class="badge new-badge">NEW SPOUSE</span>' if sp["is_new"] else '<span class="badge sp-badge">SPOUSE</span>'
                out += f'''
                <div class="spouse-box">
                    <div class="spouse-header">
                        <span class="spouse-label">PARTNER / SPOUSE:</span>
                        <span class="spouse-name">{html.escape(sp["name"])}</span>
                        <span class="spouse-id">{html.escape(sp["gid"])}</span>
                        {sp_badge}
                    </div>
                '''
            else:
                out += '<div class="spouse-box"><div class="spouse-header"><span class="spouse-label">UNKNOWN PARTNER</span></div>'

            children = fam.get("children", [])
            if children:
                out += f'<div class="children-title">Children ({len(children)}):</div>'
                out += '<div class="children-list">'
                for ch in children:
                    out += render_descendant_node(ch, visited)
                out += '</div>'
            out += '</div>'
        out += '</div>'
    out += '</div>'
    return out

visited_nodes = {mick_handle, margaret_handle}
descendants_html = ""
fam_obj = families.get(shared_fam_handle, {})
ch_list = fam_obj.get("children", [])
for ch in ch_list:
    descendants_html += render_descendant_node(ch, visited_nodes)

paternal_tree = build_ancestor_tree(mick_handle, depth=3)
maternal_tree = build_ancestor_tree(margaret_handle, depth=3)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Hourglass Convergence: McConigley x Heraghty</title>
    <style>
        body {{
            background: #090d16;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        .header {{
            text-align: center;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .header h1 {{ color: #f59e0b; margin: 0 0 8px 0; font-size: 1.8rem; }}
        .header p {{ color: #94a3b8; margin: 0; font-size: 0.95rem; }}
        .ancestry-split {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-bottom: 24px;
        }}
        .pedigree-wing {{
            flex: 1;
            background: rgba(17, 24, 39, 0.7);
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 16px;
        }}
        .wing-title {{
            font-weight: 700;
            font-size: 1.05rem;
            color: #38bdf8;
            border-bottom: 1px dashed #334155;
            padding-bottom: 8px;
            margin-bottom: 12px;
            text-align: center;
        }}
        .ancestor-unit {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}
        .ancestor-branch {{
            display: flex;
            gap: 12px;
            justify-content: space-around;
            width: 100%;
        }}
        .branch-col {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .anc-tag {{ font-size: 0.72rem; color: #f59e0b; font-weight: bold; margin-bottom: 4px; }}
        .ancestor-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px 12px;
            text-align: center;
            min-width: 130px;
        }}
        .ancestor-card .p-name {{ font-weight: 600; font-size: 0.88rem; color: #f1f5f9; }}
        .ancestor-card .p-id {{ font-size: 0.72rem; color: #94a3b8; font-family: monospace; }}
        .knot-container {{
            display: flex;
            justify-content: center;
            margin: 16px 0 32px 0;
        }}
        .knot-card {{
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(16, 185, 129, 0.15));
            border: 2px solid #f59e0b;
            border-radius: 10px;
            padding: 14px 28px;
            text-align: center;
        }}
        .knot-title {{ font-size: 0.75rem; text-transform: uppercase; color: #f59e0b; font-weight: bold; }}
        .knot-names {{ font-size: 1.25rem; font-weight: bold; color: #ffffff; margin-top: 4px; }}
        .descendants-section {{
            background: rgba(17, 24, 39, 0.8);
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 20px;
        }}
        .section-header {{
            font-size: 1.15rem;
            font-weight: bold;
            color: #10b981;
            margin-bottom: 14px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 8px;
        }}
        .person-node {{ border-left: 2px solid #334155; padding-left: 12px; margin: 8px 0; }}
        .node-new {{ border-left-color: #10b981; }}
        .node-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
        .person-name {{ font-weight: 600; font-size: 0.92rem; }}
        .person-id {{ font-size: 0.72rem; color: #94a3b8; font-family: monospace; }}
        .badge {{ font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: 600; }}
        .new-badge {{ background: #064e3b; color: #6ee7b7; border: 1px solid #10b981; }}
        .base-badge {{ background: #1e293b; color: #94a3b8; }}
        .sp-badge {{ background: #172554; color: #93c5fd; }}
        .spouse-box {{
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 6px 10px;
            margin: 4px 0 4px 8px;
        }}
        .spouse-header {{ display: flex; align-items: center; gap: 8px; }}
        .spouse-label {{ font-size: 0.7rem; color: #38bdf8; font-weight: bold; }}
        .spouse-name {{ font-weight: 600; font-size: 0.88rem; }}
        .spouse-id {{ font-size: 0.72rem; color: #94a3b8; font-family: monospace; }}
        .children-title {{ font-size: 0.72rem; color: #94a3b8; margin: 4px 0 2px 4px; }}
        .children-list {{ margin-left: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Hourglass Convergence: McConigley x Heraghty</h1>
        <p>Bi-directional audit tracing dual ancestral root systems into shared descendants</p>
    </div>

    <div class="ancestry-split">
        <div class="pedigree-wing">
            <div class="wing-title">Paternal Ancestry: {html.escape(mick_name)}</div>
            {paternal_tree}
        </div>
        <div class="pedigree-wing">
            <div class="wing-title">Maternal Ancestry: {html.escape(margaret_name)}</div>
            {maternal_tree}
        </div>
    </div>

    <div class="knot-container">
        <div class="knot-card">
            <div class="knot-title">&#10022; Convergence Pivot Union &#10022;</div>
            <div class="knot-names">{html.escape(mick_name)} &times; {html.escape(margaret_name)}</div>
        </div>
    </div>

    <div class="descendants-section">
        <div class="section-header">Shared Progeny &amp; Descendant Branches ({len(ch_list)} Children)</div>
        <div class="descendants-container">
            {descendants_html}
        </div>
    </div>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"[+] Successfully wrote {OUTPUT_HTML}")
