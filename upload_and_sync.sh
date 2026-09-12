#!/bin/bash
DEPLOY_URL="https://script.google.com/macros/s/AKfycbx5AguEgIVILADoTs8i5a9OSVY1A4Mk-ZsQyEGlSccT0BG86hZLaMsOqthiHE7JmBfjqA/exec"

echo "Uploading and converting sheets in Google Drive..."

for file in family/sheets/*.xlsx; do
    [ -f "$file" ] || continue
    fname=$(basename "$file")
    echo "  -> Sending $fname..."
    
    # Base64 encode and stream directly via POST
    base64 -w 0 "$file" | curl -sL -X POST \
        "$DEPLOY_URL?filename=$fname" \
        -H "Content-Type: text/plain" \
        --data-binary @- > /dev/null
done

echo "Refreshing local mapping.csv..."
curl -sL "$DEPLOY_URL" -o family/sheets/mapping.csv

echo "Done! All sheets converted, formatted, protected, and mapped locally."
