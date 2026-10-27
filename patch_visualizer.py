path = "22.generate_html_from_xml.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Ensure incoming spouses of existing people don't get selected as independent branch roots
old_root_logic = """    # Find roots (people with no parents in dataset)
    roots = []
    for h, p in people.items():
        if not p["childof"]:
            # Prioritize people with children or spouses
            roots.append(h)"""

new_root_logic = """    # Find roots (people with no parents, excluding incoming spouses of existing members)
    roots = []
    for h, p in people.items():
        if not p["childof"]:
            # If they are just a spouse in a family where the other partner has parents or is a baseline focus, skip as root
            is_secondary_spouse = False
            for fh in p["spouse_families"]:
                fam = families.get(fh)
                if fam:
                    other_h = fam["mother"] if fam["father"] == h else fam["father"]
                    if other_h and other_h in people:
                        other_p = people[other_h]
                        if other_p["childof"] or not other_p["id"].startswith("_NEW_"):
                            is_secondary_spouse = True
                            break
            if not is_secondary_spouse:
                roots.append(h)"""

if old_root_logic in code:
    code = code.replace(old_root_logic, new_root_logic)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("[+] 22.generate_html_from_xml.py patched successfully!")
else:
    print("[!] Target snippet not found. Checking root selection lines...")
