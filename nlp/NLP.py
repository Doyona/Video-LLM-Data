import os
import re
from typing import List

# 需要先安装: pip install langdetect
try:
    from langdetect import detect, DetectorFactory, LangDetectException  # type: ignore
    DetectorFactory.seed = 0  # 结果稳定
    _LANGDETECT_AVAILABLE = True
except Exception:
    _LANGDETECT_AVAILABLE = False

# 常见英文高频词 (截取一部分即可用于粗筛)
COMMON_EN_WORDS = {
    'the','be','to','of','and','a','in','that','have','i','it','for','not','on','with','he','as','you','do','at',
    'this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all','would','there','their',
    'what','so','up','out','if','about','who','get','which','go','me','when','make','can','like','time','no','just','him',
    'know','take','people','into','year','your','good','some','could','them','see','other','than','then','now','look','only',
    'come','its','over','think','also','back','after','use','two','how','our','work','first','well','way','even','new','want',
    'because','any','these','give','day','most','us','is','are','was','were','am','been','did','does','had','has','have','may',
    'might','should','would','could','shall','why','where','when'
}

INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'video_comment')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'video_comment_NLP')
os.makedirs(OUTPUT_DIR, exist_ok=True)

QUESTION_START_WORDS = {
    'who','what','when','where','why','how','which','whom','whose',
    'is','are','was','were','do','does','did','can','could','will','would','should','has','have','had','may','might','shall','won\'t','shouldn\'t','doesn\'t','didn\'t','isn\'t','aren\'t','can\'t','couldn\'t','haven\'t','hasn\'t','hadn\'t'
}

WORD_RE = re.compile(r"\b\w+\b")
TOKEN_RE = re.compile(r"[A-Za-z']+")

# 改进的英文回退检测
def _fallback_english(text: str) -> bool:
    # 排除非ASCII比例过高
    non_ascii = sum(1 for ch in text if ord(ch) > 127)
    if non_ascii > len(text) * 0.05:
        return False
    tokens = TOKEN_RE.findall(text.lower())
    if len(tokens) < 3:
        return False
    # 统计命中常用英文词
    hits = sum(1 for t in tokens if t in COMMON_EN_WORDS)
    hit_ratio = hits / len(tokens)
    if hit_ratio < 0.3:
        return False
    # 元音比例 (英文一般有较高元音比例)
    letters = re.findall(r'[A-Za-z]', text)
    vowels = sum(1 for ch in letters if ch.lower() in 'aeiou')
    if len(letters) == 0:
        return False
    vowel_ratio = vowels / len(letters)
    if vowel_ratio < 0.25:  # 太低可能不是英文
        return False
    return True

def is_english(text: str) -> bool:
    if _LANGDETECT_AVAILABLE:
        try:
            lang = detect(text)
            if lang == 'en':
                return True
            # langdetect 误判时再用回退
            return False
        except LangDetectException:
            return _fallback_english(text)
    return _fallback_english(text)

def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))

def is_question(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    # 1. 直接包含问号
    if t.endswith('?'):
        return True
    # 2. 以疑问词或助动词开头 (缺少问号也算)
    first = t.split(maxsplit=1)[0].lower()
    if first in QUESTION_START_WORDS:
        return True
    # 3. 以 "I wonder" / "Could you" / "Can anyone" 等结构
    lowered = t.lower()
    heuristic_patterns = [
        'i wonder', 'could you', 'can anyone', 'does anyone', 'any idea', 'do you know', 'can someone'
    ]
    for p in heuristic_patterns:
        if lowered.startswith(p):
            return True
    return False

def filter_comment(text: str, min_words: int = 6) -> bool:
    if word_count(text) < min_words:
        return False
    if not is_english(text):
        return False
    if not is_question(text):
        return False
    return True

def process_file(in_path: str, out_path: str) -> int:
    passed: List[str] = []
    try:
        with open(in_path, 'r', encoding='utf-8') as f:
            for line in f:
                c = line.strip()
                if not c:
                    continue
                if filter_comment(c):
                    passed.append(c)
    except Exception as e:
        print(f"Read error {in_path}: {e}")
        return 0

    # 去重 (保持顺序)
    seen = set()
    deduped = []
    for c in passed:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    if deduped:
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                for c in deduped:
                    f.write(c + '\n')
            print(f"Saved {len(deduped)} -> {os.path.basename(out_path)}")
        except Exception as e:
            print(f"Write error {out_path}: {e}")
    else:
        print(f"No qualified comments in {os.path.basename(in_path)}")
    return len(deduped)

def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"Input dir missing: {INPUT_DIR}")
        return
    total_kept = 0
    total_files = 0
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.txt'):
            continue
        in_path = os.path.join(INPUT_DIR, fname)
        out_path = os.path.join(OUTPUT_DIR, fname)
        total_files += 1
        total_kept += process_file(in_path, out_path)
    print(f"Done. Files processed: {total_files}, total kept comments: {total_kept}")

if __name__ == '__main__':
    main()
