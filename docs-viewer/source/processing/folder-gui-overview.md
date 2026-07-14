---
doc_id: folder-gui-overview
title: Folder-Select GUI for Processing Composites
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Folder-Select GUI

> Export meta Timestamp: 2025-08-29 15:43:14 BST What’s included: In-sketch GUI to pick SOURCE and OUTPUT folders; runs permutations pipeline with CSV + Manifest.

## How to Use

1. Run the sketch. Click **Select SOURCE folder…** and choose the folder containing your images.
2. Click **Select OUTPUT folder…** where composites + `manifest.csv` should be saved.
3. Click **START GENERATION**. Progress appears in the status area.

## Notes

- The sketch auto-detects `layer_rules.csv` in your selected SOURCE folder (optional).
- Images are loaded in deterministic (alphanumeric) order to stabilise index ↔ filename mapping.
- Other settings (blend strategy, auto-levels, etc.) are constants at the top of the file; change and re-run as needed.

## Output

- Composites written to your chosen OUTPUT folder with structured filenames.
- `manifest.csv` in OUTPUT records filename, order, strategy, modes, auto_levels, and source_files.

Want toggle controls in the GUI for strategy, auto-levels, and clip percent? I can add on-canvas widgets next.
