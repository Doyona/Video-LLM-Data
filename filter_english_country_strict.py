import csv
import os

INPUT = 'video_comment_top80_percent_overlap_enriched_english_region.csv'
OUTPUT = 'video_comment_top80_percent_overlap_enriched_english_country_strict.csv'

ENGLISH_COUNTRIES = {
    'US','GB','CA','AU','NZ','IE','SG','PH','ZA','NG','JM','TT','BB','BZ','LR','GH','KE'
}

def is_english_lang(val: str) -> bool:
    if not val:
        return False
    v = val.lower().strip()
    return v == 'en' or v.startswith('en-')

if not os.path.exists(INPUT):
    raise FileNotFoundError(INPUT)

with open(INPUT, 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames or []

kept = []
for r in rows:
    country = (r.get('channel_country') or '').strip().upper()
    lang1 = r.get('default_language','')
    lang2 = r.get('default_audio_language','')
    # 必须：国家是英语国家，两个语言字段都判定为英语
    if country in ENGLISH_COUNTRIES and is_english_lang(lang1) and is_english_lang(lang2):
        kept.append(r)

with open(OUTPUT, 'w', newline='', encoding='utf-8') as out:
    w = csv.DictWriter(out, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(kept)

print(f'Filtered {len(rows)} -> {len(kept)} rows written to {OUTPUT}')
