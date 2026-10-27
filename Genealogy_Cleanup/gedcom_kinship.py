#!/usr/bin/env python3
import sys
import re
from collections import defaultdict, deque
import csv

def parse_gedcom(filepath):
    individuals = {}  # id -> {name, birth_year}
    families = {}     # id -> {husb, wife, children: []}
    
    current_rec = None
    rec_type = None
    
    print(f"[*] Parsing GEDCOM: {filepath}")
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            
            # Record start: e.g. 0 @I123@ INDI
            m0 = re.match(r'^0\s+(@[^@]+@)\s+([A-Z_]+)', line_str)
            if m0:
                rec_id, rtype = m0.group(1), m0.group(2)
                rec_type = rtype
                if rtype == 'INDI':
                    current_rec = {'id': rec_id, 'name': 'Unknown', 'birth': ''}
                    individuals[rec_id] = current_rec
                elif rtype == 'FAM':
                    current_rec = {'id': rec_id, 'husb': None, 'wife': None, 'children': []}
                    families[rec_id] = current_rec
                else:
                    current_rec = None
                continue
            
            if not current_rec:
                continue
                
            # Parse individual details
            if rec_type == 'INDI':
                if line_str.startswith('1 NAME '):
                    current_rec['name'] = line_str[7:].replace('/', '').strip()
                elif line_str.startswith('2 DATE ') and not current_rec['birth']:
                    # Extract year if possible
                    m_yr = re.search(r'\b(1[6-9]\d\d|20\d\d)\b', line_str)
                    if m_yr:
                        current_rec['birth'] = m_yr.group(1)
            
            # Parse family relationships
            elif rec_type == 'FAM':
                if line_str.startswith('1 HUSB '):
                    current_rec['husb'] = line_str[7:].strip()
                elif line_str.startswith('1 WIFE '):
                    current_rec['wife'] = line_str[7:].strip()
                elif line_str.startswith('1 CHIL '):
                    current_rec['children'].append(line_str[7:].strip())
                    
    return individuals, families

def build_graph(individuals, families):
    adj = defaultdict(set)
    for fam_id, fam in families.items():
        parents = [p for p in [fam['husb'], fam['wife']] if p and p in individuals]
        children = [c for c in fam['children'] if c and c in individuals]
        
        # Connect spouses
        if len(parents) == 2:
            adj[parents[0]].add(parents[1])
            adj[parents[1]].add(parents[0])
            
        # Connect parent to children
        for p in parents:
            for c in children:
                adj[p].add(c)
                adj[c].add(p)
    return adj

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_kinship.py <file.ged> [search_name]")
        sys.exit(1)
        
    filepath = sys.argv[1]
    search_name = sys.argv[2].lower() if len(sys.argv) > 2 else None
    
    indis, fams = parse_gedcom(filepath)
    adj = build_graph(indis, fams)
    
    # If no search name supplied, list matching candidates or ask for root ID
    if not search_name:
        print("\n[*] To calculate kinship distances, specify a root person name or ID.")
        print("    Example: python3 gedcom_kinship.py mcconigley-family-tree.ged mcconigley")
        return
        
    matches = [i for i in indis.values() if search_name in i['name'].lower()]
    if not matches:
        print(f"No individuals found matching: '{search_name}'")
        return
        
    print(f"\n[*] Found {len(matches)} matching individuals. Select root by ID:")
    for m in matches[:10]:
        print(f"  {m['id']}: {m['name']} (b. {m['birth'] or '?'})")
        
    if len(matches) > 10:
        print(f"  ...and {len(matches) - 10} more.")

if __name__ == '__main__':
    main()