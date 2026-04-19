#!/usr/bin/env python3
"""
Rebuild data/inventory.csv from source files.

Run this whenever you download a fresh paints-inventory.xlsx from artistpigments.org.
Manual additions (paints-manual-notes.csv) are merged in automatically.

Usage:
    python3 build_inventory.py
"""

import openpyxl, csv, re
from pathlib import Path

BASE = Path(__file__).parent
XLSX = BASE / 'paints-inventory.xlsx'
MANUAL_CSV = BASE / 'paints-manual-notes.csv'
PIGMENT_INDEX = BASE / 'pigment-index.csv'
OUT = BASE / 'data' / 'inventory.csv'
PALETTES_CSV = BASE / 'data' / 'palettes.csv'
CONTAINERS_CSV = BASE / 'data' / 'containers.csv'
LOADOUTS_CSV = BASE / 'data' / 'loadouts.csv'

def norm_name(s):
    """Normalize color name: strip leading 'CfM ' brand prefix, lowercase, alphanumeric only."""
    s = re.sub(r'^cfm\s+', '', s.strip(), flags=re.IGNORECASE)
    return re.sub(r'[^a-z0-9]', '', s.lower()) if s else ''

BRAND_MAP = {
    'cfmhandmadewatercolors': 'cfm',
    'winsornewtonprofessionalwatercolour20132': 'winsornewton',
    'winsornewtonprofessionalwatercolour2013': 'winsornewton',
    'winsornewtonprofessionalwatercolour': 'winsornewton',
    'winsornewtonprofessionalwatercolours': 'winsornewton',
    'davinciwatercolors': 'davinci',
    'winsornewtoncotwanwatercolours': 'winsornewton',
    'winsornewtoncotwanwatercolors': 'winsornewton',
    'winsornewton': 'winsornewton',
    'holbeinartistswatercolorhwc': 'holbein',
    'holbeinartistswatercolourhwc': 'holbein',
    'holbeinartistsgouache': 'holbein',
    'romanszmalaquarius': 'romanszmal',
    'cfm': 'cfm',
    'davinci': 'davinci',
}

def norm_brand(s):
    n = re.sub(r'[^a-z0-9]', '', s.lower()) if s else ''
    # Try progressively shorter prefixes to catch versioned brand strings
    for key in BRAND_MAP:
        if n.startswith(key) or n == key:
            return BRAND_MAP[key]
    return n


def load_xlsx():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb['Collection']
    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    paints = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        d = dict(zip(headers, row))
        pigments = [d[f'Pigment Code #{i}'] for i in range(1, 11) if d.get(f'Pigment Code #{i}')]
        paints.append({
            'id': d['ID'],
            'color_name': d['Color Name'],
            'brand': d['Brand'],
            'manufacturer_code': re.sub(r'[^\w]', '', str(d['Code'])) if d.get('Code') else '',
            'medium': d['Medium'],
            'transparency': d['Transparency'] or '',
            'granulation': d['Granulation'] or '',
            'staining': d['Staining'] or '',
            'lightfastness': d['Lightfastness'] or '',
            'astm_lightfastness': d['ASTM Lightfastness'] or '',
            'pigments': ', '.join(pigments),
            'single_pigment': 'yes' if len(pigments) == 1 else ('no' if len(pigments) > 1 else ''),
            'hue_category': '',
            'pigment_known': 'yes' if pigments else 'no',
            'alt_names': '',
            'source': 'artistpigments',
            'notes': d['Comment'] or '',
        })
    return paints


def load_manual():
    with open(MANUAL_CSV) as f:
        return list(csv.DictReader(f))


def load_pigment_index():
    """Build a lookup from individual pigment code -> color family.
    Only uses single-pigment rows (no '+') as the canonical family for a pigment.
    """
    lookup = {}
    with open(PIGMENT_INDEX) as f:
        for row in csv.DictReader(f):
            code = row['Color Index Name'].strip()
            family = row['family'].strip()
            if code and family and '+' not in code:
                lookup[code.upper()] = family
    return lookup


def assign_hue_categories(paints, pigment_index):
    """Set hue_category from the pigment index using the first known pigment code."""
    for p in paints:
        if p['hue_category']:
            continue  # already set from manual notes
        if not p['pigments']:
            continue
        first_pigment = p['pigments'].split(',')[0].strip().upper()
        if first_pigment in pigment_index:
            p['hue_category'] = pigment_index[first_pigment]


