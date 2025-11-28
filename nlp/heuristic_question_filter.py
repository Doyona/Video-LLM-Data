import os
import re
import langdetect

INPUT_DIR = "video_comment_transformer"
OUTPUT_DIR = "video_comment_final"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 问句开头疑问词
QUESTION_START = {
    "who","what","when","where","why","how","which","whom","whose",
    "is","are","was","were","do","does","did","can","could","will","would",
    "should","has","have","had","may","might","shall","won't","isn't","aren't",
    "don't","doesn't","didn't","can't","couldn't","haven't","hasn't","hadn't"
}

# 典型问句短语
QUESTION_PATTERNS = [
    "i wonder", "could you", "could u", "can you", "can u", "can anyone",
    "does anyone", "any idea", "do you know", "can someone", "would you",
    "should i", "is it", "is there", "was it", "were they", "do we", "why is",
    "why are", "what if"
]

WORD_RE = re.compile(r"\b\w+\b")

def is_english(s: str) -> bool:
    try:
        return langdetect.detect(s) == "en"
    except:
        return False

def is_question(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    lt = t.lower()
    # 1. 有问号
    if t.endswith("?") or "?" in t:
        return True
    # 2. 以疑问词/助动词开头
    first = lt.split(maxsplit=1)[0]
    if first in QUESTION_START:
        return True
    # 3. 典型模式开头
    for p in QUESTION_PATTERNS:
        if lt.startswith(p):
            return True
    # 4. 简单倒装 (以助动词 + 代词/名词)
    if first in {"is","are","was","were","do","does","did","can","could","will","would","should","has","have","had","may","might","shall"}:
        return True
    return False

def enough_words(text: str, min_words: int = 3) -> bool:
    return len(WORD_RE.findall(text)) >= min_words

def process_file(in_path: str, out_path: str):
    if os.path.exists(out_path):
        print(f"{os.path.basename(in_path)} 已存在，跳过")
        return
    kept = []
    with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if not is_english(line):
                continue
            if not enough_words(line):
                continue
            if is_question(line):
                kept.append(line)
    if not kept:
        print(f"{os.path.basename(in_path)} 无问句，未创建文件")
        return
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(kept))
    print(f"{os.path.basename(in_path)} 保存 {len(kept)} 条问句 → {out_path}")

def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"输入目录不存在: {INPUT_DIR}")
        return
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    print(f"发现 {len(files)} 个文件待处理...")
    for fname in files:
        in_path = os.path.join(INPUT_DIR, fname)
        if not os.path.isfile(in_path):
            continue
        out_path = os.path.join(OUTPUT_DIR, fname)
        process_file(in_path, out_path)
    print("二次启发式筛选完成。")

if __name__ == "__main__":
    main()