#!/usr/bin/env python3
import sys
import csv
import re
from collections import defaultdict, deque
from gedcom_utils import parse_gedcom, build_graph, resolve_path

# Common Irish hypocorisms and name equivalence sets
NAME_SYNONYMS = [
    {"michael", "micheal", "mike", "mick", "mickey", "micky"},
    {"mary", "may", "maisie", "mollie", "marie", "maire"},
    {"patrick", "paddy", "pat", "patsy", "padraig"},
    {"bridget", "biddy", "bridie", "delia", "brid", "bid", "bried"},
    {"seamus", "james", "jim", "jimmy", "seamie"},
    {"catherine", "kate", "katie", "kitty", "katherine"},
    {"denis", "dinny", "dionysius"},
    {"edward", "eddie", "ned"},
    {"margaret", "maggie", "peggy"},
    {"charles", "charlie", "cormac"},
    {"hannah", "johanna", "ann", "annie"},
]

def normalize_str(s):
    return re.sub(r'[^a-z0-9]', '', s.lower()) if s else ''

def forenames_match(g1, g2):
    n1, n2 = normalize_str(g1), normalize_str(g2)
    if not n1 or not n2:
        return False
    if n1 == n2 or n1 in n2 or n2 in n1:
        return True
    for syn_set in NAME_SYNONYMS:
        if any(alias in n1 for alias in syn_set) and any(alias in n2 for alias in syn_set):
            return True
    return False

def surnames_match(s1, s2):
    n1, n2 = normalize_str(s1), normalize_str(s2)
    if not n1 or not n2:
        return False
    # Normalize common Irish prefixes
    for prefix in ['mc', 'mac', 'o']:
        if n1.startswith(prefix): n1 = n1[len(prefix):]
        if n2.startswith(prefix): n2 = n2[len(prefix):]
    return n1 == n2 or n1.startswith(n2) or n2.startswith(n1)

def years_close(y1, y2, tolerance=2):
    if not y1 or not y2:
        return False  # Require birth year for automated scoring
    try:
        return abs(int(y1) - int(y2)) <= tolerance
    except (ValueError, TypeError):
        return False

def compute_distances(root_id, adj, all_ids):
    distances = {}
    queue = deque([(root_id, 0)])
    visited = {root_id}
    while queue:
        curr, dist = queue.popleft()
        distances[curr] = dist
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    for node_id in all_ids:
        if node_id not in distances:
            distances[node_id] = -1
    return distances

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gedcom_suggest_bridges.py <file.ged> <root_id> [year_tolerance]")
        sys.exit(1)

    ged_file = resolve_path(sys.argv[1])
    root_id = sys.argv[2]
    tolerance = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    indis, fams = parse_gedcom(ged_file)
    adj = build_graph(indis, fams)
    distances = compute_distances(root_id, adj, indis.keys())

    connected_ids = [pid for pid, d in distances.items() if d >= 0]
    orphan_ids = [pid for pid, d in distances.items() if d == -1]

    print(f"[*] Analyzing bridges between {len(connected_ids)} connected nodes and {len(orphan_ids)} orphan nodes...")

    # Index connected individuals by birth year for fast candidate lookup
    connected_by_year = defaultdict(list)
    for cid in connected_ids:
        b = indis[cid].get('birth', '')
        if b and b.isdigit():
            connected_by_year[int(b)].append(cid)

    suggestions = []
    for oid in orphan_ids:
        o = indis[oid]
        o_birth = o.get('birth', '')
        if not o_birth or not o_birth.isdigit():
            continue

        target_yr = int(o_birth)
        # Check window +/- tolerance
        candidate_cids = []
        for yr in range(target_yr - tolerance, target_yr + tolerance + 1):
            candidate_cids.extend(connected_by_year.get(yr, []))

        for cid in candidate_cids:
            c = indis[cid]
            if surnames_match(o.get('surname'), c.get('surname')):
                if forenames_match(o.get('given'), c.get('given')):
                    year_diff = abs(target_yr - int(c['birth']))
                    
                    # Context scoring: check if they share a spouse's surname
                    o_spouses = []
                    for fid in o.get('fams', []):
                        if fid in fams:
                            sp_id = fams[fid]['wife'] if fams[fid]['husb'] == oid else fams[fid]['husb']
                            if sp_id and sp_id in indis:
                                o_spouses.append(indis[sp_id].get('surname', ''))

                    c_spouses = []
                    for fid in c.get('fams', []):
                        if fid in fams:
                            sp_id = fams[fid]['wife'] if fams[fid]['husb'] == cid else fams[fid]['husb']
                            if sp_id and sp_id in indis:
                                c_spouses.append(indis[sp_id].get('surname', ''))

                    shared_spouse = any(
                        surnames_match(s1, s2) for s1 in o_spouses for s2 in c_spouses if s1 and s2
                    )

                    confidence = "HIGH (Shared Spouse)" if shared_spouse else ("MEDIUM" if year_diff == 0 else "LOW")

                    suggestions.append({
                        "Confidence": confidence,
                        "Year_Diff": year_diff,
                        "Connected_ID": cid,
                        "Connected_Hop": distances[cid],
                        "Connected_Name": c['name'],
                        "Connected_Birth": c['birth'],
                        "Orphan_ID": oid,
                        "Orphan_Name": o['name'],
                        "Orphan_Birth": o['birth'],
                        "Action_Suggestion": "Merge identical person or re-link family"
                    })

    # Sort suggestions by confidence and smallest year difference
    conf_order = {"HIGH (Shared Spouse)": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda x: (conf_order[x['Confidence']], x['Year_Diff']))

    out_csv = ged_file.parent / "bridge_suggestions.csv"
    fields = [
        "Confidence", "Year_Diff", "Connected_ID", "Connected_Hop", "Connected_Name",
        "Connected_Birth", "Orphan_ID", "Orphan_Name", "Orphan_Birth", "Action_Suggestion"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(suggestions)

    print("\n" + "="*80)
    print(f" BRIDGE SUGGESTIONS SUMMARY (Found: {len(suggestions)})")
    print("="*80)
    for s in suggestions[:20]:
        print(f"[{s['Confidence']:<20}] Hop {s['Connected_Hop']:<2} | {s['Connected_Name']} (b. {s['Connected_Birth']}) <==> {s['Orphan_Name']} (b. {s['Orphan_Birth']})")
    print("="*80)
    print(f"[+] Output written to: {out_csv}\n")

if __name__ == '__main__':
    main()