def merge(paints, manual_rows):
    # Build lookup by (norm_name, norm_brand)
    lookup = {}
    for m in manual_rows:
        key = (norm_name(m['Color name']), norm_brand(m['Brand']))
        lookup[key] = m

    for p in paints:
        key = (norm_name(p['color_name']), norm_brand(p['brand']))
        if key in lookup:
            m = lookup[key]
            p['hue_category'] = m.get('Hue', '')
            p['alt_names'] = m.get('Alternative names/similar names', '')
            # Fill in pigment data from manual if missing
            if not p['pigments'] and m.get('Pigment 1'):
                pigs = [m[f'Pigment {i}'] for i in range(1, 4) if m.get(f'Pigment {i}')]
                p['pigments'] = ', '.join(pigs)
                p['single_pigment'] = 'yes' if len(pigs) == 1 else 'no'
                p['pigment_known'] = 'yes'

    # Add paints that are in manual but not in xlsx (uncatalogued on artistpigments)
    catalogued = {norm_name(p['color_name']) for p in paints}
    extra_id = 1
    added = []
    for m in manual_rows:
        if norm_name(m['Color name']) not in catalogued and norm_brand(m['Brand']) == 'cfm':
            pigs = [m[f'Pigment {i}'] for i in range(1, 4) if m.get(f'Pigment {i}')]
            paints.append({
                'id': f'cfm_x{extra_id:02d}',
                'color_name': m['Color name'],
                'brand': 'CfM Handmade Watercolors',
                'manufacturer_code': '',
                'medium': 'Watercolor',
                'transparency': '',
                'granulation': '',
                'staining': '',
                'lightfastness': '',
                'astm_lightfastness': '',
                'pigments': ', '.join(pigs),
                'single_pigment': 'yes' if len(pigs) == 1 else ('no' if len(pigs) > 1 else ''),
                'hue_category': m.get('Hue', ''),
                'pigment_known': 'yes' if pigs else 'no',
                'alt_names': m.get('Alternative names/similar names', ''),
                'source': 'manual',
                'notes': '',
            })
            added.append(m['Color name'])
            extra_id += 1

    return paints, added


FIELDS = ['id', 'color_name', 'brand', 'manufacturer_code', 'medium', 'hue_category',
          'transparency', 'granulation', 'staining', 'lightfastness', 'astm_lightfastness',
          'pigments', 'single_pigment', 'pigment_known', 'alt_names', 'source', 'notes']


def write_csv(paints):
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader()
        w.writerows(paints)


def check_palette_refs(paints):
    """Warn if palettes or loadouts reference IDs that don't exist."""
    if not PALETTES_CSV.exists():
        return

    inventory_ids = {p['id'] for p in paints}
    container_ids = set()
    if CONTAINERS_CSV.exists():
        with open(CONTAINERS_CSV) as f:
            container_ids = {row['id'] for row in csv.DictReader(f)}

    palette_names = set()
    broken_paints = []
    with open(PALETTES_CSV) as f:
        for row in csv.DictReader(f):
            palette_names.add(row['palette_name'])
            if row['paint_id'] not in inventory_ids:
                broken_paints.append((row['palette_name'], row['paint_id'], row['color_name']))

    broken_loadout_palettes = []
    broken_loadout_containers = []
    if LOADOUTS_CSV.exists():
        with open(LOADOUTS_CSV) as f:
            for row in csv.DictReader(f):
                if row['palette_name'] not in palette_names:
                    broken_loadout_palettes.append(row['palette_name'])
                if row['container_id'] not in container_ids:
                    broken_loadout_containers.append((row['palette_name'], row['container_id']))

    if broken_paints:
        print("WARNING: palette entries with no matching inventory ID:")
        for palette, pid, name in broken_paints:
            print(f"  [{palette}] {pid}  {name}")
    if broken_loadout_palettes:
        print("WARNING: loadouts reference unknown palettes:")
        for name in broken_loadout_palettes:
            print(f"  {name}")
    if broken_loadout_containers:
        print("WARNING: loadouts reference unknown containers:")
        for palette, cid in broken_loadout_containers:
            print(f"  [{palette}] container '{cid}' not in containers.csv")
    if not broken_paints and not broken_loadout_palettes and not broken_loadout_containers:
        print("Palette references OK.")


if __name__ == '__main__':
    paints = load_xlsx()
    manual = load_manual()
    pigment_index = load_pigment_index()
    paints, added = merge(paints, manual)
    assign_hue_categories(paints, pigment_index)
    for p in paints:
        if p['hue_category']:
            p['hue_category'] = p['hue_category'].title()
    write_csv(paints)
    print(f"Wrote {len(paints)} paints to {OUT}")
    if added:
        print(f"Added from manual (not on artistpigments): {', '.join(added)}")
    missing_hue = [p['color_name'] for p in paints if not p['hue_category']]
    print(f"Paints without hue category: {len(missing_hue)}")
    check_palette_refs(paints)
