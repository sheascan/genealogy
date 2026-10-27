import os
import gzip
import xml.etree.ElementTree as ET
import html

_base_dir = os.path.expanduser("~/Genealogy/Cousin_Review")
gramps_path = os.path.join(_base_dir, "combined_tree.gramps")
OUT_HTML = os.path.join(_base_dir, "combined_tree_audit.html")

print(f"[*] Reading gzipped Gramps XML: {gramps_path}...")
with gzip.open(gramps_path, "rb") as gz:
    tree = ET.parse(gz)

root = tree.getroot()

# Extract XML namespace if present
ns = ""
if root.tag.startswith("{"):
    ns = root.tag.split("}")[0] + "}"

def get_tag(tag):
    return f"{ns}{tag}"

# Helper to find direct children with namespace
def find_child(node, tag):
    return node.find(get_tag(tag))

def find_all_children(node, tag):
    return node.findall(get_tag(tag))

# Locate <people> and <families> containers
people_container = find_child(root, "people")
families_container = find_child(root, "families")

people = {}
if people_container is not None:
    for p in find_all_children(people_container, "person"):
        handle = p.get("handle")
        gid = p.get("id")
        
        fn, sn = "", ""
        name_node = find_child(p, "name")
        if name_node is not None:
            first_node = find_child(name_node, "first")
            if first_node is not None and first_node.text:
                fn = first_node.text
            surname_node = find_child(name_node, "surname")
            if surname_node is not None and surname_node.text:
                sn = surname_node.text
                
        people[handle] = {
            "handle": handle,
            "gid": gid,
            "name": f"{fn} {sn}".strip() or "Unnamed",
            "is_new": gid.startswith("_NEW_") or "NEW" in gid,
            "parent_families": [],
            "spouse_families": []
        }

families = {}
if families_container is not None:
    for f in find_all_children(families_container, "family"):
        fhandle = f.get("handle")
        father_ref = find_child(f, "father")
        mother_ref = find_child(f, "mother")
        f_h = father_ref.get("hlink") if father_ref is not None else None
        m_h = mother_ref.get("hlink") if mother_ref is not None else None
        
        ch_handles = [c.get("hlink") for c in find_all_children(f, "childref")]
        
        families[fhandle] = {
            "father": f_h,
            "mother": m_h,
            "children": ch_handles
        }
        
        if f_h and f_h in people:
            people[f_h]["spouse_families"].append(fhandle)
        if m_h and m_h in people:
            people[m_h]["spouse_families"].append(fhandle)
        for c_h in ch_handles:
            if c_h in people:
                people[c_h]["parent_families"].append(fhandle)

print(f"[+] Successfully loaded {len(people)} people and {len(families)} families from Gramps XML!")


def get_parent_handles(ph):
    p = people.get(ph)
    if not p or not p.get("parent_families"):
        return None, None
    for fh in p["parent_families"]:
        fam = families.get(fh)
        if fam:
            return fam.get("father"), fam.get("mother")
    return None, None

def render_ancestry_card(p_handle):
    fat_h, mot_h = get_parent_handles(p_handle)
    if not fat_h and not mot_h:
        return ""
    
    lines = []
    # Father line
    if fat_h and fat_h in people:
        f_p = people[fat_h]
        ff_h, fm_h = get_parent_handles(fat_h)
        grand = []
        if ff_h and ff_h in people: grand.append(people[ff_h]["name"])
        if fm_h and fm_h in people: grand.append(people[fm_h]["name"])
        grand_txt = f" (Parents: {' & '.join(grand)})" if grand else ""
        gid_val = f_p.get("gid", f_p.get("gramps_id", ""))
        lines.append(f'<div class="anc-line"><span class="anc-label">Paternal:</span> <strong>{html.escape(f_p["name"])}</strong> <span class="anc-id">{html.escape(gid_val)}</span>{html.escape(grand_txt)}</div>')
    
    # Mother line
    if mot_h and mot_h in people:
        m_p = people[mot_h]
        mf_h, mm_h = get_parent_handles(mot_h)
        grand = []
        if mf_h and mf_h in people: grand.append(people[mf_h]["name"])
        if mm_h and mm_h in people: grand.append(people[mm_h]["name"])
        grand_txt = f" (Parents: {' & '.join(grand)})" if grand else ""
        gid_val = m_p.get("gid", m_p.get("gramps_id", ""))
        lines.append(f'<div class="anc-line"><span class="anc-label">Maternal:</span> <strong>{html.escape(m_p["name"])}</strong> <span class="anc-id">{html.escape(gid_val)}</span>{html.escape(grand_txt)}</div>')

    return f"""
        <details class="ancestry-details">
            <summary>Ancestry &#9662;</summary>
            <div class="ancestry-box">
                {''.join(lines)}
            </div>
        </details>
    """

