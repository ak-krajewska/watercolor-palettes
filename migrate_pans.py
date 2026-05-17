#!/usr/bin/env python3
"""
One-shot: populate the pans table from existing palettes + loadouts.

For every (palette, paint) row in `palettes`, create one pan:
  - container_id from the palette's loadout (NULL if the palette is unloaded)
  - row and position copied from the palettes entry

Pan IDs are sequential `p001`, `p002`, ... in (palette_name, row, position) order.

Idempotent: exits without changes if pans already has rows. Re-running after the
initial migration requires manual intervention (the pans table is hand-curated
from this point on).
"""

import sqlite3
from pathlib import Path

DB = Path(__file__).parent / 'data' / 'paints.db'


def main():
    conn = sqlite3.connect(DB)
    conn.execute('PRAGMA foreign_keys = ON')

    existing = conn.execute('SELECT COUNT(*) FROM pans').fetchone()[0]
    if existing:
        print(f"pans already has {existing} rows -- skipping migration")
        conn.close()
        return

    loadouts = dict(conn.execute('SELECT palette_name, container_id FROM loadouts'))

    rows = conn.execute(
        'SELECT palette_name, paint_id, row, position FROM palettes '
        'ORDER BY palette_name, position'
    ).fetchall()

    inserts = []
    for i, (palette_name, paint_id, row, position) in enumerate(rows, start=1):
        pan_id = f'p{i:03d}'
        container_id = loadouts.get(palette_name)  # None for unloaded palettes
        inserts.append((pan_id, paint_id, container_id, row, position))

    conn.executemany(
        'INSERT INTO pans (id, paint_id, container_id, row, position) VALUES (?, ?, ?, ?, ?)',
        inserts
    )
    conn.commit()

    total = conn.execute('SELECT COUNT(*) FROM pans').fetchone()[0]
    with_container = conn.execute('SELECT COUNT(*) FROM pans WHERE container_id IS NOT NULL').fetchone()[0]
    loose = total - with_container
    print(f"Created {total} pans: {with_container} in containers, {loose} loose (NULL container)")

    fk_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
    if fk_errors:
        print(f"WARNING: {len(fk_errors)} foreign key violations:")
        for err in fk_errors:
            print(f"  {err}")
    else:
        print("Foreign key references OK.")

    conn.close()


if __name__ == '__main__':
    main()
