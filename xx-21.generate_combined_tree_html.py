import os
import sys
import html
from gramps.gen.db.utils import make_database
from gramps.gen.lib import Person, Family, EventType

TREE_NAME = "Test_Cousin_Import"
dbdir = os.path.expanduser("~/.gramps/grampsdb")
target_dir = None

for d in os.listdir(dbdir):
    p = os.path.join(dbdir, d)
    name_txt = os.path.join(p, "name.txt")
    if os.path.exists(name_txt):
        with open(name_txt, "r", encoding="utf-8") as f:
            if f.read().strip() == TREE_NAME:
                target_dir = p
                break

if not target_dir:
    candidates = [os.path.join(dbdir, d) for d in os.listdir(dbdir) if os.path.isdir(os.path.join(dbdir, d))]
    if candidates:
        target_dir = max(candidates, key=os.path.getmtime)
        with open(os.path.join(target_dir, "name.txt"), "r", errors="ignore") as f:
            tname = f.read().strip()
        print(f"[*] Connecting to most recently modified database: '{tname}'")
    else:
        print("[-] No Gramps databases found.")
        sys.exit(1)

db = make_database("bsddb")
db.load(target_dir)

print(f"[+] Loaded Gramps Database: {db.get_dbname()}")
print(f"    Total People:   {db.get_number_of_people()}")
print(f"    Total Families: {db.get_number_of_families()}")

def format_date_place(person, ev_type):
    for ev_ref in person.get_event_ref_list():
        ev = db.get_event_from_handle(ev_ref.ref)
        if ev and ev.get_type() == ev_type:
            d = ev.get_date().get_text()
            p_handle = ev.get_place_handle()
            p_name = db.get_place_from_handle(p_handle).get_name().value if p_handle else ""
            parts = [p for p in [d, p_name] if p]
            return " — ".join(parts)
    return ""

def get_person_card_data(p):
    gid = p.get_gramps_id()
    name = p.get_primary_name()
    fn = name.get_first_name()
    sn = name.get_surname()
    full_name = f"{fn} {sn}".strip() or "Unnamed"
    binfo = format_date_place(p, EventType.BIRTH)
    dinfo = format_date_place(p, EventType.DEATH)
    is_new = gid.startswith("_NEW_")
    return {
        "handle": p.get_handle(),
        "gid": gid,
        "name": full_name,
        "birth": binfo,
        "death": dinfo,
        "is_new": is_new
    }

def render_subtree(person_handle, visited):
    if person_handle in visited:
        return ""
    visited.add(person_handle)
    
    p = db.get_person_from_handle(person_handle)
    if not p:
        return ""
    
    pdata = get_person_card_data(p)
    tag_badge = '<span class="badge new-badge">NEW COUSIN ADDITION</span>' if pdata["is_new"] else '<span class="badge base-badge">BASELINE</span>'
    node_cls = "node-new" if pdata["is_new"] else "node-base"
    
    b_html = f'<div><strong>*</strong> {html.escape(pdata["birth"])}</div>' if pdata["birth"] else ''
    d_html = f'<div><strong>+</strong> {html.escape(pdata["death"])}</div>' if pdata["death"] else ''
    
    html_out = f'''
    <div class="person-node {node_cls}">
        <div class="node-header">
            <span class="person-name">{html.escape(pdata['name'])}</span>
            <span class="person-id">{html.escape(pdata['gid'])}</span>
            {tag_badge}
        </div>
        <div class="node-details">
            {b_html}
            {d_html}
        </div>
    '''
    
    fam_handles = p.get_family_list()
    if fam_handles:
        html_out += '<div class="marriages-container">'
        for fhandle in fam_handles:
            fam = db.get_family_from_handle(fhandle)
            if not fam:
                continue
            
            h_h = fam.get_father_handle()
            w_h = fam.get_mother_handle()
            sp_handle = w_h if h_h == person_handle else h_h
            
            spouse_markup = ""
            if sp_handle:
                sp = db.get_person_from_handle(sp_handle)
                if sp:
                    spdata = get_person_card_data(sp)
                    sp_tag = '<span class="badge new-badge">NEW SPOUSE</span>' if spdata["is_new"] else '<span class="badge base-badge">SPOUSE</span>'
                    sp_cls = "node-new" if spdata["is_new"] else "node-base"
                    sp_b = f'<div><strong>*</strong> {html.escape(spdata["birth"])}</div>' if spdata["birth"] else ''
                    sp_d = f'<div><strong>+</strong> {html.escape(spdata["death"])}</div>' if spdata["death"] else ''
                    spouse_markup = f'''
                    <div class="spouse-box {sp_cls}">
                        <div class="spouse-title">Partner / Spouse:</div>
                        <div class="person-name">{html.escape(spdata['name'])} <span class="person-id">{html.escape(spdata['gid'])}</span> {sp_tag}</div>
                        <div class="node-details">
                            {sp_b}
                            {sp_d}
                        </div>
                    </div>
                    '''
            
            children_markup = ""
            ch_refs = fam.get_child_ref_list()
            if ch_refs:
                children_markup += '<div class="children-block">'
                children_markup += f'<div class="children-title">Children ({len(ch_refs)}):</div>'
                children_markup += '<div class="children-list">'
                for cref in ch_refs:
                    children_markup += render_subtree(cref.ref, visited)
                children_markup += '</div></div>'
            
            html_out += f'''
            <div class="family-unit">
                {spouse_markup}
                {children_markup}
            </div>
            '''
        html_out += '</div>'
        
    html_out += '</div>'
    return html_out

