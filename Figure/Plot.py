import os
import csv
import numpy as np
import matplotlib.pyplot as plt

SRC = "../English_video_11.25.csv"
OUT_DIR = "fig_better"
os.makedirs(OUT_DIR, exist_ok=True)

# =========
# 1. 读取数据
# =========

# 所有样本（用于柱状图 / 直方图）
raw_all = []
final_all = []
ratio_all = []

# 仅用于散点图（要求有国家）
raw_scatter = []
final_scatter = []
ratio_scatter = []
cat_scatter = []
views_scatter = []
country_scatter = []

with open(SRC, "r", encoding="utf-8", errors="ignore") as f:
    r = csv.DictReader(f)
    for row in r:
        try:
            vc = int(row["video_comment"])
            vf = int(row["video_comment_final"])
            rt = float(row["ratio"])
            cat = (row.get("category_title", "") or "").strip() or "Unknown"
            vcnt = int(row.get("view_count", "0") or 0)
        except Exception:
            continue

        # 所有数据都进直方图用的列表
        raw_all.append(vc)
        final_all.append(vf)
        ratio_all.append(rt)

        # ===== 下面这段只用于散点图：需要国家信息 =====
        country = (row.get("channel_country", "") or "").strip()
        if country == "" or country == "0" or country.lower() in {"n/a", "na", "null"}:
            continue

        raw_scatter.append(vc)
        final_scatter.append(vf)
        ratio_scatter.append(rt)
        cat_scatter.append(cat)
        views_scatter.append(vcnt)
        country_scatter.append(country)

print(f"Total rows for histograms: {len(raw_all)}")
print(f"Total rows for scatter (with country): {len(raw_scatter)}")

# 转成 numpy
raw_all = np.array(raw_all, dtype=float)
final_all = np.array(final_all, dtype=float)
ratio_all = np.array(ratio_all, dtype=float)

raw_scatter = np.array(raw_scatter, dtype=float)
final_scatter = np.array(final_scatter, dtype=float)
ratio_scatter = np.array(ratio_scatter, dtype=float)
views_scatter = np.array(views_scatter, dtype=float)
cat_scatter = np.array(cat_scatter, dtype=object)

def save_and_close(fig, filename):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, filename), dpi=150)
    plt.close(fig)

# =========
# 2. 柱状图 / 直方图（使用全部样本）
# =========

if len(raw_all) > 0:
    # 原始评论数
    raw_p95 = np.percentile(raw_all, 95)
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    raw_for_plot = raw_all[raw_all <= raw_p95]
    ax1.hist(raw_for_plot, bins=30)
    ax1.set_title("Distribution of Raw Comment Count (≤95th percentile)")
    ax1.set_xlabel("video_comment")
    ax1.set_ylabel("number of videos")
    save_and_close(fig1, "video_comment_raw_hist.png")

if len(final_all) > 0:
    # 筛选后评论数（>0部分）
    final_pos = final_all[final_all > 0]
    if len(final_pos) > 0:
        final_p95 = np.percentile(final_pos, 95)
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        final_for_plot = final_pos[final_pos <= final_p95]
        ax2.hist(final_for_plot, bins=30)
        ax2.set_title("Distribution of Final Comment Count (≤95th percentile)")
        ax2.set_xlabel("video_comment_final")
        ax2.set_ylabel("number of videos")
        save_and_close(fig2, "video_comment_final_hist.png")

