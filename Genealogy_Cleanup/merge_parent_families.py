import sys
from gramps.gen.db.utils import make_database
from gramps.gen.lib import Family
from gramps.gui.plug import tool

def merge_identical_parent_families(db):
    print("Scanning for individuals with multiple identical parent families...")
    merged_families_count = 0
    fixed_people_count = 0

    with db.transaction("Merge Duplicate Parent Families"):
        # Iterate over all person handles
        for person_handle in db.iter_person_handles():
            person = db.get_person_from_handle(person_handle)
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

            # Check if any parent pair has more than one family record
            for pair, fam_list in parents_map.items():
                if len(fam_list) > 1:
                    primary_fam_handle = fam_list[0]
                    primary_fam = db.get_family_from_handle(primary_fam_handle)

                    for secondary_fam_handle in fam_list[1:]:
                        secondary_fam = db.get_family_from_handle(secondary_fam_handle)
                        if not secondary_fam:
                            continue

                        # Combine children into primary family
                        existing_child_refs = {ref.ref for ref in primary_fam.get_child_ref_list()}
                        for child_ref in secondary_fam.get_child_ref_list():
                            if child_ref.ref not in existing_child_refs:
                                primary_fam.add_child_ref(child_ref)
                                existing_child_refs.add(child_ref.ref)

                        # Combine events
                        existing_events = set(primary_fam.get_event_ref_list())
                        for ev_ref in secondary_fam.get_event_ref_list():
                            if ev_ref not in existing_events:
                                primary_fam.add_event_ref(ev_ref)

                        # Re-point all children in the secondary family to the primary family
                        for child_ref in secondary_fam.get_child_ref_list():
                            child = db.get_person_from_handle(child_ref.ref)
                            if child:
                                child_fam_handles = child.get_parent_family_handle_list()
                                new_handles = [h for h in child_fam_handles if h != secondary_fam_handle]
                                if primary_fam_handle not in new_handles:
                                    new_handles.append(primary_fam_handle)
                                child.set_parent_family_handle_list(new_handles)
                                db.commit_person(child, db.transaction)

                        db.commit_family(primary_fam, db.transaction)
                        db.remove_family(secondary_fam_handle, db.transaction)
                        merged_families_count += 1

                    fixed_people_count += 1

    print(f"Done! Merged {merged_families_count} duplicate families across {fixed_people_count} individuals.")

if __name__ == "__main__":
    # If run via Gramps CLI
    pass