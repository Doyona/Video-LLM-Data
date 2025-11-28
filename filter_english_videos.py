import csv
import os

SRC = 'video_comment_top80_percent_overlap_enriched.csv'
OUT = 'video_comment_top80_percent_overlap_enriched_english_region.csv'

# 英语国家/地区 ISO 3166-1 Alpha-2 代码集合（可按需扩展）
ENGLISH_COUNTRIES = {
    'US','GB','CA','AU','NZ','IE','SG','PH','ZA','NG','JM','TT','BB','BZ','LR','GH','KE'
}

# 语言字段可能为 'en' 或 'en-US' 等
def is_english_lang(val: str) -> bool:
    if not val:
        return False
    v = val.lower().strip()
    return v == 'en' or v.startswith('en-')

if not os.path.isfile(SRC):
    print(f'Source file not found: {SRC}')
    raise SystemExit(1)

with open(SRC,'r',encoding='utf-8',errors='ignore') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames or []

keep = []
for row in rows:
    lang1 = row.get('default_language','')
    lang2 = row.get('default_audio_language','')
    country = row.get('channel_country','').strip().upper()
    # 条件：语言字段至少一个判定为英语 且 国家在英语国家集合
    if (is_english_lang(lang1) or is_english_lang(lang2)) and country in ENGLISH_COUNTRIES:
        keep.append(row)

print(f'Total rows: {len(rows)} -> kept: {len(keep)}')

with open(OUT,'w',newline='',encoding='utf-8') as out_f:
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(keep)

print(f'Saved filtered file to {OUT}')