# Collect branch roots
all_handles = db.get_person_handles()
root_handles = []

for h in all_handles:
    p = db.get_person_from_handle(h)
    if len(p.get_parent_family_list()) == 0 and len(p.get_family_list()) > 0:
        root_handles.append(h)

priority_roots = []
for h in root_handles:
    p = db.get_person_from_handle(h)
    sn = p.get_primary_name().get_surname().lower()
    if any(k in sn for k in ["mcconigley", "mc conigley", "friel", "heraghty"]):
        priority_roots.append(h)

if not priority_roots:
    priority_roots = root_handles[:10]

visited_global = set()
trees_markup = ""
for rh in priority_roots:
    root_p = db.get_person_from_handle(rh)
    r_name = root_p.get_primary_name().get_name()
    trees_markup += f'<section class="root-tree"><h2>Branch: {html.escape(r_name)}</h2>'
    trees_markup += render_subtree(rh, visited_global)
    trees_markup += '</section>'

db_name = db.get_dbname()
total_people = db.get_number_of_people()
total_families = db.get_number_of_families()
db.close()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Combined Master Genealogy Tree Audit</title>
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #0f172a;
        color: #e2e8f0;
        margin: 0;
        padding: 24px;
    }
    h1 { color: #38bdf8; margin-bottom: 4px; }
    .stats { color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
    .search-box {
        margin-bottom: 24px;
        padding: 10px 16px;
        font-size: 16px;
        border-radius: 8px;
        border: 1px solid #334155;
        background: #1e293b;
        color: #fff;
        width: 320px;
    }
    .root-tree {
        background: #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 32px;
        border: 1px solid #334155;
    }
    h2 { color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 8px; font-size: 18px; }
    .person-node {
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        border-left: 5px solid;
    }
    .node-base {
        background: #1e293b;
        border-left-color: #64748b;
    }
    .node-new {
        background: #064e3b;
        border-left-color: #10b981;
    }
    .node-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .person-name { font-weight: 600; font-size: 16px; }
    .person-id { color: #94a3b8; font-size: 12px; font-family: monospace; }
    .badge {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .new-badge { background: #10b981; color: #022c22; }
    .base-badge { background: #334155; color: #94a3b8; }
    .node-details { font-size: 13px; color: #cbd5e1; line-height: 1.4; }
    .marriages-container { margin-top: 10px; padding-left: 12px; border-left: 2px dashed #475569; }
    .spouse-box {
        background: #182234;
        border: 1px solid #3b82f6;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 8px 0;
    }
    .spouse-box.node-new {
        border-color: #10b981;
        background: #064e3b;
    }
    .spouse-title { font-size: 11px; text-transform: uppercase; color: #38bdf8; font-weight: bold; margin-bottom: 4px; }
    .children-block { margin-top: 12px; }
    .children-title { font-size: 12px; font-weight: bold; color: #cbd5e1; margin-bottom: 6px; }
    .children-list { margin-left: 24px; }
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
        Database: <strong>__DB_NAME__</strong> | 
        Total People: <strong>__TOTAL_PEOPLE__</strong> | 
        Total Families: <strong>__TOTAL_FAMILIES__</strong> | 
        Highlight: <span style="color:#10b981; font-weight:bold;">Emerald = New Additions</span>
    </div>
    <input type="text" id="search" class="search-box" placeholder="Filter by name, ID, or place..." onkeyup="filterTree()">
    __TREES_MARKUP__
</body>
</html>
"""

final_html = HTML_TEMPLATE.replace("__DB_NAME__", str(db_name)) \
                          .replace("__TOTAL_PEOPLE__", str(total_people)) \
                          .replace("__TOTAL_FAMILIES__", str(total_families)) \
                          .replace("__TREES_MARKUP__", trees_markup)

out_path = os.path.expanduser("~/Genealogy/Cousin_Review/combined_tree_audit.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"\n[+] Generated Combined Tree Audit HTML successfully!")
print(f"    Target File: {out_path}")
