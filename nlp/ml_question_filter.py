import os
import re
from typing import List

# External ML libs: transformers (zero-shot classification) + langdetect
# Install (PowerShell): pip install transformers torch langdetect

try:
    from langdetect import detect, LangDetectException  # type: ignore
    _LANG_OK = True
except Exception:
    _LANG_OK = False

try:
    from transformers import pipeline  # type: ignore
except ImportError:
    raise SystemExit('Missing transformers. Run: pip install transformers torch langdetect')

# Initialize zero-shot pipeline once
_ZS = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'video_comment')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'video_comment_NLP_ML')
os.makedirs(OUTPUT_DIR, exist_ok=True)

WORD_RE = re.compile(r"\b\w+\b")

CANDIDATE_LABELS = ["question", "statement"]

def is_english(text: str) -> bool:
    if not _LANG_OK:
        # fallback: majority ASCII letters heuristic
        letters = sum(ch.isalpha() for ch in text)
        return letters / max(len(text), 1) > 0.6
    try:
        return detect(text) == 'en'
    except LangDetectException:
        return False

def word_count(t: str) -> int:
    return len(WORD_RE.findall(t))

def is_question_ml(text: str, threshold: float = 0.6) -> bool:
    # Use MNLI zero-shot classification
    res = _ZS(text, CANDIDATE_LABELS, multi_label=False)
    # res['labels'] is ordered by score desc
    top_label = res['labels'][0]
    top_score = res['scores'][0]
    return top_label == 'question' and top_score >= threshold

def filter_comment(text: str, min_words: int = 6) -> bool:
    if word_count(text) < min_words:
        return False
    if not is_english(text):
        return False
    if not is_question_ml(text):
        return False
    return True

def process_file(in_path: str, out_path: str) -> int:
    kept: List[str] = []
    try:
        with open(in_path, 'r', encoding='utf-8') as f:
            for line in f:
                c = line.strip()
                if not c:
                    continue
                if filter_comment(c):
                    kept.append(c)
    except Exception as e:
        print(f'Read error {in_path}: {e}')
        return 0

    # Deduplicate preserving order
    seen = set()
    deduped = []
    for c in kept:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    if deduped:
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                for c in deduped:
                    f.write(c + '\n')
            print(f'Saved {len(deduped)} -> {os.path.basename(out_path)}')
        except Exception as e:
            print(f'Write error {out_path}: {e}')
    else:
        print(f'No qualified comments in {os.path.basename(in_path)}')
    return len(deduped)

def main():
    if not os.path.isdir(INPUT_DIR):
        print(f'Input dir missing: {INPUT_DIR}')
        return
    total_files = 0
    total_kept = 0
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.txt'):
            continue
        in_path = os.path.join(INPUT_DIR, fname)
        out_path = os.path.join(OUTPUT_DIR, fname)
        total_files += 1
        total_kept += process_file(in_path, out_path)
    print(f'Done. Files processed: {total_files}, total kept comments: {total_kept}')

if __name__ == '__main__':
    main()
