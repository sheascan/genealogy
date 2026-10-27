import os
import pandas as pd

CSV_PATH = os.path.expanduser(
    "~/Genealogy/Cousin_Review/extracted_diffs/all_cousin_additions_anchored.csv"
)
HTML_OUT = os.path.expanduser(
    "~/Genealogy/Cousin_Review/extracted_diffs/review_workbench.html"
)

df = pd.read_csv(CSV_PATH).fillna("")

branches = sorted(df["Sibling_Branch"].unique())

html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Cousin Additions Review Workbench</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f8f9fa; color: #212529; }
  h1 { margin-bottom: 5px; }
  .tabs { display: flex; gap: 8px; margin-bottom: 15px; border-bottom: 2px solid #dee2e6; padding-bottom: 8px; flex-wrap: wrap; }
  .tab-btn { padding: 8px 16px; border: 1px solid #ced4da; background: white; border-radius: 4px; cursor: pointer; font-weight: 600; }
  .tab-btn.active { background: #0d6efd; color: white; border-color: #0d6efd; }
  .panel { display: none; background: white; padding: 15px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .panel.active { display: block; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 8px 12px; border-bottom: 1px solid #dee2e6; text-align: left; }
  th { background: #f1f3f5; font-weight: 600; }
  tr:hover { background: #f8f9fa; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge-child { background: #d1e7dd; color: #0f5132; }
  .badge-parent { background: #cff4fc; color: #055160; }
  .badge-warn { background: #fff3cd; color: #664d03; }
</style>
</head>
<body>
<h1>Cousin Additions Review Workbench</h1>
<p style="color: #6c757d;">Inspect newly anchored individuals grouped by sibling branch before committal to Gramps.</p>

<div class="tabs">
"""

for i, b in enumerate(branches):
  count = len(df[df["Sibling_Branch"] == b])
  active_cls = "active" if i == 0 else ""
  name_short = b.split("-")[0].capitalize()
  html += f'<button class="tab-btn {active_cls}" onclick="openTab(\'{b}\')">{name_short} ({count})</button>\n'

html += "</div>\n"

for i, b in enumerate(branches):
  active_cls = "active" if i == 0 else ""
  sub = df[df["Sibling_Branch"] == b]
  html += f'<div id="{b}" class="panel {active_cls}">\n'
  html += f"<h3>Branch: {b} ({len(sub)} additions)</h3>\n"
  html += """<table>
    <thead>
      <tr>
        <th>Row</th>
        <th>Person Name</th>
        <th>Generation Col</th>
        <th>Inferred Relationship</th>
        <th>Anchor Person (Gramps ID)</th>
        <th>Dates / Places</th>
      </tr>
    </thead>
    <tbody>\n"""

  for _, r in sub.iterrows():
    rel = r.get("Relation", "")
    badge = (
        "badge-child"
        if "Child" in rel
        else ("badge-warn" if "UNRESOLVED" in str(r) else "badge-parent")
    )

    # Gather extra details if present
    dates = []
    for c in ["Birth Date", "Birth Place", "Death Date", "Death Place"]:
      if c in r and r[c]:
        dates.append(f"{c}: {r[c]}")
    extra_txt = " | ".join(dates)

    html += f"""      <tr>
        <td>{r.get('Sheet_Row', '')}</td>
        <td><strong>{r.get('Identified_Name', '')}</strong></td>
        <td>{r.get('Generation_Col', '')}</td>
        <td><span class="badge {badge}">{rel}</span></td>
        <td>{r.get('Anchor_Name', '')} (<code>{r.get('Anchor_Gramps_ID', '')}</code>)</td>
        <td style="color: #6c757d;">{extra_txt}</td>
      </tr>\n"""

  html += "</tbody></table></div>\n"

html += """
<script>
function openTab(id) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById(id).classList.add('active');
}
</script>
</body>
</html>
"""

with open(HTML_OUT, "w") as f:
  f.write(html)

print(f"Generated review page: {HTML_OUT}")