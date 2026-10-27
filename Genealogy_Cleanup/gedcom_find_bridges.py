#!/usr/bin/env python3
import sys
from collections import defaultdict, deque
from gedcom_utils import parse_gedcom, build_graph, resolve_path

def get_shortest_paths(root_id, adj):
    dist = {root_id: 0}
    parent = {root_id: None}
    q = deque([root_id])
    while q:
        curr = q.popleft()
        d = dist[curr]
        for nxt in adj[curr]:
            if nxt not in dist:
                dist[nxt] = d + 1
                parent[nxt] = curr
                q.append(nxt)
    return dist, parent

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gedcom_find_bridges.py <file.ged> <root_id> [cutoff_hop]")
        sys.exit(1)
        
    cutoff = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    ged_file = resolve_path(sys.argv[1])
    root_id = sys.argv[2]
    
    indis, fams = parse_gedcom(ged_file)
    adj = build_graph(indis, fams)
    dist, parent = get_shortest_paths(root_id, adj)

    gateway_counts = defaultdict(list)
    for pid, d in dist.items():
        if d >= cutoff:
            curr = pid
            while dist[curr] >= cutoff:
                curr = parent[curr]
            gateway_counts[curr].append(pid)

    print(f"\n[*] Major Branch Gateways leading to individuals >= {cutoff} hops away:")
    print(f"{'Gateway ID':<12} | {'Hop':<4} | {'Subtree Count':<14} | {'Name'}")
    print("-" * 75)
    
    sorted_gateways = sorted(gateway_counts.items(), key=lambda x: len(x[1]), reverse=True)
    for gw, members in sorted_gateways[:15]:
        p = indis.get(gw, {'name': 'Unknown', 'birth': ''})
        print(f"{gw:<12} | {dist[gw]:<4} | {len(members):<14} | {p['name']} (b. {p.get('birth','?')})")

if __name__ == '__main__':
    main()