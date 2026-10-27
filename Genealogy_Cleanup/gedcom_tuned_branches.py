#!/usr/bin/env python3
import sys
import re
from collections import deque
import csv
from gedcom_utils import parse_gedcom, resolve_path

SURNAME_TARGETS = [
    # Core McConigley cluster
    r'^m[ac]{1,2}c?on[ia]gl',        # McConigley, McConlogue, McGonigle
    r'^m[ac]{1,2}gon[ia]gl',
    r'^m[ac]{1,2}conagh',           # McConaghy
    
    # Original core protection targets
    r'^carr?$',                     # Carr
    r'^kerr?$',                     # Kerr
    r'^dorr?ian$',                  # Dorian, Dorrian
    r'^dorr?en$',                   # Dorren
    r'^blan[ey]{2}$',               # Blaney, Blany

    # Regional & In-Law targets
    r'^boyce$',                     # Boyce
    r'^(o)?boyle$',                 # Boyle, O'Boyle
    r'^(o)?byrne$',                 # Byrne, O'Byrne
    r'^(o)?callaghan$',             # Callaghan, O'Callaghan
    r'^cannon$',                    # Cannon
    r'^chodzeisner$',               # Chodzeisner
    r'^(o)?clear[ey]$',             # Cleary, O'Cleary
    r'^coll$',                      # Coll
    r'^coyl[e]?$',                  # Coyle, Coyl
    r'^dalton$',                    # Dalton
    r'^davitt$',                    # Davitt
    r'^deen[ey]{2}$',               # Deeney, Deeny
    r'^dillon$',                    # Dillon
    r'^diver$',                     # Diver
    r'^(o)?dohert[ey]$',            # Doherty, Dougherty, Docherty
    r'^duffy$',                     # Duffy
    r'^(o)?flynn$',                 # Flynn, O'Flynn
    r'^friel[s]?$',                 # Friel, Friels
    r'^gallagh[ae]r$',              # Gallagher, Gallacher
    r'^gibbons?$',                  # Gibbon, Gibbons
    r'^heraght[ey]$',               # Heraghty, Heraghty
    r'^logue$',                     # Logue
    r'^martin$',                    # Martin
    r'^m[ac]{1,2}at[ee]er$',        # McAteer, MacAteer, Mc Ateer
    r'^m[ac]{1,2}bride$',           # McBride, MacBride, Mc Bride
    r'^m[ac]{1,2}carron$',          # McCarron
    r'^m[ac]{1,2}elwain[e]?$',      # McElwaine, Mc Elwaine
    r'^m[ac]{1,2}elwee$',           # McElwee, Mc Elwee
    r'^m[ac]{1,2}garvey$',          # McGarvey
    r'^m[ac]{1,2}ginle[ey]$',       # McGinley, MacGinley, Mc Ginley
    r'^m[ac]{1,2}kinle[ey]$',       # McKinley
    r'^meenan$',                    # Meenan
    r'^sh[ie]{2}l(d|s|ds)?$',       # Sheils, Shiels, Shields, Sheil
    r'^(o)?sween[ey]{2,3}$',        # Sweeney, Sweeny, O'Sweeney
    r'^begley$',                     # Begley
    r'^(o)?calla[gh]{1,2}an$',       # Callahan, Callaghan, O'Callahan, O'Callaghan
    r'^clinton$',                    # Clinton
    r'^m[ac]{1,2}allister$',         # McAllister, MacAllister, Mc Allister
    r'^m[ac]{1,2}c?onnigl[ey]{2}$',  # McConnigley, McConnigley (double-n variant)
]

def matches_target_surnames(surname):
    if not surname:
        return False
    cleaned = re.sub(r"[^a-zA-Z]", "", surname.lower())
    for pat in SURNAME_TARGETS:
        if re.search(pat, cleaned):
            return True
    return False

