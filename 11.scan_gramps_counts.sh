# Identify the Latest / Base Tree  - check the date and person count on the recent candidates:
echo 11 Identify the Latest / Base Tree  - check the date and person count on the recent candidates:

python3 - << 'EOF'
import os
import gzip
import xml.etree.ElementTree as ET

files = [
    os.path.expanduser("~/Genealogy/GEDCOM_Files/revised_22sep_fixed.gramps"),
    os.path.expanduser("~/Genealogy/GEDCOM_Files/revised_22Sep.gramps"),
    os.path.expanduser("~/Genealogy/GEDCOM_Files/revised_fixed.gramps"),
    os.path.expanduser("~/Genealogy/GEDCOM_Files/revised_21sep.gramps"),
    os.path.expanduser("~/Genealogy/GEDCOM_Files/export-21Sep-2302.gramps"),
]

for f in files:
    print(f"  Checking file: {f}")

    if os.path.exists(f):
        mtime = os.path.getmtime(f)
        try:
            with gzip.open(f, 'rb') as gz:
                tree = ET.parse(gz)
                root = tree.getroot()
                people = root.findall('people/person')
                print(f"File: {os.path.basename(f)}")
                print(f"  Path: {f}")
                print(f"  People count: {len(people)}")
        except Exception as e:
            print(f"File: {os.path.basename(f)} (error reading: {e})")
        print("-" * 50)
EOF