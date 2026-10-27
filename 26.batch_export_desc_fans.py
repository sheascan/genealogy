#!/usr/bin/env python3
"""
Direct Cairo headless batch exporter for Gramps Descendant Fan Charts:
- Proportional Family Spacing with Child Floor (ANGLE_WEIGHT with MIN_FLOOR=3).
- Clean Gen 2 spouse handling (roomy charts keep Joe Byrne, dense Mary suppresses).
- Native SVG Hyperlink Badges:
  Wraps each (+) badge in a standard SVG <a> link with inline hover styles and
  native hash routing, guaranteeing hand cursor and instant navigation.
"""

import os
import re
import json
import math
import itertools
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import cairo

from gramps.gen.utils.callback import Callback
from gramps.gen.dbstate import DbState
from gramps.gui.dbloader import DbLoader
import gramps.gui.widgets.fanchart as fanchart
import gramps.gui.widgets.fanchartdesc as fanchartdesc

DB_DIR = os.path.expanduser("~/.gramps/grampsdb/6adf1de1")
OUT_DIR = os.path.expanduser("~/Genealogy/website")
BRANCH_THRESHOLD = 4
MAX_RING2_CAPACITY = 22

# 1. HARD SUPPRESSION OF OUTER WIREFRAME INDICATOR ARCS
_orig_draw_person = fanchart.FanChartWidget.draw_person
def _clean_draw_person(self, ctx, person, radiusin, radiusout, start_rad, stop_rad,
                       generation, dup, userdata, thick=False,
                       has_moregen_indicator=False, is_central_person=False):
    return _orig_draw_person(self, ctx, person, radiusin, radiusout, start_rad, stop_rad,
                             generation, dup, userdata, thick=thick,
                             has_moregen_indicator=False,
                             is_central_person=is_central_person)
fanchart.FanChartWidget.draw_person = _clean_draw_person

# 2. PROPORTIONAL WEIGHTING WITH GUARANTEED BASELINE FLOOR
MIN_FLOOR = 3.0

def _compute_angles_with_floor(self, start_rad, stop_rad):
    start, portion = start_rad, stop_rad - start_rad
    nr_gen = len(self.gen2people) - 1
    
    gen = 0
    data = self.gen2people[gen][0]
    data[2] = start
    data[3] = portion
    
    for gen in range(0, nr_gen):
        prevpartnerdatahandle = None
        offset = 0
        for data_fam in self.gen2fam[gen]:
            persondata = self.gen2people[gen][data_fam[4]]
            personstart, personslice = persondata[2:4]
            if prevpartnerdatahandle != persondata[0].handle:
                offset = 0
                prevpartnerdatahandle = persondata[0].handle
            
            portion = personslice
            if data_fam[8] == fanchartdesc.COLLAPSED:
                portion = 0
            elif data_fam[8] == fanchartdesc.EXPANDED:
                portion = personslice

            data_fam[2] = personstart + offset
            data_fam[3] = portion
            offset += portion

        prevfamdatahandle = None
        offset = 0
        children = self.gen2people[gen + 1] if gen < nr_gen else []
        
        fam_weights = {}
        for persondata in children:
            fam_idx = persondata[4]
            if fam_idx not in fam_weights:
                fam_weights[fam_idx] = []
            h = persondata[0].handle if persondata[0] else None
            real_cnt = self.handle2desc.get(h, 0)
            fam_weights[fam_idx].append(max(real_cnt, MIN_FLOOR) + 1.0)

        fam_totals = {fidx: sum(wlist) for fidx, wlist in fam_weights.items()}
        fam_child_idx = {}

        for persondata in children:
            parentfamdata = self.gen2fam[gen][persondata[4]]
            famstart = parentfamdata[2]
            famslice = parentfamdata[3]
            fam_idx = persondata[4]

            if prevfamdatahandle != parentfamdata[0].handle:
                offset = 0
                prevfamdatahandle = parentfamdata[0].handle
                fam_child_idx[fam_idx] = 0

            c_idx = fam_child_idx[fam_idx]
            weight = fam_weights[fam_idx][c_idx]
            total_w = fam_totals[fam_idx]
            portion = famslice * (weight / total_w)

            if persondata[7] == fanchartdesc.COLLAPSED:
                portion = 0
            elif persondata[7] == fanchartdesc.EXPANDED:
                portion = famslice

            persondata[2] = famstart + offset
            persondata[3] = portion
            offset += portion
            fam_child_idx[fam_idx] += 1

fanchartdesc.FanChartDescWidget._compute_angles = _compute_angles_with_floor

class MockUIState(Callback):
    def __init__(self):
        super().__init__()
        self.symbols = False
        self.death_symbol = 0
        self.window = None

