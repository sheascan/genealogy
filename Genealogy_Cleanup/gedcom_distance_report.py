#!/usr/bin/env python3
import sys
import csv
from collections import defaultdict, deque
from gedcom_utils import parse_gedcom, build_graph, resolve_path

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
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_distance_report.py <master.ged> [root_id_or_name]")
        sys.exit(1)
        
    gedcom_file = sys.argv[1]
    search_param = sys.argv[2] if len(sys.argv) > 2 else ""
    
    indis, fams = parse_gedcom(gedcom_file)
    
    # Check if second arg is an exact ID or search string
    root_id = None
    if search_param.startswith('@') and search_param.endswith('@') and search_param in indis:
        root_id = search_param
    elif search_param:
        matches = [i for i in indis.values() if search_param.lower() in i['name'].lower()]
        if not matches:
            print(f"No individuals found matching '{search_param}'.")
            sys.exit(1)
        if len(matches) > 1 and matches[0]['id'] != search_param:
            print(f"\n[*] Multiple matches for '{search_param}'. Re-run with the exact ID:")
            for m in matches[:10]:
                print(f"  {m['id']}: {m['name']} (b. {m['birth'] or '?'})")
            sys.exit(0)
        root_id = matches[0]['id']
    else:
        print("Please provide a root ID (e.g., @I500001@) or name search.")
        sys.exit(1)
        
    adj = build_graph(indis, fams)
    distances = compute_distances(root_id, adj, indis.keys())
    
    dist_counts = defaultdict(int)
    for d in distances.values():
        dist_counts[d] += 1
        
    print("\n" + "="*45)
    print(f" DISTANCE HISTOGRAM FROM: {indis[root_id]['name']} ({root_id})")
    print("="*45)
    print(f"{'Hops / Degrees':<18} | {'Individual Count':<18}")
    print("-" * 45)
    for hop in sorted([k for k in dist_counts if k >= 0]):
        print(f"Hop {hop:<14} | {dist_counts[hop]:<18}")
    if dist_counts.get(-1, 0) > 0:
        print(f"{'DISCONNECTED (-1)':<18} | {dist_counts[-1]:<18}")
    print("="*45)

    out_csv = resolve_path("../GEDCOM_Files").parent / "GEDCOM_Files" / "kinship_review.csv"
    if not out_csv.parent.exists():
        out_csv = "kinship_review.csv"

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Action (KEEP/PRUNE)", "Degree_Hops", "ID", "Name", "Birth_Year", "Death_Year"])
        ranked = sorted(indis.values(), key=lambda x: (0 if distances[x['id']] == -1 else 1, distances[x['id']]), reverse=True)
        for p in ranked:
            d = distances[p['id']]
            d_str = "DISCONNECTED" if d == -1 else str(d)
            writer.writerow(["", d_str, p['id'], p['name'], p['birth'], p['death']])
            
    print(f"\n[+] Manifest exported to: {out_csv}")

if __name__ == '__main__':
    main()