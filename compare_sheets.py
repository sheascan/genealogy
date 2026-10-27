import csv
import os
import openpyxl

shadow_dir = "family/gsheets/shadow-original"
live_dir = "family/gsheets"
mapping_file = "family/sheets/mapping.csv"

changes = []


def get_sheet_data(file_path):
  wb = openpyxl.load_workbook(file_path, data_only=True)
  sheet = wb.active
  rows = []
  for row in sheet.iter_rows(values_only=True):
    rows.append([str(v) if v is not None else "" for v in row])
  return rows


if os.path.exists(mapping_file):
  with open(mapping_file, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
      slug = row.get("slug")
      shadow_path = os.path.join(shadow_dir, f"{slug}.xlsx")
      live_path = os.path.join(live_dir, f"{slug}.xlsx")

      if os.path.exists(shadow_path) and os.path.exists(live_path):
        try:
          shadow_rows = get_sheet_data(shadow_path)
          live_rows = get_sheet_data(live_path)

          diff_count = 0
          max_rows = max(len(shadow_rows), len(live_rows))
          for r_idx in range(max_rows):
            s_row = shadow_rows[r_idx] if r_idx < len(shadow_rows) else []
            l_row = live_rows[r_idx] if r_idx < len(live_rows) else []
            max_cols = max(len(s_row), len(l_row))
            for c_idx in range(max_cols):
              s_val = s_row[c_idx] if c_idx < len(s_row) else ""
              l_val = l_row[c_idx] if c_idx < len(l_row) else ""
              if s_val != l_val:
                diff_count += 1

          changes.append({"sheet": slug, "modified_cells": diff_count})
        except Exception as e:
          changes.append({"sheet": slug, "modified_cells": f"Error: {e}"})

print(f"{'Sheet Name':<35} | {'Modified Cells':<15}")
print("-" * 55)
for item in changes:
  print(f"{item['sheet']:<35} | {item['modified_cells']:<15}")