#!/usr/bin/env python3
import sys
import csv
from collections import defaultdict, deque, Counter
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

def find_connected_components(disconnected_ids, adj):
    visited = set()
    components = []
    
    for start_node in disconnected_ids:
        if start_node in visited:
            continue
        
        comp = []
        q = deque([start_node])
        visited.add(start_node)
        
        while q:
            curr = q.popleft()
            comp.append(curr)
            for nxt in adj[curr]:
                if nxt in disconnected_ids and nxt not in visited:
                    visited.add(nxt)
                    q.append(nxt)
        components.append(comp)
        
    return components

def analyze_cluster(comp, indis, fams):
    comp_set = set(comp)
    surnames = Counter()
    
    for pid in comp:
        s = indis[pid].get('surname', '').strip()
        if s:
            surnames[s] += 1
            
    # Find candidate roots: individuals with no parents in this component
    roots = []
    for pid in comp:
        famc = indis[pid].get('famc')
        has_parents_in_comp = False
        if famc and famc in fams:
            h = fams[famc].get('husb')
            w = fams[famc].get('wife')
            if (h and h in comp_set) or (w and w in comp_set):
                has_parents_in_comp = True
        if not has_parents_in_comp:
            roots.append(pid)
            
    # Sort roots by birth year if available
    def birth_sort_key(pid):
        b = indis[pid].get('birth', '')
        return int(b) if (b and b.isdigit()) else 9999
        
    roots.sort(key=birth_sort_key)
    primary_root_id = roots[0] if roots else comp[0]
    primary_root = indis[primary_root_id]
    
    # Check if primary root has a spouse in this cluster to present as a founding couple
    couple_label = f"{primary_root['name']} (b. {primary_root.get('birth') or '?'})"
    for fams_id in primary_root.get('fams', []):
        if fams_id in fams:
            sp_id = fams[fams_id]['wife'] if fams[fams_id]['husb'] == primary_root_id else fams[fams_id]['husb']
            if sp_id and sp_id in comp_set:
                sp = indis[sp_id]
                couple_label += f" & {sp['name']} (b. {sp.get('birth') or '?'})"
                break

    top_surnames = ", ".join([f"{s} ({c})" for s, c in surnames.most_common(3)])
    
    return {
        'size': len(comp),
        'root_id': primary_root_id,
        'anchor_couple': couple_label,
        'top_surnames': top_surnames,
        'members': comp
    }

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gedcom_cluster_orphans.py <clean_or_canonical.ged> <root_id>")
        sys.exit(1)
        
    ged_file = resolve_path(sys.argv[1])
    root_id = sys.argv[2]
    
    indis, fams = parse_gedcom(ged_file)
    adj = build_graph(indis, fams)
    distances = compute_distances(root_id, adj, indis.keys())
    
    disconnected = {pid for pid, d in distances.items() if d == -1}
    print(f"\n[*] Total Disconnected Individuals: {len(disconnected)}")
    
    components = find_connected_components(disconnected, adj)
    print(f"[*] Grouped into {len(components)} distinct family clusters.")
    
    cluster_summaries = []
    for comp in components:
        cluster_summaries.append(analyze_cluster(comp, indis, fams))
        
    cluster_summaries.sort(key=lambda x: x['size'], reverse=True)
    
    print("\n" + "="*85)
    print(f"{'Cluster Root / Anchor Couple':<45} | {'Size':<6} | {'Top Surnames'}")
    print("="*85)
    
    for c in cluster_summaries[:25]:
        print(f"{c['anchor_couple'][:45]:<45} | {c['size']:<6} | {c['top_surnames']}")
        
    out_csv = ged_file.parent / "orphan_clusters_review.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Cluster_Size", "Primary_Root_ID", "Anchor_Couple", "Top_Surnames", "Member_IDs"])
        for c in cluster_summaries:
            writer.writerow([c['size'], c['root_id'], c['anchor_couple'], c['top_surnames'], " ".join(c['members'])])
            
    print("="*85)
    print(f"[+] Full cluster manifest exported to: {out_csv}\n")

if __name__ == '__main__':
    main()