if len(ratio_all) > 0:
    # ratio 分布 + 四分位 & 均值
    ratio_q25 = np.percentile(ratio_all, 25)
    ratio_med = np.percentile(ratio_all, 50)
    ratio_q75 = np.percentile(ratio_all, 75)
    ratio_mean = np.mean(ratio_all)
    fig3, ax3 = plt.subplots(figsize=(7, 4))
    # 仅取 0 - 0.2 范围
    ratio_for_plot = ratio_all[(ratio_all >= 0) & (ratio_all <= 0.2)]
    ax3.hist(ratio_for_plot, bins=40, range=(0, 0.2))
    # 竖线标记
    ax3.axvline(ratio_q25, color='orange', linestyle='--', label=f"25%={ratio_q25:.3f}")
    ax3.axvline(ratio_med, color='red', linestyle='--', label=f"median={ratio_med:.3f}")
    ax3.axvline(ratio_q75, color='green', linestyle='--', label=f"75%={ratio_q75:.3f}")
    ax3.axvline(ratio_mean, color='blue', linestyle='--', label=f"mean={ratio_mean:.3f}")
    ax3.set_xlim(0, 0.2)
    ax3.set_ylim(0, 20)
    ax3.set_title("Distribution of Ratio (Final/Raw)\nwith 25%, Median, 75%, Mean")
    ax3.set_xlabel("ratio")
    ax3.set_ylabel("number of videos")
    ax3.legend(loc='upper right', fontsize=8)
    save_and_close(fig3, "ratio_hist.png")
# =========
# 4. 散点图（按 category_title 上色，不过滤国家）
# =========

if len(raw_all) == 0:
    print("No data for scatter plot.")
else:
    # 用全部数据（不用 raw_scatter / final_scatter）
    raw_s = raw_all
    final_s = final_all
    cats_s = np.array(cat_scatter if len(cat_scatter) == len(raw_all) else cat_scatter, dtype=object)
    views_s = np.array(views_scatter if len(views_scatter) == len(raw_all) else views_scatter, dtype=float)

    # 若 cat_scatter / views_scatter 长度是散点子集，需要直接用 full 列
    with open(SRC, "r", encoding="utf-8", errors="ignore") as f:
        r = csv.DictReader(f)
        cats_s = []
        views_s = []
        for row in r:
            try:
                cats_s.append((row.get("category_title", "") or "Unknown").strip())
                views_s.append(int(row.get("view_count", "0") or 0))
            except:
                cats_s.append("Unknown")
                views_s.append(0)

    cats_s = np.array(cats_s, dtype=object)
    views_s = np.array(views_s, dtype=float)

    # 截到 P95，让图更好看
    raw_p95 = np.percentile(raw_s, 95)
    final_pos = final_s[final_s > 0]
    final_p95 = np.percentile(final_pos, 95) if len(final_pos) > 0 else np.max(final_s)

    mask = (raw_s <= raw_p95) & (final_s <= final_p95)

    x = raw_s[mask]
    y = final_s[mask]
    cats = cats_s[mask]
    views = views_s[mask]

    fig, ax = plt.subplots(figsize=(8, 6))

    # 点大小映射（按 view_count）
    views_pos = np.maximum(views, 1)
    v_sqrt = np.sqrt(views_pos)
    v95 = np.percentile(v_sqrt, 95)
    v_norm = np.clip(v_sqrt / v95, 0, 1)
    sizes = 30 + (160 - 30) * v_norm

    # 颜色映射：按 category_title
    unique_cats = sorted(list(set(cats)))
    cmap = plt.cm.get_cmap("tab20", len(unique_cats))

    for i, cat in enumerate(unique_cats):
        m = (cats == cat)
        ax.scatter(
            x[m], y[m],
            s=sizes[m],
            color=cmap(i),
            alpha=0.75,
            edgecolors="none",
            label=cat
        )

    # 修改散点图坐标范围
    ax.set_xlim(0, 15000)
    ax.set_ylim(0, 800)
    ax.set_xlabel("Raw comment count")
    ax.set_ylabel("Final (English-cleaned) comment count")
    ax.set_title("Raw vs Final Comments (Clipped)\nColored by Category Title")

    # 图例放右侧
    ax.legend(
        title="Category",
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        borderaxespad=0.
    )

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "scatter_by_category_no_country_filter.png"), dpi=150)
    plt.close(fig)

    print("Saved scatter_by_category_no_country_filter.png")
print(f"Saved plots to {OUT_DIR}")
