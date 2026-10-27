#!/usr/bin/env python3
import sys
from pathlib import Path
from collections import Counter, defaultdict
import re

def resolve_path(arg_path: str) -> Path:
    p = Path(arg_path)
    if not p.exists():
        fallback = Path(__file__).resolve().parent.parent / "GEDCOM_Files" / arg_path
        if fallback.exists():
            return fallback
    return p

def extract_year(date_str: str) -> str:
    match = re.search(r'\b(1\d{3}|20\d{2})\b', date_str)
    return match.group(1) if match else "Unknown"

def audit_gedcom(filepath: Path, max_people_per_source: int = 5):
    print(f"[*] Reading {filepath}...")

    indi_count = 0
    fam_count = 0
    custom_tags = Counter()
    
    # Data stores
    indi_names = {}        # { '@I001@': 'Patrick McConigley' }
    indi_births = {}       # { '@I001@': '1884' }
    source_titles = {}     # { '@S500002@': 'Census of Ireland 1901' }
    source_to_indis = defaultdict(list)  # { '@S500002@': ['@I001@', ...] }

    current_id = None
    current_type = None
    in_birt = False

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue

            # Record Level 0: 0 @ID@ INDI / FAM / SOUR
            if line_str.startswith("0 "):
                in_birt = False
                tokens = line_str.split(" ", 2)
                if len(tokens) >= 3 and tokens[1].startswith("@"):
                    current_id = tokens[1]
                    current_type = tokens[2]
                    if current_type == "INDI":
                        indi_count += 1
                        indi_names[current_id] = "Unknown"
                        indi_births[current_id] = "Unknown"
                    elif current_type == "FAM":
                        fam_count += 1
                else:
                    current_id = None
                    current_type = None
                continue

            # Track Birth context under INDI
            if current_type == "INDI":
                if line_str == "1 BIRT":
                    in_birt = True
                    continue
                elif line_str.startswith("1 ") and not line_str.startswith("1 BIRT"):
                    in_birt = False

                if line_str.startswith("1 NAME "):
                    raw = line_str[7:].strip()
                    indi_names[current_id] = re.sub(r"/", "", raw).strip()

                elif in_birt and line_str.startswith("2 DATE "):
                    indi_births[current_id] = extract_year(line_str[7:].strip())

            # Source titles under SOUR
            elif current_type == "SOUR":
                if line_str.startswith("1 TITL ") or line_str.startswith("1 ABBR "):
                    if current_id not in source_titles:
                        source_titles[current_id] = line_str[7:].strip()

            # Cross-reference source citations under INDI
            parts = line_str.split(" ", 2)
            if len(parts) >= 2:
                tag = parts[1]
                if tag.startswith("_"):
                    custom_tags[tag] += 1
                elif tag == "SOUR" and len(parts) >= 3 and parts[2].startswith("@"):
                    src_ref = parts[2]
                    if current_type == "INDI" and current_id:
                        if current_id not in source_to_indis[src_ref]:
                            source_to_indis[src_ref].append(current_id)

    print("\n--- GEDCOM SUMMARY ---")
    print(f"Total Individuals (INDI): {indi_count}")
    print(f"Total Families (FAM):     {fam_count}")

    print("\n--- TOP CUSTOM / MYHERITAGE TAGS ---")
    for tag, count in custom_tags.most_common(5):
        print(f"  {tag:<22}: {count}")

    print("\n--- TOP SOURCES WITH ASSOCIATED INDIVIDUALS ---")
    # Rank sources by number of referenced individuals
    sorted_sources = sorted(source_to_indis.items(), key=lambda x: len(x[1]), reverse=True)

    for src_id, indis in sorted_sources[:10]:
        title = source_titles.get(src_id, "Unknown Title")
        if len(title) > 65:
            title = title[:62] + "..."
        print(f"\n[{src_id}] {title} ({len(indis)} individuals):")
        
        for indi_id in indis[:max_people_per_source]:
            name = indi_names.get(indi_id, "Unknown")
            byear = indi_births.get(indi_id, "Unknown")
            print(f"    - {indi_id:<8} {name:<28} (b. {byear})")
        
        remaining = len(indis) - max_people_per_source
        if remaining > 0:
            print(f"      ... and {remaining} more individuals")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_audit.py <path_to_gedcom>")
        sys.exit(1)

    target_path = resolve_path(sys.argv[1])
    if not target_path.exists():
        print(f"Error: File not found: {sys.argv[1]}")
        sys.exit(1)

    audit_gedcom(target_path)