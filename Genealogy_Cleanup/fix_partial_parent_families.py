import os
import sys
from gramps.gen.db.utils import make_database
from gramps.gen.db.txn import DbTxn

TREE_PATH = "/home/mikemcconigley/.gramps/grampsdb/6aaaa868"

def safe_get_family(db, handle):
    if not handle or not db.has_family_handle(handle):
        return None
    try:
        return db.get_family_from_handle(handle)
    except Exception:
        return None

def merge_families(db, trans, keep_fam, drop_fam):
    keep_handle = keep_fam.get_handle()
    drop_handle = drop_fam.get_handle()

    # Consolidate children
    keep_child_refs = {ref.ref for ref in keep_fam.get_child_ref_list()}
    for c_ref in drop_fam.get_child_ref_list():
        if c_ref.ref not in keep_child_refs:
            keep_fam.add_child_ref(c_ref)
            keep_child_refs.add(c_ref.ref)

        # Repoint child
        if db.has_person_handle(c_ref.ref):
            child_obj = db.get_person_from_handle(c_ref.ref)
            c_fams = [h for h in child_obj.get_parent_family_handle_list() if h != drop_handle]
            if keep_handle not in c_fams:
                c_fams.append(keep_handle)
            child_obj.set_parent_family_handle_list(c_fams)
            db.commit_person(child_obj, trans)

    # Consolidate events
    keep_events = {ref.ref for ref in keep_fam.get_event_ref_list()}
    for ev in drop_fam.get_event_ref_list():
        if ev.ref not in keep_events:
            keep_fam.add_event_ref(ev)

    db.commit_family(keep_fam, trans)
    db.remove_family(drop_handle, trans)

def run_cleanup():
    print(f"Opening database: {TREE_PATH}")
    try:
        db = make_database("sqlite")
        db.load(TREE_PATH)
    except Exception:
        db = make_database("bsddb")
        db.load(TREE_PATH)

    merged_count = 0
    empty_stubs_removed = 0

    with DbTxn("Consolidate Duplicate and Stub Families", db) as trans:
        person_handles = list(db.iter_person_handles())

        for p_handle in person_handles:
            if not db.has_person_handle(p_handle):
                continue
            person = db.get_person_from_handle(p_handle)
            fam_handles = person.get_parent_family_handle_list()

            # 1. Clean identical handles in the same list & prune deleted
            valid_handles = []
            for fh in fam_handles:
                if fh not in valid_handles and db.has_family_handle(fh):
                    valid_handles.append(fh)
            if valid_handles != fam_handles:
                person.set_parent_family_handle_list(valid_handles)
                db.commit_person(person, trans)
                fam_handles = valid_handles

            if len(fam_handles) <= 1:
                continue

            families = [safe_get_family(db, h) for h in fam_handles]
            families = [f for f in families if f is not None]

            # 2. Sweep out pure empty stubs (None, None) if another family exists
            non_empty = [f for f in families if f.get_father_handle() or f.get_mother_handle()]
            empty = [f for f in families if not f.get_father_handle() and not f.get_mother_handle()]

            if non_empty and empty:
                target_keep = non_empty[0]
                for ef in empty:
                    merge_families(db, trans, target_keep, ef)
                    empty_stubs_removed += 1
                families = [f for f in non_empty if db.has_family_handle(f.get_handle())]

            if len(families) <= 1:
                continue

            # 3. Compare remaining pairs
            i = 0
            while i < len(families):
                j = i + 1
                while j < len(families):
                    f1 = safe_get_family(db, families[i].get_handle())
                    f2 = safe_get_family(db, families[j].get_handle())

                    if not f1 or not f2:
                        j += 1
                        continue

                    fa1, mo1 = f1.get_father_handle(), f1.get_mother_handle()
                    fa2, mo2 = f2.get_father_handle(), f2.get_mother_handle()

                    keep_fam, drop_fam = None, None

                    # Identical parents (Both Father & Mother match)
                    if fa1 == fa2 and mo1 == mo2 and (fa1 or mo1):
                        keep_fam, drop_fam = f1, f2
                    # Same Father, one Mother known, one unknown
                    elif fa1 and fa1 == fa2:
                        if mo1 and not mo2:
                            keep_fam, drop_fam = f1, f2
                        elif mo2 and not mo1:
                            keep_fam, drop_fam = f2, f1
                    # Same Mother, one Father known, one unknown
                    elif mo1 and mo1 == mo2:
                        if fa1 and not fa2:
                            keep_fam, drop_fam = f1, f2
                        elif fa2 and not fa1:
                            keep_fam, drop_fam = f2, f1

                    if keep_fam and drop_fam:
                        merge_families(db, trans, keep_fam, drop_fam)
                        merged_count += 1
                        families.pop(j)
                    else:
                        j += 1
                i += 1

    print(f"\nExecution Summary:")
    print(f" * Empty (None, None) stub families eliminated: {empty_stubs_removed}")
    print(f" * Identical and partial parent families merged: {merged_count}")
    db.close()

if __name__ == "__main__":
    run_cleanup()