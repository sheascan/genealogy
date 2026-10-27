import os
from gramps.gen.db.utils import make_database

TREE_PATH = "/home/mikemcconigley/.gramps/grampsdb/6aaaa868"
db = make_database("sqlite")
db.load(TREE_PATH)

print("--- Inspecting First 10 People with Multiple Parents ---")
count = 0
for handle in db.iter_person_handles():
    p = db.get_person_from_handle(handle)
    fam_handles = p.get_parent_family_handle_list()
    if len(fam_handles) > 1:
        count += 1
        print(f"\nPerson: {p.get_primary_name().get_name()} ({p.gramps_id})")
        for fh in fam_handles:
            fam = db.get_family_from_handle(fh)
            if fam:
                f_handle = fam.get_father_handle()
                m_handle = fam.get_mother_handle()
                f_name = db.get_person_from_handle(f_handle).get_primary_name().get_name() if f_handle else "None"
                m_name = db.get_person_from_handle(m_handle).get_primary_name().get_name() if m_handle else "None"
                print(f"  -> Family {fam.gramps_id}: Father=[{f_name}], Mother=[{m_name}], Children={len(fam.get_child_ref_list())}")
            else:
                print(f"  -> Broken family pointer: {fh}")
        if count >= 80:
            break

db.close()