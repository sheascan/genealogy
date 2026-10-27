import os
import sys
from gramps.gen.db.utils import make_database
from gramps.gen.db.txn import DbTxn

TREE_NAME = "McConigley K4 2000"

def find_tree_dir(target_name):
    base_dir = os.path.expanduser("~/.gramps/grampsdb")
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if os.path.isdir(path):
            name_file = os.path.join(path, "name.txt")
            if os.path.isfile(name_file):
                with open(name_file, "r", encoding="utf-8") as f:
                    if f.read().strip() == target_name:
                        return path
    return None

def run_fix():
    dbpath = find_tree_dir(TREE_NAME)
    if not dbpath:
        print(f"Error: Could not locate directory for tree '{TREE_NAME}'")
        return

    print(f"Opening database directly from: {dbpath}")
    
    try:
        db = make_database("sqlite")
        db.load(dbpath)
    except Exception:
        db = make_database("bsddb")
        db.load(dbpath)

    merged_families_count = 0
    fixed_people_count = 0

    print("Scanning for individuals with duplicate identical parent families...")

    with DbTxn("Merge Duplicate Parent Families", db) as trans:
        person_handles = list(db.iter_person_handles())

        for person_handle in person_handles:
            person = db.get_person_from_handle(person_handle)
            if not person:
                continue

            parent_family_handles = person.get_parent_family_handle_list()
            if len(parent_family_handles) <= 1:
                continue

            # Group families by (father_handle, mother_handle)
            parents_map = {}
            for fam_handle in parent_family_handles:
                fam = db.get_family_from_handle(fam_handle)
                if not fam:
                    continue
                pair = (fam.get_father_handle(), fam.get_mother_handle())
                parents_map.setdefault(pair, []).append(fam_handle)

            person_modified = False
            for pair, fam_list in parents_map.items():
                if len(fam_list) > 1:
                    primary_fam_handle = fam_list[0]
                    primary_fam = db.get_family_from_handle(primary_fam_handle)

                    for secondary_fam_handle in fam_list[1:]:
                        secondary_fam = db.get_family_from_handle(secondary_fam_handle)
                        if not secondary_fam:
                            continue

                        # Consolidate child references
                        existing_child_refs = {ref.ref for ref in primary_fam.get_child_ref_list()}
                        for child_ref in secondary_fam.get_child_ref_list():
                            if child_ref.ref not in existing_child_refs:
                                primary_fam.add_child_ref(child_ref)
                                existing_child_refs.add(child_ref.ref)

                        # Consolidate event references
                        existing_events = {ref.ref for ref in primary_fam.get_event_ref_list()}
                        for ev_ref in secondary_fam.get_event_ref_list():
                            if ev_ref.ref not in existing_events:
                                primary_fam.add_event_ref(ev_ref)

                        # Re-point all children attached to duplicate family to the primary family
                        for child_ref in secondary_fam.get_child_ref_list():
                            child = db.get_person_from_handle(child_ref.ref)
                            if child:
                                c_fam_handles = child.get_parent_family_handle_list()
                                new_handles = [h for h in c_fam_handles if h != secondary_fam_handle]
                                if primary_fam_handle not in new_handles:
                                    new_handles.append(primary_fam_handle)
                                child.set_parent_family_handle_list(new_handles)
                                db.commit_person(child, trans)

                        db.commit_family(primary_fam, trans)
                        db.remove_family(secondary_fam_handle, trans)
                        merged_families_count += 1
                        person_modified = True

            if person_modified:
                fixed_people_count += 1

    print(f"Complete: Merged {merged_families_count} duplicate families across {fixed_people_count} individuals.")
    db.close()

if __name__ == "__main__":
    run_fix()