COLOR_PALETTES = [
    {"start": "#FFFBEA", "end": "#6BAED6", "name": "Classic Slate Blue"},
    {"start": "#FFFFF0", "end": "#55A670", "name": "Emerald Sage"},
    {"start": "#FFF8E7", "end": "#E67E22", "name": "Autumn Amber"},
    {"start": "#FBF7FF", "end": "#8E7CC3", "name": "Heather Lavender"},
    {"start": "#FFF5F5", "end": "#E57373", "name": "Rosewood Coral"},
    {"start": "#F0FDF4", "end": "#0D9488", "name": "Nordic Teal"},
    {"start": "#FFFDF0", "end": "#D97706", "name": "Warm Ochre"},
    {"start": "#F8FAFC", "end": "#475569", "name": "Steel Navy"},
    {"start": "#FEFCE8", "end": "#CA8A04", "name": "Antique Gold"},
]

ROOT_SIBLINGS = [
    {"name": "Mary",    "handle": "1046aa72c9844b74269b51e0843d", "file": "Mary.svg",    "gen": 3},
    {"name": "Mick",    "handle": "1046aa72b96125e88cd2bfd999c1", "file": "Mick.svg",    "gen": 3},
    {"name": "Sean",    "handle": "1046aa72dad83ac757febe625d23", "file": "Sean.svg",    "gen": 3},
    {"name": "Norah",   "handle": "1046aa72c9776bca4dc892edf484", "file": "Norah.svg",   "gen": 3},
    {"name": "Brigid",  "handle": "1046aa72d2853cecfd331b88fe7d", "file": "Brigid.svg",  "gen": 3},
    {"name": "Paddy",   "handle": "1046aa72d27b640e7b9dc6417fc4", "file": "Paddy.svg",   "gen": 3},
    {"name": "Charlie", "handle": "1046aa72db047ef344321cf7edc3", "file": "Charlie.svg", "gen": 3},
    {"name": "Danny",   "handle": "1046aa72dae253e4b91d88a50ba2", "file": "Danny.svg",   "gen": 3},
    {"name": "Tommy",   "handle": "1046aa72dae81c77334ed90c51a6", "file": "Tommy.svg",   "gen": 3},
]

def count_descendants(db, person_handle):
    p = db.get_person_from_handle(person_handle)
    if not p: return 0
    total = 0
    for fhandle in p.get_family_handle_list():
        fam = db.get_family_from_handle(fhandle)
        if not fam: continue
        for cref in fam.get_child_ref_list():
            total += 1 + count_descendants(db, cref.ref)
    return total

