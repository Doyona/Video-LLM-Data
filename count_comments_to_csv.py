import os
import csv

VIDEO_COMMENT_DIR = "video_comment"
TRANSFORMER_DIR = "comment_transformer"
OUTPUT_CSV = "comment_counts.csv"

def count_lines(folder):
    counts = {}
    if not os.path.isdir(folder):
        print(f"Missing folder: {folder}")
        return counts
    for fname in os.listdir(folder):
        if not fname.endswith('.txt'):
            continue
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                n = sum(1 for _ in f)
            counts[fname] = n
        except Exception as e:
            print(f"Read error {path}: {e}")
    return counts

def main():
    vc_counts = count_lines(VIDEO_COMMENT_DIR)
    tf_counts = count_lines(TRANSFORMER_DIR)
    all_files = set(vc_counts.keys()) | set(tf_counts.keys())
    total_vc = sum(vc_counts.values())
    total_tf = sum(tf_counts.values())
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['video_id', 'video_comment', 'video_comment_transformer'])
        writer.writeheader()
        for fname in sorted(all_files):
            video_id = os.path.splitext(fname)[0]
            vc = vc_counts.get(fname, 0)
            tf = tf_counts.get(fname, 0)
            writer.writerow({'video_id': video_id, 'video_comment': vc, 'video_comment_transformer': tf})
        # 最后一行输出汇总
        writer.writerow({'video_id': 'TOTAL', 'video_comment': total_vc, 'video_comment_transformer': total_tf})
    print(f"统计完成，已保存到 {OUTPUT_CSV}")

if __name__ == '__main__':
    main()