#!/usr/bin/env python3
"""
Generate index.html from palette and inventory data.

Run after build_inventory.py to regenerate the HTML view.

Usage:
    python3 build_html.py
"""

import csv
import markdown
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
DATA = BASE / 'data'
NOTES = BASE / 'notes'
OUT = BASE / 'index.html'
OUT_LABELS = BASE / 'labels.html'


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def load_inventory():
    paints = {}
    for row in load_csv(DATA / 'inventory.csv'):
        paints[row['id']] = row
    return paints


def load_palettes():
    """Returns dict of palette_name -> list of rows, in order."""
    palettes = defaultdict(list)
    for row in load_csv(DATA / 'palettes.csv'):
        palettes[row['palette_name']].append(row)
    return palettes


def load_containers():
    containers = {}
    for row in load_csv(DATA / 'containers.csv'):
        containers[row['id']] = row
    return containers


def load_notes():
    """Returns dict of stem -> rendered HTML."""
    notes = {}
    if NOTES.exists():
        for f in sorted(NOTES.glob('*.md')):
            text = f.read_text()
            notes[f.stem] = markdown.markdown(text, extensions=['tables'])
    return notes


def palette_paints_used(palettes):
    """Set of all paint IDs used in any palette."""
    used = set()
    for rows in palettes.values():
        for row in rows:
            used.add(row['paint_id'])
    return used


def render_palette(name, rows, inventory, container):
    """Render a single palette as HTML."""
    # Group by row
    by_row = defaultdict(list)
    for row in rows:
        r = row.get('row') or 'row1'
        by_row[r].append(row)
    for r in by_row:
        by_row[r].sort(key=lambda x: int(x.get('position') or 0))

    container_name = container['name'] if container else ''
    container_slots = container['max_slots'] if container else ''
    slot_count = len(rows)

    html = f'<section class="palette" id="palette-{name}">\n'
    html += f'<h2>{name.replace("-", " ").title()}</h2>\n'
    if container_name:
        html += f'<p class="palette-meta">{container_name} &mdash; {slot_count} of {container_slots} slots</p>\n'

    html += '<div class="pan-grid">\n'
    row_order = {'top': 0, 'row1': 0, 'middle': 1, 'row2': 1, 'bottom': 2, 'row3': 2}
    for row_key in sorted(by_row.keys(), key=lambda r: row_order.get(r, 99)):
        html += f'<div class="pan-row">\n'
        for entry in by_row[row_key]:
            paint = inventory.get(entry['paint_id'], {})
            color_name = paint.get('color_name') or entry.get('color_name') or entry['paint_id']
            brand = paint.get('brand') or ''
            manufacturer_code = paint.get('manufacturer_code') or ''
            pigments = paint.get('pigments') or ''
            notes = entry.get('notes') or ''

            # Shorten brand for display
            brand_short = (brand
                .replace("Winsor & Newton Professional Water Colour [2013-]", "W&N")
                .replace("Holbein Artists' Watercolor (HWC)", "Holbein")
                .replace("Holbein Artists' Gouache", "Holbein")
                .replace("Roman Szmal Aquarius", "Szmal")
                .replace("CfM Handmade Watercolors", "CfM")
                .replace("Da Vinci Watercolors", "Da Vinci")
                .replace("Winsor & Newton Cotman Water Colours", "W&N Cotman"))
            if manufacturer_code:
                brand_short = f'{brand_short} {manufacturer_code}'

            html += '<div class="pan">\n'
            html += f'<div class="pan-name">{color_name}</div>\n'
            html += f'<div class="pan-brand">{brand_short}</div>\n'
            if pigments:
                html += f'<div class="pan-pigments">{pigments}</div>\n'
            if notes:
                html += f'<div class="pan-notes">{notes}</div>\n'
            html += '</div>\n'
        html += '</div>\n'
    html += '</div>\n'
    html += '</section>\n'
    return html


