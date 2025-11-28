import os
import csv
import re
import cld3  # 来自 pycld3，pip install pycld3

INPUT_DIR = "video_comment"
OUT_FOLDER = "video_comment_English"          # 保存仅英文评论文本
SUMMARY_CSV = "video_comment_English.csv"     # 汇总统计

MIN_LEN = 5        # 最少词数量
MIN_PROB = 0.80    # CLD3 置信度阈值，建议 0.80 或 0.85

os.makedirs(OUT_FOLDER, exist_ok=True)

# 去掉 URL、tag、emoji、常见符号等
CLEAN_RE = re.compile(
    r"https?://\S+|[#@]\w+|[\u2600-\u26FF\u2700-\u27BF]|[^\w\s]"
)

COMMON_EN_WORDS = {
    "the", "is", "are", "what", "how", "why",
    "can", "you", "your", "this", "that", "and", "do"
}

def clean_text(t: str) -> str:
    t = t.strip()
    t = CLEAN_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def is_english(line: str) -> bool:
    if not line:
        return False

    cleaned = clean_text(line)
    if not cleaned:
        return False

    words = cleaned.split()
    if len(words) < MIN_LEN:
        return False

    # ✅ 使用 CLD3 进行语言识别
    result = cld3.get_language(cleaned)
    if result is None:
        return False

    lang = result.language          # 例如 'en', 'fr', 'de', 'und'
    prob = result.probability       # 0~1
    reliable = result.is_reliable

    # 主规则：英文 + 可靠 + 概率高于阈值
    if lang == "en" and reliable and prob >= MIN_PROB:
        return True

    # 附加规则：稍低置信度时，结合常见英文词辅助判断
    if lang == "en" and prob >= 0.70:
        hit = sum(1 for w in words if w.lower() in COMMON_EN_WORDS)
        return hit >= 2

    return False

summary_rows = []

for fname in os.listdir(INPUT_DIR):
    if not fname.endswith(".txt"):
        continue
    in_path = os.path.join(INPUT_DIR, fname)
    if not os.path.isfile(in_path):
        continue

    with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip() for l in f if l.strip()]

    total = len(lines)
    english = [l for l in lines if is_english(l)]
    english_count = len(english)
    ratio = english_count / total if total > 0 else 0.0
    video_id = os.path.splitext(fname)[0]

    if english_count > 0:
        out_txt = os.path.join(OUT_FOLDER, fname)
        with open(out_txt, "w", encoding="utf-8") as out_f:
            out_f.write("\n".join(english))

    print(f"{video_id}: total={total} english={english_count} ratio={ratio:.3f}")
    summary_rows.append([video_id, total, english_count, f"{ratio:.6f}"])

with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["video_id", "total_comments", "english_comments", "english_ratio"])
    w.writerows(summary_rows)

print(f"完成: {SUMMARY_CSV}, 英文评论文件目录: {OUT_FOLDER}")
