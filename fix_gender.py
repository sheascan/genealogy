import gzip
import xml.etree.ElementTree as ET

input_path = "Rebuilds/baseline_add_cousins_and_theShans.gramps"
output_path = "Rebuilds/baseline_add_cousins_and_theShans_fixed.gramps"

GRAMPS_NS = "http://gramps-project.org/xml/1.7.1/"
ET.register_namespace('', GRAMPS_NS)

FEMALE = {
    "anne", "marie", "ava", "bridget", "kathleen", "gillian", "jessica",
    "hannah", "caitlin", "celia", "dawn", "rebecca", "ellie", "melissa",
    "gail", "sheila", "angela", "maria", "lucy", "amy", "zoe", "clara",
    "maureen", "siobhan", "siobhán", "paula", "michaela", "fiona", "sinead",
    "noreen", "alicia", "margaret", "annie", "mary", "teresa", "anita",
    "laura", "grainne", "ciara", "eimear", "niamh", "martina", "orlagh",
    "aoife", "catherine", "rose", "sarah", "eileen", "mairead", "claire",
    "doireann", "sadhbh", "ariela", "lisa", "carmel", "chloe", "joanne",
    "dominique", "helen", "emma", "sharon", "theresa", "rachael", "sian",
    "jackie", "leah", "megan", "ashleigh", "poppy", "olivia"
}

MALE = {
    "sean", "james", "mike", "michael", "dominic", "warren", "tyler", "ryan",
    "theo", "danny", "charles", "charlie", "john", "patrick", "liam", "seamus",
    "jerry", "alan", "willie", "damien", "martin", "duncan", "rob", "bobby",
    "neil", "gerard", "ronan", "aodhan", "aodhán", "gabriel", "conor", "darragh",
    "odhran", "odhrán", "fiach", "senan", "oisin", "tadhg", "cathal", "jamesy",
    "tommy", "thomas", "simon", "enda", "kevin", "ollie", "steve", "steven",
    "matt", "emmet", "dave", "harry", "fiachra", "conn", "ruadhri", "mark",
    "aaron", "paul", "scott", "colm", "calum", "kyle", "daniel"
}

with gzip.open(input_path, "rb") as f:
    tree = ET.parse(f)
root = tree.getroot()
ns = {"g": GRAMPS_NS}

fixed_count = 0
for p in root.findall(".//g:person", ns):
    g_elem = p.find("g:gender", ns)
    current_gender = g_elem.text if g_elem is not None else "0"
    
    if current_gender in ("0", "Unknown", None):
        first = p.findtext(".//g:first", default="", namespaces=ns).strip().lower()
        first_token = first.split()[0] if first else ""
        
        target = None
        if first_token in FEMALE:
            target = "1"
        elif first_token in MALE:
            target = "2"
            
        if target:
            if g_elem is None:
                g_elem = ET.SubElement(p, f"{{{GRAMPS_NS}}}gender")
            g_elem.text = target
            fixed_count += 1

with gzip.open(output_path, "wb") as f:
    tree.write(f, encoding="utf-8", xml_declaration=True)

print(f"Successfully patched {fixed_count} records with intact namespaces.")
