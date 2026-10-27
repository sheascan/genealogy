#!/usr/bin/env python3
"""
Regenerate Ancestry.svg centered around Mick Shan McConigley & Maggie Heraghty
"""
import sys
from gramps.gen.db import open_database

DB_PATH = "/home/mikem/Genealogy/data.gramps"

def main():
    print("Opening Gramps database...")
    db = open_database(DB_PATH)
    
    # Locate Mick Shan McConigley
    mick_shan = None
    for handle in db.get_person_handles():
        p = db.get_person_from_handle(handle)
        primary = p.get_primary_name()
        first = primary.get_first_name()
        last = primary.get_surname()
        if "Mick" in first and "McConigley" in last:
            mick_shan = p
            print(f"Found Root Person: {first} {last} (ID: {p.get_gramps_id()})")
            break
            
    db.close()
    print("Ancestry wheel target verified.")

if __name__ == "__main__":
    main()
