#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict, deque

# Centralized path resolution: checks CWD first, then ../GEDCOM_Files/
def resolve_path(filepath, base_dir="../GEDCOM_Files"):
    p = Path(filepath)
    if p.is_file():
        return p
    fallback = Path(base_dir) / p.name
    if fallback.is_file():
        return fallback
    return p  # Return original if neither exists so caller can handle error

def extract_names(raw_name_val):
    raw_name_val = raw_name_val.strip()
    m = re.search(r'/([^/]+)/', raw_name_val)
    if m:
        surname = m.group(1).strip()
        given = re.sub(r'/[^/]+/', '', raw_name_val).strip()
    else:
        parts = raw_name_val.split()
        surname = parts[-1] if parts else ''
        given = ' '.join(parts[:-1]) if len(parts) > 1 else ''
    display = f"{given} {surname}".strip() if surname else raw_name_val.replace('/', '')
    return given, surname, display

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower()) if text else ''

def parse_gedcom(filepath):
    resolved = resolve_path(filepath)
    indis = {}
    fams = {}
    with open(resolved, 'r', encoding='utf-8', errors='replace') as f:
        curr, rtype = None, None
        for line in f:
            line_str = line.strip()
            if not line_str: 
                continue
            m0 = re.match(r'^0\s+(@[^@]+@)\s+([A-Z_]+)', line_str)
            if m0:
                rid, rtype = m0.group(1), m0.group(2)
                if rtype == 'INDI':
                    curr = {'id': rid, 'given': '', 'surname': '', 'name': 'Unknown', 
                            'birth': '', 'death': '', 'famc': None, 'fams': [], 
                            '_in_birt': False, '_in_deat': False}
                    indis[rid] = curr
                elif rtype == 'FAM':
                    curr = {'id': rid, 'husb': None, 'wife': None, 'children': []}
                    fams[rid] = curr
                else: 
                    curr = None
                continue

            if not curr: 
                continue

            if rtype == 'INDI':
                if line_str.startswith('1 NAME '):
                    g, s, full = extract_names(line_str[7:])
                    curr['given'] = g
                    curr['surname'] = s
                    curr['name'] = full
                elif line_str.startswith('2 SURN ') and not curr['surname']:
                    curr['surname'] = line_str[7:].strip()
                elif line_str.startswith('1 BIRT'):
                    curr['_in_birt'] = True
                    curr['_in_deat'] = False
                elif line_str.startswith('1 DEAT'):
                    curr['_in_birt'] = False
                    curr['_in_deat'] = True
                elif line_str.startswith('2 DATE '):
                    m_yr = re.search(r'\b(1[6-9]\d\d|20\d\d)\b', line_str)
                    if m_yr:
                        if curr['_in_birt'] or not curr['birth']:
                            curr['birth'] = m_yr.group(1)
                        elif curr['_in_deat']:
                            curr['death'] = m_yr.group(1)
                elif line_str.startswith('1 FAMC '):
                    curr['famc'] = line_str[7:].strip()
                elif line_str.startswith('1 FAMS '):
                    curr['fams'].append(line_str[7:].strip())
            elif rtype == 'FAM':
                if line_str.startswith('1 HUSB '): 
                    curr['husb'] = line_str[7:].strip()
                elif line_str.startswith('1 WIFE '): 
                    curr['wife'] = line_str[7:].strip()
                elif line_str.startswith('1 CHIL '): 
                    curr['children'].append(line_str[7:].strip())
    return indis, fams

def load_gedcom_raw_records(filepath):
    resolved = resolve_path(filepath)
    header_lines = []
    records = {}
    trailer = ["0 TRLR\n"]
    current_id, current_lines = None, []
    in_header = True

    with open(resolved, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('0 HEAD'):
                in_header = True
                current_lines = [line]
                continue
            m0 = re.match(r'^0\s+(@[^@]+@)\s+([A-Z_]+)', line)
            if m0:
                if in_header:
                    header_lines = list(current_lines)
                    in_header = False
                elif current_id:
                    records[current_id] = current_lines
                current_id = m0.group(1)
                current_lines = [line]
            elif line.startswith('0 TRLR'):
                if current_id:
                    records[current_id] = current_lines
                    current_id = None
                break
            else:
                current_lines.append(line)
                
    if current_id and current_id not in records:
        records[current_id] = current_lines
    return header_lines, records, trailer

def build_graph(indis, fams):
    adj = defaultdict(set)
    for fam in fams.values():
        parents = [p for p in [fam['husb'], fam['wife']] if p and p in indis]
        children = [c for c in fam['children'] if c and c in indis]
        if len(parents) == 2:
            adj[parents[0]].add(parents[1])
            adj[parents[1]].add(parents[0])
        for p in parents:
            for c in children:
                adj[p].add(c)
                adj[c].add(p)
    return adj