def render_inventory(inventory, used_ids):
    brands = sorted(set(p['brand'] for p in inventory.values()))
    hues = sorted(set(p['hue_category'] for p in inventory.values() if p['hue_category']))

    html = '<section class="inventory" id="inventory">\n'
    html += '<h2>Full Inventory</h2>\n'

    # Filter controls
    html += '''<div class="filters">
  <label>Brand:
    <select id="filter-brand" onchange="applyFilters()">
      <option value="">All</option>\n'''
    for b in brands:
        short = (b.replace("Winsor & Newton Professional Water Colour [2013-]", "W&N")
                  .replace("Holbein Artists' Watercolor (HWC)", "Holbein HWC")
                  .replace("Holbein Artists' Gouache", "Holbein Gouache")
                  .replace("Roman Szmal Aquarius", "Szmal Aquarius")
                  .replace("CfM Handmade Watercolors", "CfM"))
        html += f'      <option value="{b}">{short}</option>\n'
    html += '''    </select>
  </label>
  <label>Hue:
    <select id="filter-hue" onchange="applyFilters()">
      <option value="">All</option>\n'''
    for h in hues:
        html += f'      <option value="{h}">{h}</option>\n'
    html += '''    </select>
  </label>
  <label>
    <input type="checkbox" id="filter-unused" onchange="applyFilters()">
    Not used in any palette
  </label>
</div>\n'''

    # Table
    html += '''<table id="inventory-table">
<thead>
  <tr>
    <th>Color</th>
    <th>Brand</th>
    <th>Hue</th>
    <th>Pigments</th>
    <th>Transparency</th>
    <th>Granulation</th>
    <th>Lightfastness</th>
    <th>In palettes</th>
  </tr>
</thead>
<tbody>\n'''

    # Build palette membership lookup
    palette_rows = load_csv(DATA / 'palettes.csv')
    paint_palettes = defaultdict(list)
    for row in palette_rows:
        paint_palettes[row['paint_id']].append(row['palette_name'])

    for pid, p in sorted(inventory.items(), key=lambda x: x[1]['color_name']):
        unused_class = '' if pid in used_ids else ' unused'
        palettes_str = ', '.join(sorted(set(paint_palettes[pid]))) if pid in paint_palettes else '—'
        brand_short = (p['brand']
            .replace("Winsor & Newton Professional Water Colour [2013-]", "W&N")
            .replace("Holbein Artists' Watercolor (HWC)", "Holbein")
            .replace("Holbein Artists' Gouache", "Holbein")
            .replace("Roman Szmal Aquarius", "Szmal")
            .replace("CfM Handmade Watercolors", "CfM")
            .replace("Da Vinci Watercolors", "Da Vinci"))
        if p.get('manufacturer_code'):
            brand_short = f'{brand_short} {p["manufacturer_code"]}'
        html += f'<tr class="paint-row{unused_class}" data-brand="{p["brand"]}" data-hue="{p["hue_category"]}" data-unused="{"true" if pid not in used_ids else "false"}">\n'
        html += f'  <td>{p["color_name"]}</td>\n'
        html += f'  <td>{brand_short}</td>\n'
        html += f'  <td>{p["hue_category"]}</td>\n'
        html += f'  <td class="pigments">{p["pigments"]}</td>\n'
        html += f'  <td>{p["transparency"]}</td>\n'
        html += f'  <td>{p["granulation"]}</td>\n'
        html += f'  <td>{p["lightfastness"]}</td>\n'
        html += f'  <td>{palettes_str}</td>\n'
        html += '</tr>\n'

    html += '</tbody></table>\n</section>\n'
    return html


CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 14px;
    color: #222;
    background: #f9f7f4;
    padding: 2rem;
    max-width: 1100px;
    margin: 0 auto;
}
h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.2rem; margin-bottom: 0.75rem; border-bottom: 1px solid #ddd; padding-bottom: 0.4rem; }
h3 { font-size: 1rem; margin: 1rem 0 0.4rem; }
nav { margin-bottom: 2.5rem; }
nav a { margin-right: 1rem; color: #666; text-decoration: none; font-size: 0.9rem; }
nav a:hover { color: #222; }
.subtitle { color: #888; font-size: 0.9rem; margin-bottom: 2rem; }
section { margin-bottom: 3rem; }

/* Palette pan grid */
.palette-meta { color: #888; font-size: 0.85rem; margin-bottom: 1rem; }
.pan-grid { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; }
.pan-row { display: flex; gap: 0.5rem; }
.pan {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.6rem 0.75rem;
    width: 160px;
    min-height: 70px;
}
.pan-name { font-weight: 600; font-size: 0.85rem; line-height: 1.3; }
.pan-brand { color: #888; font-size: 0.75rem; margin-top: 0.2rem; }
.pan-pigments { color: #555; font-size: 0.72rem; margin-top: 0.25rem; font-family: monospace; }
.pan-notes { color: #e07030; font-size: 0.72rem; margin-top: 0.25rem; font-style: italic; }

/* Palette notes */
.palette-notes {
    background: white;
    border: 1px solid #e8e4df;
    border-radius: 4px;
    padding: 1.25rem 1.5rem;
    font-size: 0.88rem;
    line-height: 1.7;
    max-width: 720px;
}
.palette-notes h1 { font-size: 1.1rem; margin-bottom: 0.75rem; }
.palette-notes h2 { font-size: 0.95rem; margin-top: 1.25rem; }
.palette-notes h3 { font-size: 0.88rem; }
.palette-notes p { margin-bottom: 0.6rem; }
.palette-notes ul, .palette-notes ol { padding-left: 1.25rem; margin-bottom: 0.6rem; }
.palette-notes li { margin-bottom: 0.3rem; }
.palette-notes table { border-collapse: collapse; width: 100%; margin-bottom: 0.75rem; }
.palette-notes td, .palette-notes th { border: 1px solid #ddd; padding: 0.3rem 0.5rem; font-size: 0.82rem; }
.palette-notes strong { font-weight: 600; }

/* Inventory */
.filters { display: flex; gap: 1.5rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; }
.filters label { font-size: 0.88rem; color: #555; display: flex; align-items: center; gap: 0.4rem; }
.filters select { font-size: 0.85rem; padding: 0.2rem 0.4rem; border: 1px solid #ccc; border-radius: 3px; }
table { width: 100%; border-collapse: collapse; font-size: 0.83rem; background: white; }
thead th { background: #f0ede8; text-align: left; padding: 0.5rem 0.6rem; font-weight: 600; position: sticky; top: 0; }
tbody tr { border-bottom: 1px solid #eee; }
tbody tr:hover { background: #faf8f5; }
td { padding: 0.4rem 0.6rem; vertical-align: top; }
.pigments { font-family: monospace; font-size: 0.78rem; color: #555; }
tr.unused { background: #fffbf5; }
tr.hidden { display: none; }
.unused-badge { display: inline-block; font-size: 0.7rem; background: #f0e8d8; color: #a06020; border-radius: 3px; padding: 0.1rem 0.35rem; margin-left: 0.4rem; }
'''

JS = '''
function applyFilters() {
    const brand = document.getElementById('filter-brand').value;
    const hue = document.getElementById('filter-hue').value;
    const unusedOnly = document.getElementById('filter-unused').checked;
    document.querySelectorAll('.paint-row').forEach(row => {
        const matchBrand = !brand || row.dataset.brand === brand;
        const matchHue = !hue || row.dataset.hue === hue;
        const matchUnused = !unusedOnly || row.dataset.unused === 'true';
        row.classList.toggle('hidden', !(matchBrand && matchHue && matchUnused));
    });
}
'''


def build(inventory, palettes, containers):
    notes = load_notes()
    used_ids = palette_paints_used(palettes)

    palette_order = ['default', 'garden', 'urban-sketch', 'cfm-floral']
    palette_order += [k for k in palettes if k not in palette_order]

    # Nav links
    nav = '<nav>\n'
    for name in palette_order:
        if name in palettes:
            nav += f'  <a href="#palette-{name}">{name.replace("-", " ").title()}</a>\n'
    nav += '  <a href="#inventory">Inventory</a>\n'
    nav += '</nav>\n'

    body = ''
    for name in palette_order:
        if name not in palettes:
            continue
        rows = palettes[name]
        container_id = rows[0].get('container_id', '') if rows else ''
        container = containers.get(container_id)
        body += render_palette(name, rows, inventory, container)

        # Look for matching notes file
        notes_key = f'{name}-palette'
        if notes_key in notes:
            body += f'<div class="palette-notes">{notes[notes_key]}</div>\n'
        body += '\n'

    body += render_inventory(inventory, used_ids)

    # Notes files not matched to a palette
    matched = {f'{n}-palette' for n in palette_order}
    extra_notes = {k: v for k, v in notes.items() if k not in matched}
    if extra_notes:
        body += '<section id="notes">\n<h2>Notes</h2>\n'
        for stem, content in extra_notes.items():
            body += f'<h3>{stem.replace("-", " ").title()}</h3>\n'
            body += f'<div class="palette-notes">{content}</div>\n'
        body += '</section>\n'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Watercolor Palettes</title>
<style>{CSS}</style>
</head>
<body>
<h1>Watercolor Palettes</h1>
<p class="subtitle">{len(inventory)} paints &mdash; {len(palettes)} palettes</p>
{nav}
{body}
<script>{JS}</script>
</body>
</html>'''

    OUT.write_text(html)
    print(f"Wrote {OUT}")
    print(f"  {len(palettes)} palettes, {len(inventory)} paints, {len(used_ids)} used in palettes, {len(inventory) - len(used_ids)} not in any palette")


LABELS_CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: white;
    padding: 10mm;
}
h2 {
    font-size: 9pt;
    font-weight: 600;
    color: #888;
    margin: 6mm 0 3mm;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    break-after: avoid;
}
h2:first-child { margin-top: 0; }
.palette-section {
    margin-bottom: 8mm;
}
.card-row {
    display: flex;
    flex-wrap: wrap;
    gap: 2mm;
    margin-bottom: 2mm;
}
.card {
    width: 30mm;
    height: 19mm;
    border: 0.3pt solid #bbb;
    border-radius: 1mm;
    padding: 1.5mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    page-break-inside: avoid;
}
.card-name {
    font-size: 6.5pt;
    font-weight: 700;
    line-height: 1.25;
}
.card-brand {
    font-size: 5.5pt;
    color: #666;
    line-height: 1.2;
}
.card-pigments {
    font-size: 5pt;
    font-family: monospace;
    color: #444;
    line-height: 1.2;
    margin-top: auto;
}
@media print {
    body { padding: 8mm; }
    h2 { color: #999; }
    .card { border-color: #ccc; }
}
'''


def build_labels(inventory, palettes, containers):
    palette_order = ['default', 'garden', 'urban-sketch', 'cfm-floral']
    palette_order += [k for k in palettes if k not in palette_order]

    body = ''
    for name in palette_order:
        if name not in palettes:
            continue
        rows = palettes[name]
        container_id = rows[0].get('container_id', '') if rows else ''
        container = containers.get(container_id, {})
        container_name = container.get('name', '')

        label = name.replace('-', ' ').title()
        if container_name:
            label += f' — {container_name}'
        body += f'<div class="palette-section">\n<h2>{label}</h2>\n'

        orientation = container.get('pan_orientation', 'portrait')
        if orientation == 'landscape':
            card_style = 'width:30mm;height:19mm;'
        else:
            card_style = 'width:19mm;height:30mm;'

        # Group entries by row, preserving physical order
        by_row = defaultdict(list)
        for entry in rows:
            by_row[entry.get('row') or 'row1'].append(entry)
        for r in by_row:
            by_row[r].sort(key=lambda x: int(x.get('position') or 0))

        row_order = {'top': 0, 'row1': 0, 'middle': 1, 'row2': 1, 'bottom': 2, 'row3': 2}
        for row_key in sorted(by_row.keys(), key=lambda r: row_order.get(r, 99)):
            body += '<div class="card-row">\n'
            for entry in by_row[row_key]:
                paint = inventory.get(entry['paint_id'], {})
                color_name = paint.get('color_name') or entry.get('color_name') or entry['paint_id']
                brand = paint.get('brand') or ''
                manufacturer_code = paint.get('manufacturer_code') or ''
                pigments = paint.get('pigments') or ''

                brand_short = (brand
                    .replace("Winsor & Newton Professional Water Colour [2013-]", "W&N")
                    .replace("Holbein Artists' Watercolor (HWC)", "Holbein")
                    .replace("Holbein Artists' Gouache", "Holbein")
                    .replace("Roman Szmal Aquarius", "Szmal")
                    .replace("CfM Handmade Watercolors", "CfM")
                    .replace("Da Vinci Watercolors", "Da Vinci")
                    .replace("Winsor & Newton Cotman Water Colours", "W&N"))
                if manufacturer_code:
                    brand_short = f'{brand_short} {manufacturer_code}'

                body += f'<div class="card" style="{card_style}">\n'
                body += f'  <div class="card-name">{color_name}</div>\n'
                body += f'  <div class="card-brand">{brand_short}</div>\n'
                if pigments:
                    body += f'  <div class="card-pigments">{pigments}</div>\n'
                body += '</div>\n'
            body += '</div>\n'

        body += '</div>\n'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Palette Labels</title>
<style>{LABELS_CSS}</style>
</head>
<body>
{body}
</body>
</html>'''

    OUT_LABELS.write_text(html)
    total = sum(len(v) for v in palettes.values())
    print(f"Wrote {OUT_LABELS} ({total} labels across {len(palettes)} palettes)")


if __name__ == '__main__':
    inventory = load_inventory()
    palettes = load_palettes()
    containers = load_containers()
    build(inventory, palettes, containers)
    build_labels(inventory, palettes, containers)
