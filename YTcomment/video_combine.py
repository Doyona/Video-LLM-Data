import os
import csv

DIR_RAW = "YTcomment/video_comment"
DIR_FINAL = "YTcomment/video_comment_final"
OUT_CSV = "YTcomment/YT_merge.csv"

def count_lines(folder):
    counts = {}
    if not os.path.isdir(folder):
        print(f"Missing folder: {folder}")
        return counts
    for fname in os.listdir(folder):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                n = sum(1 for _ in f)
            counts[fname] = n
        except Exception as e:
            print(f"Read error {path}: {e}")
    return counts

def main():
    raw_counts = count_lines(DIR_RAW)
    final_counts = count_lines(DIR_FINAL)

    all_files = sorted(set(raw_counts.keys()) | set(final_counts.keys()))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "video_comment", "video_comment_final"])
        for fname in all_files:
            vid = os.path.splitext(fname)[0]
            raw_n = raw_counts.get(fname, 0)
            final_n = final_counts.get(fname, 0)
            w.writerow([vid, raw_n, final_n])

    print(f"Saved: {OUT_CSV}")

if __name__ == "__main__":
    main()