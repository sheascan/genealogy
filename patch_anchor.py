import re

path = "1.anchor_by_generation_slice.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Strengthen is_spouse_entry
old_func = """def is_spouse_entry(name, role):
    n = str(name).strip().lower()
    r = str(role).strip().lower()
    if r.startswith("sp") or r.startswith("ex") or r.startswith("partner"):
        return True
    if re.match(r"^(sp |sp\.|ex |ex\.|ex\.sp|partner)", n):
        return True
    return False"""

new_func = """def is_spouse_entry(name, role):
    n = str(name).strip().lower()
    r = str(role).strip().lower()
    if any(r.startswith(p) for p in ["sp", "ex", "partner"]):
        return True
    return bool(re.match(r"^(sp[\.\s]|sp$|ex[\.\s]|ex\.sp[\.\s]?|partner[\.\s]?)", n))"""

code = code.replace(old_func, new_func)

with open(path, "w", encoding="utf-8") as f:
    f.write(code)

print("[+] 1.anchor_by_generation_slice.py patched successfully.")
