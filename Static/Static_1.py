import csv
import os

SRC = "./video_comment_merged_counts.csv"
OUT_RATIO = "./video_comment_ratio_ge_0.8.csv"
OUT_TOP80P = "./video_comment_top80_percent_overlap.csv"

RATIO_THRESHOLD = 0.8
PERCENT_THRESHOLD = 0.80  # 前80%

def load_rows(path):
    rows = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.DictReader(f)
        for d in r:
            try:
                vc = int(d["video_comment"])
                vf = int(d["video_comment_final"])
            except:
                continue
            rows.append({
                "video_id": d["video_id"],
                "video_comment": vc,
                "video_comment_final": vf
            })
    return rows

def rank_map(rows, key):
    sorted_rows = sorted(rows, key=lambda x: x[key], reverse=True)
    return {row["video_id"]: idx+1 for idx, row in enumerate(sorted_rows)}

def export_ratio(rows):
    out = []
    for r in rows:
        vc = r["video_comment"]
        vf = r["video_comment_final"]
        if vc <= 0:
            continue
        ratio = vf / vc
        if ratio >= RATIO_THRESHOLD:
            out.append((r["video_id"], vc, vf, ratio))
    out.sort(key=lambda x: x[3], reverse=True)
    with open(OUT_RATIO, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["video_id","video_comment","video_comment_final","ratio"])
        for row in out:
            w.writerow([row[0], row[1], row[2], f"{row[3]:.6f}"])
    print(f"比例筛选完成: {OUT_RATIO} 共 {len(out)} 行")

def export_top80_percent(rows):
    rk_vc = rank_map(rows, "video_comment")
    rk_vf = rank_map(rows, "video_comment_final")
    total = len(rows)
    cutoff = int(total * PERCENT_THRESHOLD)
    out = []
    for r in rows:
        rv = rk_vc[r["video_id"]]
        rf = rk_vf[r["video_id"]]
        if rv <= cutoff and rf <= cutoff:
            vc = r["video_comment"]
            vf = r["video_comment_final"]
            ratio = vf / vc if vc > 0 else 0.0
            out.append((r["video_id"], vc, vf, ratio, rv, rf))
    out.sort(key=lambda x: x[3], reverse=True)
    with open(OUT_TOP80P, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["video_id","video_comment","video_comment_final","ratio","rank_vc","rank_vf","cutoff_rank"])
        for row in out:
            w.writerow([row[0], row[1], row[2], f"{row[3]:.6f}", row[4], row[5], cutoff])
    print(f"前80%重叠筛选完成: {OUT_TOP80P} 共 {len(out)} 行")

def main():
    if not os.path.isfile(SRC):
        print(f"源文件不存在: {SRC}")
        return
    rows = load_rows(SRC)
    if not rows:
        print("无数据")
        return
    export_ratio(rows)
    export_top80_percent(rows)

if __name__ == "__main__":
    main()