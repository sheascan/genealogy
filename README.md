# McConigley Genealogy Reunion Hub (November 2026)

Interactive extended hourglass charts and Google Sheet crowdsourcing pipeline.

## Project Structure

```text
Genealogy/
├── cousins.csv                 # Cousin mapping: prefix, focus name & year
├── generate_hourglass_plus.py  # Core GEDCOM parser -> HTML & XLSX generator
├── hourglass_plus.ged          # Master GEDCOM export from Gramps
├── run_all.sh                  # Batch generator for all cousins
├── requirements.txt            # Python environment dependencies
└── family/                     # Deployable Web Root (single folder sync)
    ├── index.html              # Landing directory for family branches
    ├── Mary.html               # Visual branch tree
    ├── Mick.html
    ├── ...
    ├── api/
    │   └── update_sheet.php    # Webhook endpoint for Apps Script
    └── sheets/                 # Collaborative spreadsheet assets
        ├── Mary.xlsx           # Generated template for Drive
        ├── Mary.php            # HTTP redirect stub to live Google Sheet
        ├── ...

[200~# In ~/Genealogy
php -S 0.0.0.0:8080 -t family/~
# In ~/Genealogy
php -S 0.0.0.0:8080 -t family/
# In ~/Genealogy
php -S 0.0.0.0:8080 -t family/
Visit http://localhost:8080/ in your browser.
# genealogy
