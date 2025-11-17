import os
import csv

INPUT_DIR = "comment_transformer"  # 源目录
OUTPUT_CSV = "comments_export.csv"  # 输出文件名

def collect_rows():
    rows = []
    if not os.path.isdir(INPUT_DIR):
        print(f"Directory missing: {INPUT_DIR}")
        return rows
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.txt'):
            continue
        path = os.path.join(INPUT_DIR, fname)
        if not os.path.isfile(path):
            continue
        # video_id = 去掉扩展名
        video_id = os.path.splitext(fname)[0]
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    comment = line.strip()
                    if not comment:
                        continue
                    rows.append({'video_id': video_id, 'comment': comment})
        except Exception as e:
            print(f"Read error {path}: {e}")
    return rows

def write_csv(rows):
    if not rows:
        print("No comments to export.")
        return
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['video_id', 'comment'])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows -> {OUTPUT_CSV}")

def main():
    rows = collect_rows()
    write_csv(rows)

if __name__ == '__main__':
    main()
