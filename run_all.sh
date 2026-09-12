#!/bin/bash
GEDCOM="McConigley Tree v5.ged"
CSV_CONFIG="cousins.csv"

if [ ! -f "$GEDCOM" ]; then
    echo "Error: $GEDCOM not found!"
    exit 1
fi

if [ ! -f "$CSV_CONFIG" ]; then
    echo "Error: $CSV_CONFIG not found!"
    exit 1
fi

mkdir -p family/sheets family/api

# Remove old non-obscure files to avoid leaks
rm -f family/*.html family/index.html 2>/dev/null || true

echo "Generating tokenized branch charts..."
tail -n +2 "$CSV_CONFIG" | while IFS=',' read -r prefix focus; do
    prefix=$(echo "$prefix" | xargs)
    focus=$(echo "$focus" | xargs)
    
    if [ -n "$prefix" ] && [ -n "$focus" ]; then
        echo "----------------------------------------------------"
        echo "Processing: $prefix -> '$focus'"
        python3 generate_hourglass_plus.py "$GEDCOM" "$focus" "$prefix"
    fi
done

# Block directory listing with blank index.php and .htaccess in web roots
cat << 'PHPBLOCK' > family/index.php
<?php http_response_code(403); exit('403 Forbidden'); ?>
PHPBLOCK
cat << 'PHPBLOCK' > family/sheets/index.php
<?php http_response_code(403); exit('403 Forbidden'); ?>
PHPBLOCK
echo "Options -Indexes" > family/.htaccess
echo "Options -Indexes" > family/sheets/.htaccess

# Create a private, non-indexed admin landing console
ADMIN_CONSOLE="family/admin_console_7f9a.html"
cat << 'ADMIN_HEAD' > "$ADMIN_CONSOLE"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Reunion Admin Console</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; background: #f8fafc; color: #0f172a; }
    .container { max-width: 900px; margin: 0 auto; }
    h1 { margin-bottom: 6px; }
    .subtitle { color: #64748b; margin-top: 0; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-radius: 8px; overflow: hidden; }
    th, td { padding: 12px 16px; font-size: 0.92rem; border-bottom: 1px solid #f1f5f9; }
    th { background: #0f172a; color: #f8fafc; text-align: left; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.6px; }
    tr:hover { background: #f8fafc; }
    a { color: #0284c7; text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; }
    .url-token { font-family: monospace; font-size: 0.84rem; color: #475569; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
    .sheet-link { display: inline-block; font-size: 0.8rem; color: #475569; background: #f1f5f9; padding: 4px 10px; border-radius: 4px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🔒 McConigley Reunion Admin Console</h1>
    <div class="subtitle">Private Overview • Obscured Links for Individual Cousins</div>
    <table>
      <thead>
        <tr>
          <th>Cousin Target</th>
          <th>Secret Share Link (To Email Cousin)</th>
          <th>Worksheet</th>
        </tr>
      </thead>
      <tbody>
ADMIN_HEAD

python3 -c '
import csv, hashlib

salt = "McConigleyReunion2026"
with open("cousins.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if not row or not row[0].strip():
            continue
        pfx = row[0].strip()
        focus = row[1].strip()
        token_src = pfx.lower() + "-" + salt
        token = hashlib.sha256(token_src.encode()).hexdigest()[:8]
        slug = pfx.lower() + "-" + token
        print(f"""        <tr>
          <td><strong>{focus}</strong></td>
          <td><a href="{slug}.html">/{slug}.html</a> <span class="url-token">({pfx})</span></td>
          <td><a class="sheet-link" href="sheets/{slug}.php" target="_blank">✏️ Report changes</a></td>
        </tr>""")
' >> "$ADMIN_CONSOLE"

cat << 'ADMIN_FOOT' >> "$ADMIN_CONSOLE"
      </tbody>
    </table>
  </div>
</body>
</html>
ADMIN_FOOT

echo "----------------------------------------------------"
echo "Done! Secure links and folder protection generated."
echo "Admin overview created at: family/admin_console_7f9a.html"
