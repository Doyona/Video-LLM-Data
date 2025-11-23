import os
import time
import requests
import langdetect

HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", "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")
API_URL = "https://api-inference.huggingface.co/models/Alireza1044/question-classification"  # 改为标准端点
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}", "Accept": "application/json"}

INPUT_DIR = "video_comment/"
OUTPUT_DIR = "video_comment_transformer_strict/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MIN_WORDS = 6
BATCH_SIZE = 8
API_THRESHOLD = float(os.getenv("QUESTION_THRESHOLD", "0.50"))
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0

# 零样本回退 (可选)
try:
    from transformers import pipeline  # type: ignore
    _zs_pipe = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    _HAS_FALLBACK = True
except Exception:
    _zs_pipe = None
    _HAS_FALLBACK = False

# ---- API 调用 ----

def _request_api(payload):
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        except Exception as e:
            print(f"[NETWORK ERROR] attempt {attempt+1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
            continue
        if resp.status_code == 200:
            return resp
        if resp.status_code in {429, 503} and attempt < MAX_RETRIES - 1:
            print(f"[RATE/LIMIT] {resp.status_code}, retrying...")
            time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
            continue
        print(f"[API ERROR] {resp.status_code} {resp.text[:200]}")
        return None
    return None

# 单条

def model_question(text: str, threshold: float = API_THRESHOLD) -> bool:
    resp = _request_api({"inputs": text})
    if resp is None:
        return fallback_question(text)  # API失败回退
    try:
        data = resp.json()
    except Exception as e:
        print("[PARSE ERROR]", e)
        return fallback_question(text)
    label, score = _extract_label_score(data)
    if label is None:
        return fallback_question(text)
    return label == 'question' and score >= threshold

# 批量

def model_question_batch(texts, threshold: float = API_THRESHOLD):
    resp = _request_api({"inputs": texts})
    results = []
    if resp is None:
        # 全部用回退
        for t in texts:
            results.append(fallback_question(t))
        return results
    try:
        data = resp.json()
    except Exception as e:
        print("[PARSE ERROR batch]", e)
        for t in texts:
            results.append(fallback_question(t))
        return results
    # data 可能是 list(每条一个预测)
    if isinstance(data, list) and all(isinstance(x, (list, dict)) for x in data):
        for item, original in zip(data, texts):
            label, score = _extract_label_score(item)
            if label is None:
                results.append(fallback_question(original))
            else:
                results.append(label == 'question' and score >= threshold)
    else:
        # 不符合预期，逐条回退
        for t in texts:
            results.append(fallback_question(t))
    return results

# 提取标签与分数

def _extract_label_score(obj):
    label = None
    score = 0.0
    try:
        if isinstance(obj, list):
            if obj and isinstance(obj[0], dict):
                label = obj[0].get('label')
                score = float(obj[0].get('score', 0.0))
        elif isinstance(obj, dict):
            if 'label' in obj and 'score' in obj:
                label = obj.get('label')
                score = float(obj.get('score', 0.0))
            elif 'labels' in obj and 'scores' in obj:
                if obj['labels'] and obj['scores']:
                    label = obj['labels'][0]
                    score = float(obj['scores'][0])
    except Exception:
        return None, 0.0
    return label, score

# 回退逻辑 (零样本 + 简单启发式)

def fallback_question(text: str) -> bool:
    if _HAS_FALLBACK:
        try:
            res = _zs_pipe(text, candidate_labels=["question", "statement"], multi_label=False)
            return res['labels'][0].lower() == 'question'
        except Exception as e:
            print("[FALLBACK PIPE ERROR]", e)
    # 简单启发式退路
    t = text.strip().lower()
    if not t:
        return False
    if t.endswith('?') or '?' in t:
        return True
    first = t.split(maxsplit=1)[0]
    return first in {"who","what","when","where","why","how","which"}

# 语言判断

def is_english(text: str) -> bool:
    try:
        return langdetect.detect(text) == 'en'
    except:
        return False

# 保留条件

def keep(text: str) -> bool:
    if not is_english(text):
        return False
    if len([w for w in text.split() if w.isalpha()]) < MIN_WORDS:
        return False
    return model_question(text)

# 文件处理（批量推理）

def process_file(in_path, out_path):
    if os.path.exists(out_path):
        print(f"{os.path.basename(in_path)} 已存在，跳过")
        return
    candidates = []
    with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if not is_english(text):
                continue
            if len([w for w in text.split() if w.isalpha()]) < MIN_WORDS:
                continue
            candidates.append(text)
    if not candidates:
        print(f"{os.path.basename(in_path)} 无候选评论，未创建文件")
        return
    kept = []
    # 分批调用 API
    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i:i+BATCH_SIZE]
        flags = model_question_batch(batch)
        for text, ok in zip(batch, flags):
            if ok:
                kept.append(text)
    if not kept:
        print(f"{os.path.basename(in_path)} 无问句，未创建文件")
        return
    with open(out_path, 'w', encoding='utf-8') as out:
        for k in kept:
            out.write(k + '\n')
    print(f"{os.path.basename(in_path)} 保存 {len(kept)}/{len(candidates)} 条问句 → {out_path}")

# 主入口

def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"输入目录不存在: {INPUT_DIR}")
        return
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.txt')]
    if not files:
        print("无待处理文件")
        return
    print(f"使用阈值: {API_THRESHOLD}, 批大小: {BATCH_SIZE}, 回退可用: {_HAS_FALLBACK}")
    for fname in files:
        in_path = os.path.join(INPUT_DIR, fname)
        if not os.path.isfile(in_path):
            continue
        out_path = os.path.join(OUTPUT_DIR, fname)
        process_file(in_path, out_path)
    print("处理完成")

if __name__ == '__main__':
    main()
