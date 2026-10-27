import re
import os

path = os.path.expanduser("~/Genealogy/22.generate_html_from_xml.py")
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Helper function definitions
helper_code = '''
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
'''

# 2. Inject helper function right above render_node if not already present
if "def render_ancestry_card" not in code:
    code = code.replace("def render_node(p_handle, visited):", helper_code + "\ndef render_node(p_handle, visited):")

# 3. Call render_ancestry_card right after node-header closes
old_header_close = '        </div>\n    \'\'\''
new_header_close = '        </div>\n        {render_ancestry_card(p_handle)}\n    \'\'\''

if old_header_close in code and "{render_ancestry_card" not in code:
    code = code.replace(old_header_close, new_header_close, 1)

# 4. Inject CSS styles into the template
css_styles = """
    .ancestry-details {
        margin: 6px 0 10px 0;
        font-size: 0.82rem;
    }
    .ancestry-details summary {
        cursor: pointer;
        color: #94a3b8;
        font-weight: 500;
        user-select: none;
    }
    .ancestry-details summary:hover {
        color: #38bdf8;
    }
    .ancestry-box {
        margin-top: 6px;
        padding: 8px 12px;
        background: rgba(15, 23, 42, 0.65);
        border-left: 3px solid #f59e0b;
        border-radius: 4px;
        line-height: 1.5;
    }
    .anc-line {
        color: #cbd5e1;
        margin: 3px 0;
    }
    .anc-label {
        color: #f59e0b;
        font-weight: 600;
        margin-right: 4px;
    }
    .anc-id {
        color: #64748b;
        font-family: monospace;
        font-size: 0.78rem;
    }
</style>"""

if "ancestry-details" not in code and "</style>" in code:
    code = code.replace("</style>", css_styles, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("[+] Successfully added collapsible ancestry cards to 22.generate_html_from_xml.py!")
