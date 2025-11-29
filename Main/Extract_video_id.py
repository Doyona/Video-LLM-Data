#!/usr/bin/env python3
#!/usr/bin/env python3
"""Small utility: extract a `video_id` column from CSVs in the `Video_csv` folder
and write per-file and combined id lists into the `video_id` output folder.

Behavior:
- Detects input folder by looking for any sibling directory named case-insensitively
  'video_csv' (handles small name variations). Falls back to './Video_csv'.
- Detects or creates an output folder named case-insensitively 'video_id' (prefers
  existing `VIdeo_id` in this repository).
- For each CSV (non-recursive), finds a header column that looks like 'video_id' or
  contains both 'video' and 'id' (case-insensitive). Falls back to first column.
- Writes one file per source CSV named `<source>_video_ids.txt` and a combined
  `all_video_ids.txt` with unique ids (one per line).
"""
from pathlib import Path
import csv
import sys
from typing import List, Set


def find_case_insensitive_dir(base: Path, target_lower: str) -> Path:
    """Return the first directory under `base` whose lower() == target_lower, or None."""
    for child in base.iterdir():
        # ignore accidental surrounding whitespace in folder names
        if child.is_dir() and child.name.strip().lower() == target_lower:
            return child
    return None


def extract_ids_from_csv(path: Path) -> List[str]:
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            with path.open('r', encoding=enc, errors='replace', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
            break
        except Exception:
            rows = []
    if not rows:
        return []

    header = rows[0]
    # find column index for video id
    vid_idx = None
    for i, h in enumerate(header):
        if h and 'video' in h.lower() and 'id' in h.lower():
            vid_idx = i
            break
    if vid_idx is None:
        for i, h in enumerate(header):
            if h and h.strip().lower() == 'video_id':
                vid_idx = i
                break
    if vid_idx is None:
        # fallback to first column
        vid_idx = 0

    ids = []
    for r in rows[1:]:
        if len(r) > vid_idx:
            v = r[vid_idx].strip()
            if v and v.lower() != 'video_id':
                ids.append(v)
    return ids


def main():
    base = Path(__file__).resolve().parent

    # Find input folder (case-insensitive)
    input_dir = find_case_insensitive_dir(base, 'video_csv')
    if input_dir is None:
        input_dir = base / 'Video_csv'

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}")
        sys.exit(1)

    # Find or create output folder (prefer existing folder named e.g. 'VIdeo_id')
    out_dir = find_case_insensitive_dir(base, 'video_id')
    if out_dir is None:
        out_dir = base / 'video_id'
        out_dir.mkdir(exist_ok=True)

    csv_files = sorted([p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == '.csv'])
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        sys.exit(0)

    all_ids: Set[str] = set()
    for csvf in csv_files:
        ids = extract_ids_from_csv(csvf)
        if not ids:
            print(f"[INFO] no ids extracted from {csvf.name}")
            continue
        # write per-file ids
        out_file = out_dir / (csvf.stem + '_video_ids.txt')
        with out_file.open('w', encoding='utf-8') as fo:
            for v in ids:
                fo.write(v + '\n')
        print(f"Wrote {len(ids)} ids to {out_file.relative_to(base)}")
        for v in ids:
            all_ids.add(v)

    # combined file
    combined = out_dir / 'all_video_ids.txt'
    with combined.open('w', encoding='utf-8') as fo:
        for v in sorted(all_ids):
            fo.write(v + '\n')
    print(f"Wrote {len(all_ids)} unique ids to {combined.relative_to(base)}")


if __name__ == '__main__':
    main()