def get_bloodline_with_generations(root_id, indis, fams):
    # 1. Trace direct ancestors and record generation step (Gen 0 = root, 1 = parents, etc.)
    ancestor_gen = {root_id: 0}
    q = deque([root_id])
    while q:
        curr = q.popleft()
        g = ancestor_gen[curr]
        famc = indis[curr].get('famc')
        if famc and famc in fams:
            for parent in [fams[famc]['husb'], fams[famc]['wife']]:
                if parent and parent in indis:
                    if parent not in ancestor_gen or ancestor_gen[parent] > g + 1:
                        ancestor_gen[parent] = g + 1
                        q.append(parent)

    # 2. Trace all descendants down from ancestors, tracking the originating ancestor gen
    blood_relatives = set()
    person_gen_origin = {}
    
    # Initialize queue with ancestors
    q = deque()
    for anc, g in ancestor_gen.items():
        blood_relatives.add(anc)
        person_gen_origin[anc] = g
        q.append(anc)

    visited_fams = set()
    while q:
        curr = q.popleft()
        curr_g = person_gen_origin[curr]
        for fams_id in indis[curr].get('fams', []):
            if fams_id in fams and fams_id not in visited_fams:
                visited_fams.add(fams_id)
                for child in fams[fams_id]['children']:
                    if child in indis:
                        if child not in person_gen_origin or person_gen_origin[child] > curr_g:
                            person_gen_origin[child] = curr_g
                        if child not in blood_relatives:
                            blood_relatives.add(child)
                            q.append(child)

    return ancestor_gen, blood_relatives, person_gen_origin

def get_immediate_inlaw_family(spouse_id, indis, fams):
    # Returns parents and siblings of the spouse (1 hop)
    inlaw_kin = set()
    famc = indis[spouse_id].get('famc')
    if famc and famc in fams:
        # Parents
        p1, p2 = fams[famc]['husb'], fams[famc]['wife']
        if p1 and p1 in indis: inlaw_kin.add(p1)
        if p2 and p2 in indis: inlaw_kin.add(p2)
        # Siblings
        for sib in fams[famc]['children']:
            if sib and sib in indis:
                inlaw_kin.add(sib)
    return inlaw_kin

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gedcom_tuned_branches.py <file.ged> <root_id> [max_inlaw_gen]")
        print("       max_inlaw_gen defaults to 2 (protects in-law parents/siblings up to grandparents)")
        sys.exit(1)
        
    ged_file = resolve_path(sys.argv[1])
    root_id = sys.argv[2]
    max_inlaw_gen = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    
    indis, fams = parse_gedcom(ged_file)
    if root_id not in indis:
        print(f"Error: {root_id} not found.")
        sys.exit(1)

    ancestor_gen, blood_relatives, person_gen_origin = get_bloodline_with_generations(root_id, indis, fams)
    
    spouses_of_blood = set()
    expanded_inlaws = set()

    for b in blood_relatives:
        b_gen = person_gen_origin.get(b, 99)
        for fams_id in indis[b].get('fams', []):
            if fams_id in fams:
                h, w = fams[fams_id]['husb'], fams[fams_id]['wife']
                spouse = h if h and h != b else (w if w and w != b else None)
                if spouse and spouse in indis:
                    spouses_of_blood.add(spouse)
                    
                    # If this blood marriage connects at or within max_inlaw_gen (e.g. Gen <= 2)
                    if b_gen <= max_inlaw_gen:
                        expanded_inlaws.update(get_immediate_inlaw_family(spouse, indis, fams))

    core_group = blood_relatives | spouses_of_blood | expanded_inlaws
    extraneous = set(indis.keys()) - core_group

    print("\n" + "="*60)
    print(f" CLASSIFICATION SUMMARY (Max In-Law Gen K={max_inlaw_gen})")
    print("="*60)
    print(f"Direct Ancestors:                  {len(ancestor_gen):>5}")
    print(f"Blood Relatives (all descendants): {len(blood_relatives):>5}")
    print(f"Direct Spouses of Blood Relatives: {len(spouses_of_blood):>5}")
    print(f"In-Law Parents/Siblings (Gen <= {max_inlaw_gen}): {len(expanded_inlaws):>5}")
    print(f"Total Protected Core:              {len(core_group):>5}")
    print(f"Extraneous Branches (Review List): {len(extraneous):>5}")
    print("="*60)

    out_csv = ged_file.parent / "branches_to_cull.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Cull_Decision", "Surname_Flag", "ID", "Surname", "Given_Name", "Birth_Year", "Reason"])
        
        sorted_extraneous = sorted(
            extraneous,
            key=lambda pid: (
                0 if matches_target_surnames(indis[pid]['surname']) else 1,
                indis[pid]['surname'].upper(),
                indis[pid]['given'].upper()
            )
        )
        
        for pid in sorted_extraneous:
            p = indis[pid]
            surn = p['surname']
            is_target = matches_target_surnames(surn)
            decision = "FLAGGED_REVIEW" if is_target else "PRUNE"
            surn_flag = "KEY_SURNAME_MATCH" if is_target else ""
            reason = "Key surname - check link before culling" if is_target else f"In-law line beyond Gen {max_inlaw_gen}"
            writer.writerow([decision, surn_flag, pid, surn, p['given'], p['birth'], reason])

    print(f"[+] Manifest written to: {out_csv}")

if __name__ == '__main__':
    main()