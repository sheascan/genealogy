#!/usr/bin/env python3
"""
Automates generation of sub-branch SVGs and manifests for McConigley Atlas.
"""
import os
import json
import subprocess
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState

TREE_NAME = "McConigley_Tree" # Replace with exact tree name in Gramps
OUT_DIR = os.path.expanduser("~/Genealogy/website")
MIN_DESCENDANTS_FOR_SUBFAN = 5  # Trigger threshold for generating a dedicated fan

def get_descendant_count(db, person_handle):
    count = 0
    person = db.get_person_from_handle(person_handle)
    for fam_handle in person.get_family_list():
        fam = db.get_family_from_handle(fam_handle)
        for child_ref in fam.get_child_ref_list():
            count += 1 + get_descendant_count(db, child_ref.ref)
    return count

def run_export(tree_name, gramps_id, out_svg_path, generations=3):
    cmd = [
        "gramps",
        "-O", tree_name,
        "-a", "report",
        "-p", f"name=descend_fan,pid={gramps_id},gen={generations},of={out_svg_path}"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    dbstate = DbState()
    # Read database directly to find primary sibling nodes and their children
    print(f"Scanning Gramps database: {TREE_NAME}...")
    
    # Alternatively: define the target Gramps Person IDs (or Gramps IDs like I0001)
    # in a lightweight map if you want curated sub-fans:
    targets = {
        "Mary": [
            {"id": "I0045", "label": "Margaret (McAteer)", "file": "Mary_Margaret.svg"},
            {"id": "I0048", "label": "May (McLoughlin)", "file": "Mary_May.svg"},
            {"id": "I0050", "label": "Patrick (Friel)", "file": "Mary_Patrick.svg"}
        ],
        "Mick": [
            {"id": "I0102", "label": "Mick Jr Branch", "file": "Mick_MickJr.svg"},
            {"id": "I0115", "label": "John Branch", "file": "Mick_John.svg"}
        ],
        "Tommy": [
            {"id": "I0201", "label": "Tommy Jr Branch", "file": "Tommy_TommyJr.svg"}
        ]
    }

    manifest = {}

    for sib_name, branches in targets.items():
        manifest[sib_name] = []
        for b in branches:
            out_file = os.path.join(OUT_DIR, b["file"])
            print(f"Generating SVG for {b['label']} -> {b['file']}...")
            run_export(TREE_NAME, b["id"], out_file, generations=3)
            manifest[sib_name].append({
                "label": b["label"],
                "file": b["file"]
            })

    # Save manifest for the webpage
    manifest_path = os.path.join(OUT_DIR, "branches.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Export complete. Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()