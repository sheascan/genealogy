#!/usr/bin/env python3
import sys
from collections import Counter
from gedcom_utils import parse_gedcom, resolve_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 gedcom_surnames.py <file.ged> [min_count_or_filter]")
        print("       e.g.: python3 gedcom_surnames.py McConigley_Original.ged 5")
        print("       e.g.: python3 gedcom_surnames.py McConigley_Original.ged friel")
        sys.exit(1)

    ged_file = resolve_path(sys.argv[1])
    filter_arg = sys.argv[2] if len(sys.argv) > 2 else "1"

    indis, _ = parse_gedcom(ged_file)
    
    counts = Counter()
    for p in indis.values():
        s = p.get('surname', '').strip()
        counts[s if s else "[Unknown / Missing]"] += 1

    print(f"\n[*] Surnames in {ged_file.name} (Total Individuals: {len(indis)})")
    print(f"{'Surname':<30} | {'Count':<8} | {'% of Tree'}")
    print("-" * 55)

    if filter_arg.isdigit():
        min_count = int(filter_arg)
        matching = [item for item in counts.most_common() if item[1] >= min_count]
    else:
        search_term = filter_arg.lower()
        matching = [item for item in counts.most_common() if search_term in item[0].lower()]

    for surn, cnt in matching[:40]:
        pct = (cnt / len(indis)) * 100
        print(f"{surn:<30} | {cnt:<8} | {pct:>5.1f}%")

    if len(matching) > 40:
        print(f"  ... and {len(matching) - 40} more matching surnames.")

if __name__ == '__main__':
    main()