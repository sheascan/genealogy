**Genealogy Pipeline Scripts**

* **`gedcom_utils.py`**
Shared utility library containing common GEDCOM line-by-line parsing, family graph network builders, and automated path resolution between `Genealogy_Cleanup/` and `GEDCOM_Files/`.
* **`gedcom_audit.py`**
Performs an initial integrity scan on a GEDCOM file, reporting total individual and family counts alongside top source citations and custom application tags.


* **`gedcom_detect_duplicates.py`**
Scans the tree for duplicate siblings and parallel married couple branches, calculating subtree weights and generating `duplicates_manifest.csv`.


* **`gedcom_quarantine_duplicates.py`**
Splits identified duplicates out of the primary dataset, creating a clean canonical tree (`mcconigley_canonical.ged`), a preserved sandbox (`mcconigley_quarantine.ged`), and an indexed manifest (`quarantine_catalog.csv`).


* **`gedcom_distance_report.py`**
Calculates kinship network hops from a designated root person, displays a distance distribution histogram, and exports `kinship_review.csv` to flag distant or disconnected lines.


* **`gedcom_find_bridges.py`**
Identifies gateway ancestors and bottleneck connections leading to remote branches beyond a specified hop cutoff to pinpoint where collateral trees attach.


* **`gedcom_tuned_branches.py`**
Separates direct bloodline descendants and their spouses from remote in-law trees, generating `branches_to_cull.csv` while automatically protecting key regional surnames.


* **`gedcom_prune_branches.py`**
Executes the review decisions from `branches_to_cull.csv`, severing confirmed collateral branches into the quarantine file and generating the baseline `mcconigley_final_clean.ged`.


* **`gedcom_stitch.py`**
Selectively restores and reconnects a specific quarantined branch back into the clean master tree using its catalog ID, producing a timestamped file for safe verification.

Script,Generated Output Files,Destination Folder
gedcom_detect_duplicates.py,duplicates_manifest.csv,../GEDCOM_Files/
gedcom_quarantine_duplicates.py,mcconigley_canonical.gedmcconigley_quarantine.gedquarantine_catalog.csv,../GEDCOM_Files/
gedcom_tuned_branches.py,branches_to_cull.csv,../GEDCOM_Files/
gedcom_prune_branches.py,mcconigley_final_clean.gedmcconigley_quarantine.ged (appended),../GEDCOM_Files/
gedcom_stitch.py,mcconigley_restored_<BRANCH>_<TIMESTAMP>.ged,../GEDCOM_Files/
gedcom_distance_report.py,kinship_review.csv,../GEDCOM_Files/

------------------------------------------------------

GEDCOM Cleanup Script Syntax

gedcom_audit.py

Bash
python3 gedcom_audit.py <master.ged>[cite: 9]
Example: python3 gedcom_audit.py mcconigley-family-tree.ged

gedcom_detect_duplicates.py

Bash
python3 gedcom_detect_duplicates.py <master.ged>[cite: 8]
Example: python3 gedcom_detect_duplicates.py mcconigley-family-tree.ged

gedcom_quarantine_duplicates.py

Bash
python3 gedcom_quarantine_duplicates.py <master.ged> <duplicates_manifest.csv>[cite: 3]
Example: python3 gedcom_quarantine_duplicates.py mcconigley-family-tree.ged duplicates_manifest.csv

gedcom_distance_report.py

Bash
python3 gedcom_distance_report.py <master.ged> <root_id_or_name>
Example by ID: python3 gedcom_distance_report.py mcconigley_canonical.ged @I500001@
Example by Name: python3 gedcom_distance_report.py mcconigley_canonical.ged "Mick McConigley"

gedcom_find_bridges.py

Bash
python3 gedcom_find_bridges.py <file.ged> <root_id> [cutoff_hop][cite: 6]
Example (default 8 hops): python3 gedcom_find_bridges.py mcconigley_canonical.ged @I500001@
Example (custom cutoff): python3 gedcom_find_bridges.py mcconigley_canonical.ged @I500001@ 6

gedcom_tuned_branches.py

Bash
python3 gedcom_tuned_branches.py <file.ged> <root_id>[cite: 1]
Example: python3 gedcom_tuned_branches.py mcconigley_canonical.ged @I500001@

gedcom_prune_branches.py

Bash
python3 gedcom_prune_branches.py <canonical.ged> <branches_to_cull.csv>[cite: 4]
Example: python3 gedcom_prune_branches.py mcconigley_canonical.ged branches_to_cull.csv

gedcom_stitch.py

Bash
python3 gedcom_stitch.py <BRANCH_ID> [clean_file.ged] [quarantine_file.ged] [catalog.csv]
Example (using defaults): python3 gedcom_stitch.py BRANCH_005

[cite: 2]

Example (explicit files): python3 gedcom_stitch.py BRANCH_005 mcconigley_final_clean.ged mcconigley_quarantine.ged quarantine_catalog.csv