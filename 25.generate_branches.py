#!/usr/bin/env python3
"""
Generates both:
1. Root sibling fan charts (2-3 generations, clean legibility).
2. Deep extension sub-branch fan charts.
Also writes branches.json for automatic UI linkage.
"""

import os
import json
import subprocess

TREE_NAME = "McConigley_Tree"  # Your Gramps database name
OUT_DIR = os.path.expanduser("~/Genealogy/website")

# ----------------------------------------------------------------------
# 1. PRIMARY SIBLINGS (ROOT FANS)
# Set gen=2 or gen=3 to ensure names are never culled or blanked.
# Replace the Gramps IDs ('I0001', etc.) with their actual IDs in your tree.
# ----------------------------------------------------------------------
ROOT_SIBLINGS = [
    {"name": "Mary",    "id": "I0001", "file": "Mary.svg",    "gen": 2},
    {"name": "Mick",    "id": "I0002", "file": "Mick.svg",    "gen": 2},
    {"name": "Sean",    "id": "I0003", "file": "Sean.svg",    "gen": 2},
    {"name": "Norah",   "id": "I0004", "file": "Norah.svg",   "gen": 2},  # Unitary fallback handles if no desc
    {"name": "Brigid",  "id": "I0005", "file": "Brigid.svg",  "gen": 2},
    {"name": "Paddy",   "id": "I0006", "file": "Paddy.svg",   "gen": 2},
    {"name": "Charlie", "id": "I0007", "file": "Charlie.svg", "gen": 2},
    {"name": "Danny",   "id": "I0008", "file": "Danny.svg",   "gen": 2},
    {"name": "Tommy",   "id": "I0009", "file": "Tommy.svg",   "gen": 2},
]

# ----------------------------------------------------------------------
# 2. EXTENSION FANS (DEEP SUB-BRANCHES)
# Detailed 3-4 generation charts for prolific branches.
# ----------------------------------------------------------------------
SUB_BRANCHES = {
    "Mary": [
        {"id": "I0045", "label": "Margaret (McAteer)", "file": "Mary_Margaret.svg", "gen": 3},
        {"id": "I0048", "label": "May (McLoughlin)",   "file": "Mary_May.svg",      "gen": 3},
        {"id": "I0050", "label": "Patrick (Friel)",    "file": "Mary_Patrick.svg",  "gen": 3}
    ],
    "Mick": [
        {"id": "I0102", "label": "Mick Jr Branch",     "file": "Mick_MickJr.svg",   "gen": 3},
        {"id": "I0115", "label": "John Branch",        "file": "Mick_John.svg",     "gen": 3}
    ],
    "Tommy": [
        {"id": "I0201", "label": "Tommy Jr Branch",    "file": "Tommy_TommyJr.svg", "gen": 3}
    ]
}

def run_export(tree_name, gramps_id, out_svg_path, generations=2):
    cmd = [
        "gramps",
        "-O", tree_name,
        "-a", "report",
        "-p", f"name=descend_fan,pid={gramps_id},gen={generations},of={out_svg_path}"
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Connecting to Gramps DB '{TREE_NAME}' -> Output: {OUT_DIR}\n")

    # Phase 1: Generate Root Sibling Fans
    print("=== Phase 1: Generating Base Sibling Fans (Clean / Reduced Depth) ===")
    for sib in ROOT_SIBLINGS:
        out_file = os.path.join(OUT_DIR, sib["file"])
        print(f"  -> [{sib['name']}] (PID: {sib['id']}, gen={sib['gen']}) => {sib['file']}")
        run_export(TREE_NAME, sib["id"], out_file, generations=sib["gen"])

    # Phase 2: Generate Extension Sub-Branch Fans
    print("\n=== Phase 2: Generating Deep Extension Fans ===")
    manifest = {}
    for sib_name, branches in SUB_BRANCHES.items():
        manifest[sib_name] = []
        for b in branches:
            out_file = os.path.join(OUT_DIR, b["file"])
            print(f"  -> [{sib_name} Sub] {b['label']} (PID: {b['id']}, gen={b['gen']}) => {b['file']}")
            run_export(TREE_NAME, b["id"], out_file, generations=b["gen"])
            manifest[sib_name].append({
                "label": b["label"],
                "file": b["file"]
            })

    # Phase 3: Write Manifest for index.html
    manifest_path = os.path.join(OUT_DIR, "branches.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nCompleted! Generated root fans, extension fans, and {manifest_path}")

if __name__ == "__main__":
    main()