def render_node(p_handle, visited):
    if p_handle in visited:
        return ""
    visited.add(p_handle)
    
    p = people.get(p_handle)
    if not p:
        return ""
    
    cls = "node-new" if p["is_new"] else "node-base"
    badge = '<span class="badge new-badge">NEW COUSIN ADDITION</span>' if p["is_new"] else '<span class="badge base-badge">BASELINE</span>'
    
    out = f'''
    <div class="person-node {cls}">
        <div class="node-header">
            <span class="person-name">{html.escape(p["name"])}</span>
            <span class="person-id">{html.escape(p["gid"])}</span>
            {badge}
        </div>
        {render_ancestry_card(p_handle)}
    '''
    
    if p["spouse_families"]:
        out += '<div class="marriages-container">'
        for fhandle in p["spouse_families"]:
            fam = families.get(fhandle)
            if not fam:
                continue
            
            sp_handle = fam["mother"] if fam["father"] == p_handle else fam["father"]
            sp = people.get(sp_handle)
            
            if sp:
                sp_cls = "node-new" if sp["is_new"] else "node-base"
                sp_badge = '<span class="badge new-badge">NEW SPOUSE</span>' if sp["is_new"] else '<span class="badge base-badge">SPOUSE</span>'
                out += f'''
                <div class="spouse-box {sp_cls}">
                    <div class="spouse-title">Partner / Spouse:</div>
                    <div class="person-name">{html.escape(sp["name"])} <span class="person-id">{html.escape(sp["gid"])}</span> {sp_badge}</div>
                </div>
                '''
            
            if fam["children"]:
                out += f'<div class="children-block"><div class="children-title">Children ({len(fam["children"])}):</div><div class="children-list">'
                for c_handle in fam["children"]:
                    out += render_node(c_handle, visited)
                out += '</div></div>'
                
        out += '</div>'
    out += '</div>'
    return out

# Pick branch roots (exclude incoming spouses of established members)
def is_genuine_root(h, p):
    if len(p["parent_families"]) != 0 or len(p["spouse_families"]) == 0:
        return False
    # If this person is a spouse to someone who has parents or is a baseline member, do not treat as root
    for fh in p["spouse_families"]:
        fam = families.get(fh)
        if fam:
            other_h = fam["mother"] if fam["father"] == h else fam["father"]
            if other_h and other_h in people:
                other_p = people[other_h]
                other_id = other_p.get("gramps_id", other_p.get("id", ""))
                if len(other_p["parent_families"]) > 0 or not other_id.startswith("_NEW_"):
                    return False
    return True

root_handles = [h for h, p in people.items() if is_genuine_root(h, p)]
priority_roots = [h for h in root_handles if any(k in people[h]["name"].lower() for k in ["mcconigley", "mc conigley", "friel", "heraghty"])]

if not priority_roots:
    priority_roots = root_handles[:20]

visited = set()
trees_markup = ""
for rh in priority_roots:
    trees_markup += f'<section class="root-tree"><h2>Branch: {html.escape(people[rh]["name"])}</h2>'
    trees_markup += render_node(rh, visited)
    trees_markup += '</section>'

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Combined Master Genealogy Tree Audit</title>
<style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
    h1 { color: #38bdf8; margin-bottom: 4px; }
    .stats { color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
    .search-box { margin-bottom: 24px; padding: 10px 16px; font-size: 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #fff; width: 340px; }
    .root-tree { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 32px; border: 1px solid #334155; }
    h2 { color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 8px; font-size: 18px; }
    .person-node { border-radius: 8px; padding: 10px 14px; margin: 8px 0; border-left: 5px solid; }
    .node-base { background: #1e293b; border-left-color: #64748b; }
    .node-new { background: #064e3b; border-left-color: #10b981; }
    .node-header { display: flex; align-items: center; gap: 12px; }
    .person-name { font-weight: 600; font-size: 15px; }
    .person-id { color: #94a3b8; font-size: 12px; font-family: monospace; }
    .badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 9999px; text-transform: uppercase; }
    .new-badge { background: #10b981; color: #022c22; }
    .base-badge { background: #334155; color: #94a3b8; }
    .marriages-container { margin-top: 8px; padding-left: 12px; border-left: 2px dashed #475569; }
    .spouse-box { background: #182234; border: 1px solid #3b82f6; border-radius: 6px; padding: 6px 10px; margin: 6px 0; }
    .spouse-box.node-new { border-color: #10b981; background: #064e3b; }
    .spouse-title { font-size: 11px; text-transform: uppercase; color: #38bdf8; font-weight: bold; }
    .children-block { margin-top: 8px; }
    .children-title { font-size: 12px; font-weight: bold; color: #cbd5e1; margin-bottom: 4px; }
    .children-list { margin-left: 20px; }
</style>
<script>
function filterTree() {
    let q = document.getElementById("search").value.toLowerCase();
    let nodes = document.querySelectorAll(".person-node, .spouse-box");
    nodes.forEach(n => {
        let text = n.innerText.toLowerCase();
        n.style.opacity = (q === "" || text.includes(q)) ? "1" : "0.2";
    });
}
</script>
</head>
<body>
    <h1>Combined Family Tree Audit</h1>
    <div class="stats">
        Total People: <strong>__TOTAL_P__</strong> | Total Families: <strong>__TOTAL_F__</strong> | 
        <span style="color:#10b981; font-weight:bold;">Emerald = New Additions</span>
    </div>
    <input type="text" id="search" class="search-box" placeholder="Filter by name, ID..." onkeyup="filterTree()">
    __MARKUP__
</body>
</html>
"""

html_out = HTML_TEMPLATE.replace("__TOTAL_P__", str(len(people))) \
                        .replace("__TOTAL_F__", str(len(families))) \
                        .replace("__MARKUP__", trees_markup)

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"[+] Audit HTML generated successfully: {OUT_HTML}")
