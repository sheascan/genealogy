#Run this one-liner in your terminal to strip or match the namespace dynamically:
echo this one-liner to strip or match the namespace dynamically:
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

    if not os.path.exists(f):
        continue
    try:
        with gzip.open(f, 'rb') as gz:
            tree = ET.parse(gz)
            root = tree.getroot()
            
            # Match any tag ending with 'person' regardless of namespace prefix
            people = [elem for elem in root.iter() if elem.tag.endswith('person') and elem.tag != f"{root.tag.split('}')[0]}}}people"]
            # More direct: find all tags matching local name 'person'
            people = [elem for elem in root.iter() if elem.tag.split('}')[-1] == 'person']
            families = [elem for elem in root.iter() if elem.tag.split('}')[-1] == 'family']
            
            print(f"File: {os.path.basename(f)}")
            print(f"  Root Tag: {root.tag}")
            print(f"  People:   {len(people)}")
            print(f"  Families: {len(families)}")
            print("-" * 50)
    except Exception as e:
        print(f"File: {os.path.basename(f)} (error: {e})")
EOF