def export_svg(dbstate, uistate, sib_name, handle, maxgen, palette, out_path, is_base_sibling=False, branches=None):
    widget = fanchartdesc.FanChartDescWidget(dbstate, uistate)
    widget.set_values(
        root_person_handle=handle,
        maxgen=maxgen,
        flipupsidedownname=True,
        twolinename=True,
        background=fanchart.BACKGROUND_GRAD_GEN,
        fontdescr='Sans Bold 9',
        grad_start=palette["start"],
        grad_end=palette["end"],
        filtr=None,
        alpha_filter=0.2,
        form=fanchart.FORM_CIRCLE,
        angle_algo=1,
        dupcolor="#FFFFFF",
        showid=False
    )
    widget.prepare_background_box(maxgen)
    widget._fill_data_structures()

    ring2_grandchildren = [p for p in widget.gen2people.get(2, []) if p[0] is not None]
    nr_grandchildren = len(ring2_grandchildren)

    if is_base_sibling and maxgen == 3:
        if nr_grandchildren > MAX_RING2_CAPACITY:
            if 2 in widget.gen2fam:
                widget.gen2fam[2] = []
            if maxgen in widget.gen2people:
                widget.gen2people[maxgen] = []
            orig_radius = widget.get_radiusinout_for_gen_pair
            def custom_radius(generation):
                r_in_p, r_out_p, r_in_part, r_out_part = orig_radius(generation)
                if generation == 2:
                    return (r_in_p, r_out_part, r_out_part, r_out_part)
                return (r_in_p, r_out_p, r_in_part, r_out_part)
            widget.get_radiusinout_for_gen_pair = custom_radius
        else:
            if maxgen in widget.gen2people:
                widget.gen2people[maxgen] = [p for p in widget.gen2people[maxgen] if p[0] is not None]
    else:
        if maxgen in widget.gen2people:
            widget.gen2people[maxgen] = [p for p in widget.gen2people[maxgen] if p[0] is not None]

    widthpx = 2 * widget.halfdist()

    person_angle_map = {}
    if 1 in widget.gen2people:
        for pdata in widget.gen2people[1]:
            if pdata[0]:
                person_angle_map[pdata[0].handle] = (pdata[2], pdata[2] + pdata[3])

    surface = cairo.SVGSurface(out_path, widthpx, widthpx)
    ctx = cairo.Context(surface)
    widget.prt_draw(None, ctx, scale=1.0)
    surface.flush()
    surface.finish()

    # INJECT NATIVE SVG HYPERLINKS & BADGES
    if is_base_sibling and branches:
        cx, cy = widthpx / 2.0, widthpx / 2.0
        r_in_p, r_out_p, _, _ = widget.get_radiusinout_for_gen_pair(1)
        badge_r = (r_in_p + r_out_p) / 2.0

        with open(out_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        # Embedded stylesheet directly in the SVG for hover glow and cursor
        badge_style = '''
<defs>
  <style>
    .fan-link { cursor: pointer; }
    .fan-badge circle { transition: transform 0.15s ease, fill 0.15s ease; transform-origin: center; }
    .fan-link:hover .fan-badge circle { fill: #0284c7 !important; stroke: #ffffff !important; stroke-width: 2.5px !important; }
  </style>
</defs>
'''
        overlays = []
        for b in branches:
            h = b["handle"]
            if h in person_angle_map:
                s_rad, e_rad = person_angle_map[h]
                mid_angle = (s_rad + e_rad) / 2.0
                
                bx = cx - badge_r * math.sin(mid_angle)
                by = cy + badge_r * math.cos(mid_angle)
                branch_key = b["file"].replace('.svg', '')
                label = b["label"]

                # Native SVG <a> link with explicit hash target
                badge_svg = f'''
  <a href="#{sib_name}/{branch_key}" xlink:href="#{sib_name}/{branch_key}" data-branch="{sib_name}/{branch_key}" class="fan-link" title="Open {label}">
    <g class="fan-badge">
      <circle cx="{bx:.2f}" cy="{by:.2f}" r="9.5" fill="#0f172a" stroke="#ffffff" stroke-width="1.8" />
      <text x="{bx:.2f}" y="{by:.2f}" text-anchor="middle" dy="3.3" font-family="system-ui, -apple-system, sans-serif" font-size="11" font-weight="900" fill="#ffffff" pointer-events="none">+</text>
    </g>
  </a>'''
                overlays.append(badge_svg)

        if overlays:
            svg_content = svg_content.replace('</svg>', badge_style + '\n' + '\n'.join(overlays) + '\n</svg>')
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    dbstate = DbState()
    uistate = MockUIState()
    loader = DbLoader(dbstate, uistate)

    print(f"Loading Gramps database: {DB_DIR}...")
    loader.read_file(DB_DIR)
    db = dbstate.db

    manifest = {
        "_meta": {
            "parents": "Mick Sean McConigley & Margaret Heraghty",
            "hub_url": "hub.html"
        }
    }
    palette_cycle = itertools.cycle(COLOR_PALETTES)

    sibling_branches = {}
    for sib in ROOT_SIBLINGS:
        sib_name = sib["name"]
        sib_person = db.get_person_from_handle(sib["handle"])
        sibling_branches[sib_name] = []
        
        seen_names = set()
        for fhandle in sib_person.get_family_handle_list():
            fam = db.get_family_from_handle(fhandle)
            if not fam: continue
            for cref in fam.get_child_ref_list():
                child_handle = cref.ref
                desc_count = count_descendants(db, child_handle)
                if desc_count >= BRANCH_THRESHOLD:
                    child = db.get_person_from_handle(child_handle)
                    first_name = child.get_primary_name().get_first_name().strip()
                    clean_name = "".join(c for c in first_name if c.isalnum() or c in (" ", "_")).rstrip()
                    if not clean_name: clean_name = f"Child_{child.get_gramps_id()}"
                    
                    branch_key = clean_name
                    counter = 2
                    while branch_key in seen_names:
                        branch_key = f"{clean_name}_{counter}"
                        counter += 1
                    seen_names.add(branch_key)
                    
                    filename = f"{sib_name}_{branch_key.replace(' ', '_')}.svg"
                    sibling_branches[sib_name].append({
                        "handle": child_handle,
                        "label": f"{clean_name} ({desc_count})",
                        "file": filename,
                        "count": desc_count
                    })

    # Base Sibling Fans
    print("\n=== Generating Base Sibling Fans (with Native <a> Badges) ===")
    for sib in ROOT_SIBLINGS:
        sib_name = sib["name"]
        palette = next(palette_cycle)
        out_svg = os.path.join(OUT_DIR, sib["file"])
        b_list = sibling_branches[sib_name]
        print(f"  -> {sib_name:<8} [{len(b_list)} interactive branches] => {sib['file']}")
        export_svg(dbstate, uistate, sib_name, sib["handle"], sib["gen"], palette, out_svg, is_base_sibling=True, branches=b_list)
        manifest[sib_name] = [
            {"label": b["label"], "file": b["file"], "count": b["count"]}
            for b in b_list
        ]

    # Sub-Branches
    print("\n=== Generating Filtered Sub-Branches ===")
    for sib in ROOT_SIBLINGS:
        sib_name = sib["name"]
        for b in sibling_branches[sib_name]:
            palette = next(palette_cycle)
            out_svg = os.path.join(OUT_DIR, b["file"])
            print(f"  -> {sib_name} > {b['label']:<22} [{palette['name']:<20}] => {b['file']}")
            export_svg(dbstate, uistate, sib_name, b["handle"], 3, palette, out_svg, is_base_sibling=False)

    manifest_path = os.path.join(OUT_DIR, "branches.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    db.close()
    print(f"\nAll SVGs and {manifest_path} regenerated with native links!")

if __name__ == "__main__":
    main()
